import os

import pytest

from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import candidate, rpc

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"
LEGACY_UPSTREAM = f"{MOCK}/upstream/mcp"  # Python SDK server on the 2025-11-25 profile with sessions


def connection(client, **spec):
    response = client.post("/api/connections", json={"name": spec.pop("name", "Upstream"), "base_url": LEGACY_UPSTREAM, "protocol": "mcp", **spec})
    assert response.status_code == 201, response.text
    return response.json()


def check(client, item):
    response = client.post(f"/api/connections/{item['id']}/check", headers={"If-Match": str(item["revision"])})
    assert response.status_code == 200, response.text
    return response.json()


def run(client, tool, arguments, confirm=False):
    response = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": str(tool["revision"])}, json={"arguments": arguments, "confirm_write": confirm})
    assert response.status_code == 200, response.text
    return response.json()


@gateway
def test_individual_tools_from_an_older_mcp_server(registry):
    client, _, _ = registry
    upstream = connection(client)
    assert client.post("/api/tools", json={"name": "too_soon", "description": "x", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "add"}).status_code == 422  # not discovered yet
    checked = check(client, upstream)
    assert checked["probe_summary"]["success"] and "3 tools discovered (protocol 2025-11-25)" == checked["probe_summary"]["message"]
    assert {t["name"]: t["read_only"] for t in checked["discovered"]} == {"add": True, "lookup_ticket": True, "file_ticket": False}
    assert client.post("/api/tools", json={"name": "nope", "description": "x", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "missing"}).status_code == 422
    rest = client.post("/api/connections", json={"name": "REST", "base_url": MOCK}).json()
    assert client.post("/api/tools", json={"name": "wrong", "description": "x", "kind": "mcp", "connection_id": rest["id"], "upstream_tool": "add"}).status_code == 422
    # The input schema comes from discovery, never from the client.
    created = client.post("/api/tools", json={"name": "sum_numbers", "description": "Add two integers for the agent.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "add", "input_schema": {"type": "object", "properties": {"evil": {"type": "string"}}}})
    assert created.status_code == 201, created.text
    tool = created.json()
    assert set(tool["input_schema"]["properties"]) == {"a", "b"} and tool["input_schema"]["required"] == ["a", "b"]
    outcome = run(client, tool, {"body": {"a": 2, "b": 3}})
    assert outcome["success"] and outcome["result"]["structuredContent"] == {"result": 5}
    assert outcome["input_schema"]["properties"]["body"]["required"] == ["a", "b"]
    assert client.get("/api/workspace").json()["tools"][0]["tested"]
    # Upstream tool errors and invalid arguments come back as errors the agent can read.
    lookup = client.post("/api/tools", json={"name": "ticket", "description": "Find a ticket.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "lookup_ticket"}).json()
    assert "Ticket not found" in run(client, lookup, {"body": {"ticket_id": "missing"}})["result"]["structuredContent"]["error"]
    # Arguments are checked against the upstream schema before anything is sent.
    for bad in ({}, {"body": {"ticket_id": 7}}):
        rejected = run(client, lookup, bad)
        assert not rejected["success"] and "error" in rejected
    file = client.post("/api/tools", json={"name": "file", "description": "File a ticket.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "file_ticket", "effect": "write"}).json()
    assert client.post(f"/api/tools/{file['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"title": "x"}}}).status_code == 422  # write needs confirmation
    assert run(client, file, {"body": {"title": "Broken laptop"}}, confirm=True)["result"]["structuredContent"]["priority"] == "normal"
    preview = client.get("/api/releases/preview").json()
    assert "sum_numbers" in preview["added"]


@gateway
def test_mcp_tools_from_a_daedalus_server_with_credentials_and_renaming(registry, monkeypatch):
    client, _, settings = registry
    upstream_tools = [{"id": n, "revision": 1, "spec": ToolSpec(name=n, description=f"{n} upstream", kind="python", pack="demo", function=n).model_dump()} for n in ("echo", "whoami")]
    with candidate(compile_bundle(upstream_tools, {}, []), settings) as (upstream_url, upstream_token, _):
        origin = upstream_url.rsplit("/", 1)[0]
        for approved in (MOCK, origin):
            assert client.post("/api/policies/origins", json={"origin": approved, "description": "fixture"}).status_code == 201
        monkeypatch.setenv("FACTORY_SECRET_UPSTREAM", upstream_token)
        unauthenticated = check(client, connection(client, name="No token", base_url=upstream_url))
        assert not unauthenticated["probe_summary"]["success"] and "401" in unauthenticated["probe_summary"]["message"]
        upstream = check(client, connection(client, name="Helios", base_url=upstream_url, auth_mode="static", secret_ref="FACTORY_SECRET_UPSTREAM"))
        assert upstream["probe_summary"]["message"] == "2 tools discovered (protocol 2026-07-28)"
        tool = client.post("/api/tools", json={"name": "helios_echo", "description": "Echo through Helios.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "echo"}).json()
        outcome = run(client, tool, {"body": {"text": "hello"}})
        assert outcome["success"], outcome
        assert outcome["result"]["structuredContent"] == {"text": "hello"}
        # Served by this server's own gateway under the local name.
        bundle = compile_bundle([{"id": tool["id"], "revision": 1, "spec": {k: v for k, v in tool.items() if k not in {"id", "revision", "validated", "tested", "published", "test_summary"}}}],
            {upstream["id"]: {k: v for k, v in upstream.items() if k not in {"id", "revision", "probe_summary", "discovered"}}}, [MOCK, origin])
        with candidate(bundle, settings) as (url, token, tools):
            assert [t["name"] for t in tools] == ["helios_echo"]
            assert rpc(url, token, "tools/call", {"name": "helios_echo", "arguments": {"body": {"text": "twice removed"}}})["structuredContent"] == {"text": "twice removed"}


def test_http_errors_from_an_mcp_endpoint_are_reported_plainly():
    from factory import mcp_client
    from factory.gateway import GatewayError, rpc
    with pytest.raises(mcp_client.MCPError, match=r"HTTP 429 \(rate limited\): Error 1015.*retry after 30 seconds"):
        mcp_client.discover(f"{MOCK}/ratelimited/mcp")
    with pytest.raises(GatewayError, match="HTTP 429 instead of an MCP result"):
        rpc(f"{MOCK}/ratelimited/mcp", "token", "tools/list")


@gateway
def test_tool_tests_exclude_federation_and_unfederatable_servers_are_flagged(registry):
    import time
    from factory.gateway import GatewayError
    client, _, settings = registry
    upstream = connection(client, name="Older SDK server", federate=True)
    checked = check(client, upstream)
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["federation_ok"] is False
    assert "cannot be federated" in checked["probe_summary"]["message"]
    assert any("does not implement server/discover" in p for p in client.get("/api/releases/preview").json()["problems"])
    # Its tools still work individually, and a tool test never brings in the federated server.
    tool = client.post("/api/tools", json={"name": "sum", "description": "Add.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "add"}).json()
    outcome = run(client, tool, {"body": {"a": 1, "b": 2}})
    assert outcome["success"], outcome
    assert next(e for e in outcome["log"] if e["code"] == "config_validated")["values"]["targets"] == "1"
    # Federating it anyway fails fast instead of polling the upstream for 15 seconds.
    spec = {k: v for k, v in upstream.items() if k not in {"id", "revision", "probe_summary", "discovered"}}
    bundle = compile_bundle([], {upstream["id"]: {**spec, "_discovered": ["add"]}}, [MOCK])
    started = time.monotonic()
    with pytest.raises(GatewayError):
        with candidate(bundle, settings):
            pass
    assert time.monotonic() - started < 8


def test_repeated_gateway_log_lines_are_collapsed(tmp_path):
    from factory.gateway import gateway_log_tail
    log = tmp_path / "gateway.log"
    line = "2026-10-15T15:07:{s}Z\tinfo\trequest gateway=default/default listener=factory route=internal/default src.addr=127.0.0.1:{p} http.method=POST mcp.method.name=server/discover mcp.error.code=-32601 duration={d}ms"
    log.write_text("\n".join([line.format(s=10 + i, p=50000 + i, d=90 + i) for i in range(5)] + ["2026-10-15T15:08:00Z\terror\trequest http.status=429 error=\"429 Too Many Requests\""]))
    tail = gateway_log_tail(log)
    assert len(tail) == 2 and tail[0].endswith("(x5)") and "src.addr" not in tail[0] and "server/discover" in tail[0] and "429" in tail[1]


@gateway
def test_a_server_with_mcp_tools_reviews_and_publishes_cleanly(registry):
    """Regression: compiling a release must not trip over the connection's discovered-tools annotation."""
    client, _, _ = registry
    upstream = check(client, connection(client))
    tool = client.post("/api/tools", json={"name": "sum", "description": "Add.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "add"}).json()
    assert any("test the current definition" in p for p in client.get("/api/releases/preview").json()["problems"])
    assert run(client, tool, {"body": {"a": 1, "b": 1}})["success"]
    preview = client.get("/api/releases/preview").json()
    assert preview["problems"] == [] and preview["added"] == ["sum"]
    published = client.post("/api/releases", json={"revision": preview["revision"]})
    assert published.status_code == 202, published.text
