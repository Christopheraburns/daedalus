"""A small MCP client for consuming other MCP servers: tool discovery and tool calls.

It speaks the latest profile (2026-07-28: no handshake, per-request metadata) first and
falls back to the earlier Streamable HTTP profile (initialize, session id, then requests)
when the server rejects it, so Daedalus can consume servers built on older SDKs. Used by
the Builder for discovery and by the executor for `kind: mcp` tools.
"""
import json
import itertools

import httpx

MODERN = "2026-07-28"
LEGACY_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")
MAX_RESPONSE = 1024 * 1024
CLIENT_INFO = {"name": "daedalus", "version": "0.1.0"}
_ids = itertools.count(1)


class MCPError(ValueError):
    pass


def http_problem(response):
    """A readable reason for an HTTP error that carries no JSON-RPC reply (rate limits, proxies, timeouts)."""
    detail = ""
    try:
        body = response.json()
        if isinstance(body, dict):
            detail = " ".join(str(body[k]) for k in ("title", "detail", "message", "error") if isinstance(body.get(k), str))
    except ValueError:
        detail = response.text.strip().splitlines()[0] if response.text.strip() else ""
    retry = response.headers.get("retry-after")
    advice = f"; retry after {retry} seconds" if retry and retry.isdigit() else ""
    label = {429: "rate limited", 502: "bad gateway", 503: "unavailable", 504: "timed out"}.get(response.status_code, "error")
    return f"Upstream MCP server answered HTTP {response.status_code} ({label}){': ' + detail[:240] if detail else ''}{advice}"


def _message(response, request_id):
    """The JSON-RPC reply to request_id, from a JSON or event-stream response."""
    if len(response.content) > MAX_RESPONSE:
        raise MCPError("Upstream MCP response exceeded 1 MiB")
    if response.status_code > 400:
        # 400 can carry a JSON-RPC "unsupported version" reply (used for profile fallback); higher codes from
        # proxies and rate limiters usually do not.
        try:
            body = response.json()
        except ValueError:
            body = None
        if not (isinstance(body, dict) and body.get("jsonrpc")):
            raise MCPError(http_problem(response))
    if "text/event-stream" in response.headers.get("content-type", ""):
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    message = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if message.get("id") == request_id:
                    return message
        raise MCPError("Upstream MCP server sent no reply on its event stream")
    try:
        return response.json()
    except ValueError as exc:
        raise MCPError(f"Upstream MCP server answered HTTP {response.status_code} without JSON-RPC") from exc


class Client:
    def __init__(self, url, headers=None, timeout=8.0):
        self.url = url
        self.http = httpx.Client(headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", **(headers or {})}, timeout=timeout, trust_env=False, follow_redirects=False)
        self.profile = None  # "modern" or the negotiated legacy version
        self.session = None

    def close(self):
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _post(self, method, params, headers):
        request_id = next(_ids)
        response = self.http.post(self.url, headers=headers, json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        if response.status_code in (401, 403):
            raise MCPError(f"Upstream MCP server rejected the credentials (HTTP {response.status_code})")
        return response, _message(response, request_id)

    def _modern(self, method, params):
        params = {**params, "_meta": {"io.modelcontextprotocol/protocolVersion": MODERN, "io.modelcontextprotocol/clientInfo": CLIENT_INFO, "io.modelcontextprotocol/clientCapabilities": {}}}
        headers = {"MCP-Protocol-Version": MODERN, "Mcp-Method": method, **({"Mcp-Name": params["name"]} if "name" in params else {})}
        return self._post(method, params, headers)

    def _initialize(self):
        response, message = self._post("initialize", {"protocolVersion": LEGACY_VERSIONS[0], "capabilities": {}, "clientInfo": CLIENT_INFO}, {})
        if "error" in message:
            raise MCPError(f"Upstream MCP server refused to initialize: {message['error'].get('message', '')[:300]}")
        version = message.get("result", {}).get("protocolVersion")
        if version not in LEGACY_VERSIONS:
            raise MCPError(f"Upstream MCP server offered unsupported protocol version {version}")
        self.profile, self.session = version, response.headers.get("mcp-session-id")
        headers = {"MCP-Protocol-Version": version, **({"Mcp-Session-Id": self.session} if self.session else {})}
        self.http.post(self.url, headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"})

    def request(self, method, params=None):
        params = dict(params or {})
        if self.profile in (None, "modern"):
            response, message = self._modern(method, params)
            error = message.get("error") or {}
            unsupported = response.status_code == 400 or error.get("code") in (-32600, -32601, -32602) and self.profile is None
            if not unsupported or self.profile == "modern":
                self.profile = "modern"
                return self._result(message)
            self._initialize()
        headers = {"MCP-Protocol-Version": self.profile, **({"Mcp-Session-Id": self.session} if self.session else {})}
        _, message = self._post(method, params, headers)
        return self._result(message)

    @staticmethod
    def _result(message):
        if "error" in message:
            raise MCPError(f"Upstream MCP error {message['error'].get('code')}: {message['error'].get('message', '')[:300]}")
        result = message.get("result")
        if not isinstance(result, dict):
            raise MCPError("Upstream MCP server returned no result")
        return result

    def list_tools(self):
        tools, cursor = [], None
        for _ in range(20):
            result = self.request("tools/list", {"cursor": cursor} if cursor else {})
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return tools
        raise MCPError("Upstream MCP server returned more than 20 pages of tools")

    def call_tool(self, name, arguments):
        return self.request("tools/call", {"name": name, "arguments": arguments})


def supports_discover(url, headers=None):
    """Whether the server answers server/discover on the latest profile. agentgateway needs it to federate
    a server; individual MCP tools do not."""
    with Client(url, headers, timeout=15.0) as client:
        _, message = client._modern("server/discover", {})
    return "result" in message


def discover(url, headers=None):
    """[{name, description, input_schema, read_only}] for every tool the server lists."""
    with Client(url, headers, timeout=15.0) as client:
        tools = client.list_tools()
        profile = client.profile
    found = []
    for tool in tools:
        if not isinstance(tool, dict) or not tool.get("name"):
            continue
        schema = tool.get("inputSchema") or {"type": "object", "properties": {}}
        # Gateways that publish OpenAPI operations (agentgateway, so any Daedalus server) nest JSON
        # inputs under "body"; expose the inner fields and re-wrap on the way out.
        properties = schema.get("properties") or {}
        wrapped = set(properties) == {"body"} and (properties["body"] or {}).get("type") == "object"
        found.append({"name": tool["name"], "description": tool.get("description", "") or "", "input_schema": properties["body"] if wrapped else schema,
            "wrap_body": wrapped, "read_only": bool((tool.get("annotations") or {}).get("readOnlyHint"))})
    return found, profile
