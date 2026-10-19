"""Pinned agentgateway process and version-specific MCP probes."""

import hashlib
import json
import re
import os
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from .compiler import canonical, executor_schema
from .settings import LEGACY, MODERN, ROOT

MAX_RESPONSE = 1024 * 1024
# Shared secret between the gateway target policy and the loopback executor.
KEY_HEADER = "x-daedalus-executor-key"
USER_HEADER = "x-daedalus-user"
TOKEN_HEADER = "x-daedalus-caller-token"


class GatewayError(ValueError):
    pass


@dataclass
class Executor:
    process: subprocess.Popen
    port: int
    key: str
    directory: Path


def rpc(url, token, method, params=None, version=MODERN):
    params = dict(params or {})
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": version}
    if version == MODERN:
        params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": version,
            "io.modelcontextprotocol/clientInfo": {"name": "daedalus", "version": "0.1.0"},
            "io.modelcontextprotocol/clientCapabilities": {},
        }
        headers["Mcp-Method"] = method
        if "name" in params:
            headers["Mcp-Name"] = params["name"]
    payload = {"jsonrpc": "2.0", "id": "factory-probe", "method": method, "params": params}
    with httpx.Client(timeout=15, trust_env=False, follow_redirects=False) as client:
        with client.stream("POST", url, headers=headers, json=payload) as response:
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > MAX_RESPONSE:
                    raise GatewayError("Gateway response exceeded 1 MiB")
                if "text/event-stream" in response.headers.get("content-type", ""):
                    for line in bytes(data).decode(errors="replace").splitlines():
                        if line.startswith("data: "):
                            try:
                                message = json.loads(line[6:])
                            except json.JSONDecodeError:
                                continue
                            if message.get("id") == payload["id"]:
                                return rpc_result(message, version)
            try:
                message = json.loads(data)
            except ValueError as exc:
                raise GatewayError(f"Gateway returned HTTP {response.status_code} without an MCP result: {bytes(data[:200]).decode(errors='replace')}") from exc
            if isinstance(message, dict) and "result" not in message and "error" not in message:
                # Not a JSON-RPC reply at all: a timeout or proxy page. Say what it was instead of "missing result".
                timeout = " (the gateway's 10-second request limit or 8-second backend limit was reached)" if response.status_code in (502, 504) else ""
                raise GatewayError(f"Gateway returned HTTP {response.status_code} instead of an MCP result{timeout}: {canonical(message)[:300]}")
            return rpc_result(message, version)


def rpc_result(message, version):
    if "error" in message:
        raise GatewayError(f"MCP error {message['error'].get('code')}: {message['error'].get('message', '')[:300]}")
    result = message.get("result")
    if not isinstance(result, dict):
        raise GatewayError("Missing MCP result")
    if version == MODERN and result.get("resultType") != "complete":
        raise GatewayError("Modern response missing resultType=complete")
    return result


def catalog(url, token, version=MODERN):
    if version == MODERN:
        discovery = rpc(url, token, "server/discover")
        if MODERN not in discovery.get("supportedVersions", []):
            raise GatewayError("Gateway does not advertise the requested modern protocol")
    else:
        discovery = rpc(url, token, "initialize", {"protocolVersion": LEGACY, "capabilities": {}, "clientInfo": {"name": "daedalus", "version": "0.1.0"}}, LEGACY)
        if discovery.get("protocolVersion") != LEGACY:
            raise GatewayError("Legacy version was not accepted")
    result = rpc(url, token, "tools/list", version=version)
    if result.get("nextCursor"):
        raise GatewayError("Unexpected paginated catalog for the bounded initial profile")
    if version == MODERN and ("ttlMs" not in result or "cacheScope" not in result):
        raise GatewayError("Modern catalog missing cache metadata")
    return sorted(result.get("tools", []), key=lambda t: t["name"])


def openapi_target_names(bundle, release_id):
    return [f"r-{release_id.replace('-', '')}-{i}" for i, _ in enumerate(bundle["targets"])]


def executor_target_name(release_id):
    return f"r-{release_id.replace('-', '')}-py"


def federated_target_names(bundle, release_id):
    return [f"r-{release_id.replace('-', '')}-f{i}" for i, _ in enumerate(bundle.get("federated", []))]


def target_names(bundle, release_id):
    names = openapi_target_names(bundle, release_id)
    if bundle.get("python_tools"):
        names.append(executor_target_name(release_id))
    names.extend(federated_target_names(bundle, release_id))
    return names or [f"r-{release_id.replace('-', '')}-empty"]


def expected_names(bundle):
    return [t["spec"]["name"] for t in bundle["tools"]] + [name for entry in bundle.get("federated", []) for name in entry["tools"]]


def target_policies(connection, secrets, jwt, forwarding):
    """Per-connection backend policies for declarative HTTP tools (see auth.py for the modes)."""
    mode = connection.get("auth_mode", "none")
    if mode == "static":
        return {"backendAuth": {"key": {"value": {"file": secrets[connection["secret_ref"]]}}}}
    if mode == "forward-token":
        if jwt:
            return {"backendAuth": {"passthrough": {}}}
        if forwarding:
            return None  # candidate verification runs without caller identity; the live server forwards it
        raise GatewayError("Connections that forward the caller's token need caller identity on this server (FACTORY_JWT_ISSUER)")
    return None


def executor_policies(executor, jwt):
    """The executor learns the caller from headers the gateway controls, never from the client."""
    default_user = os.getenv("FACTORY_EXECUTOR_DEFAULT_USER", "development")
    policies = {"requestHeaderModifier": {"set": {KEY_HEADER: executor.key}}}
    if jwt:
        # The probe port carries no JWT, so the expression falls back to the development user there.
        policies["transformations"] = {"request": {"set": {USER_HEADER: f"has(jwt.sub) ? jwt.sub : {json.dumps(default_user)}"}}}
        policies["backendAuth"] = {"passthrough": {"location": {"header": {"name": TOKEN_HEADER}}}}  # bare token; tools add the scheme
    else:
        policies["transformations"] = {"request": {"set": {USER_HEADER: json.dumps(default_user)}}}
    return policies


def materialize_secrets(bundle, directory):
    """Static connection secrets as 0600 files the gateway reads; missing ones fail the release."""
    paths = {}
    for connection in bundle.get("connections", {}).values():
        if connection.get("auth_mode") == "static":
            ref = connection["secret_ref"]
            value = os.environ.get(ref, "")
            if not value:
                raise GatewayError(f"Secret {ref} is not set in this application's environment")
            Path(directory).mkdir(parents=True, exist_ok=True)
            path = Path(directory) / ref
            path.write_text(value)
            path.chmod(0o600)
            paths[ref] = str(path)
    return paths


def api_key_policy(token):
    return {"mode": "strict", "keys": [{"keyHash": "sha256:" + hashlib.sha256(token.encode()).hexdigest()}]}


def gateway_config(bundle, release_id, settings, port=None, admin_port=15000, host=None, token=None, executor=None, secrets=None, jwt=None, probe_port=None, forwarding=False):
    targets = []
    secrets = secrets or {}
    for name, target in zip(openapi_target_names(bundle, release_id), bundle["targets"]):
        entry = {"name": name, "openapi": {"host": target["host"], "schema": canonical(target["schema"])}}
        policies = target_policies(bundle["connections"][target["connection_id"]], secrets, jwt, forwarding)
        if policies:
            entry["policies"] = policies
        targets.append(entry)
    if bundle.get("python_tools"):
        if executor is None:
            raise GatewayError("Python tools require a running executor")
        targets.append({"name": executor_target_name(release_id), "openapi": {"host": f"http://127.0.0.1:{executor.port}", "schema": canonical(executor_schema(bundle["python_tools"]))},
            "policies": executor_policies(executor, jwt)})
    for name, entry in zip(federated_target_names(bundle, release_id), bundle.get("federated", [])):
        connection = bundle["connections"][entry["connection_id"]]
        target = {"name": name, "mcp": {"host": connection["base_url"]}}
        policies = target_policies(connection, secrets, jwt, forwarding)
        if policies:
            target["policies"] = policies
        targets.append(target)
    if not targets:
        targets = [{"name": target_names(bundle, release_id)[0], "openapi": {"host": "http://127.0.0.1:9", "schema": canonical({"openapi": "3.0.3", "info": {"title": "Empty server", "version": "1"}, "servers": [{"url": "/"}], "paths": {}})}}]
    origin_rule = '!("origin" in request.headers) || request.headers["origin"] in ' + canonical(settings.browser_origins)
    public = {"port": port or settings.gateway_port, "bindAddress": host or settings.gateway_host, "authorization": {"rules": [origin_rule]}}
    gateways = {"factory": public}
    if jwt:
        # Clients present the issuer's JWT; Daedalus verifies the live catalog with its own token on loopback.
        public["jwtAuth"] = {"mode": "strict", "issuer": jwt["issuer"], "jwks": jwt["jwks"], **({"audiences": jwt["audiences"]} if jwt.get("audiences") else {})}
        gateways["probe"] = {"port": probe_port or settings.probe_port, "bindAddress": "127.0.0.1", "apiKey": api_key_policy(token or settings.gateway_token), "authorization": {"rules": [origin_rule]}}
    else:
        public["apiKey"] = api_key_policy(token or settings.gateway_token)
    return {
        "config": {"adminAddr": f"127.0.0.1:{admin_port}", "statsAddr": "off", "readinessAddr": "off", "workerThreads": 2},
        "gateways": gateways,
        "mcp": {"gateways": list(gateways), "statefulMode": "stateless", "prefixMode": "never", "failureMode": "failClosed", "targets": targets,
            "policies": {"timeout": {"requestTimeout": "10s", "backendRequestTimeout": "8s", "responseIdleTimeout": "5s"}}},
    }


def validate_config(config, settings, path):
    schema = json.loads((ROOT / "schemas/vendor/agentgateway-1.6.0.json").read_text())
    Draft202012Validator(schema).validate(config)
    path.write_text(canonical(config))
    process = subprocess.run([settings.gateway_binary, "--validate-only", "-f", str(path)], capture_output=True, text=True, timeout=20)
    if process.returncode:
        raise GatewayError("Generated configuration rejected by agentgateway: " + process.stderr[-600:])


def write_atomic(path, config):
    staged = path.with_suffix(".next")
    with staged.open("w") as file:
        file.write(canonical(config))
        file.flush()
        os.fsync(file.fileno())
    os.replace(staged, path)


def stop_process(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


def available_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_executor(bundle, directory, port=None, log=None):
    """Start the loopback executor for a bundle and wait until it is healthy.

    Registry credentials and management tokens are withheld from tool code; only
    FACTORY_EXECUTOR_* and FACTORY_PACK_* settings pass through.
    """
    port = port or available_port()
    key = secrets.token_urlsafe(32)
    path = Path(directory) / "executor-bundle.json"
    path.write_text(canonical(bundle))
    env = {k: v for k, v in os.environ.items() if not k.startswith(("FACTORY_", "DATABASE_", "POSTGRES_")) or k.startswith(("FACTORY_EXECUTOR_", "FACTORY_PACK_", "FACTORY_SECRET_"))}
    env.update(FACTORY_EXECUTOR_KEY=key, PYTHONPATH=str(ROOT / "services"))
    process = subprocess.Popen([sys.executable, "-m", "factory.executor", "--bundle", str(path), "--port", str(port)], env=env, stdout=log, stderr=log, start_new_session=True)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise GatewayError("Executor exited during startup; see its log")
        try:
            with httpx.Client(timeout=2, trust_env=False) as client:
                if client.get(f"http://127.0.0.1:{port}/healthz").status_code == 200:
                    return Executor(process, port, key, Path(directory))
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    stop_process(process)
    raise GatewayError("Executor did not become ready within 20 seconds")


def wait_catalog(url, token, process, expected, timeout=15):
    """Wait for the gateway to serve exactly the expected tool names; None accepts whatever it serves (discovery)."""
    deadline = time.monotonic() + timeout
    last_error = "Gateway not ready"
    delay = 0.2
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise GatewayError("Gateway process exited before verification")
        try:
            tools = catalog(url, token)
            if expected is None or [t["name"] for t in tools] == sorted(expected):
                return tools
            last_error = "Gateway catalog has not converged"
        except GatewayError as exc:
            # A JSON-RPC error or an upstream HTTP error is an answer, not a not-ready gateway: retrying only
            # repeats it against upstream servers (and can trip their rate limits).
            if re.match(r"MCP error -32(600|601|602)|Gateway returned HTTP 4\d\d instead", str(exc)):
                raise
            last_error = str(exc)
        except (httpx.HTTPError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(delay)
        delay = min(delay * 2, 1.6)
    raise GatewayError(last_error)


def gateway_log_tail(path, limit=8):
    """The last warning/error lines from a candidate's gateway and executor log, for test logs.
    Timestamps, client ports and durations are dropped so repeats collapse into one line with a count."""
    try:
        lines = Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return []
    flagged = []
    for line in lines:
        if not any(word in line.lower() for word in ("error", "warn", "traceback", "exception", "failed")):
            continue
        text = re.sub(r"^\S+Z\s+", "", line.strip())
        text = re.sub(r"\s(src\.addr|duration|gateway|listener|route|http\.host|http\.version)=\S+", "", text)
        if flagged and flagged[-1][0] == text:
            flagged[-1][1] += 1
        else:
            flagged.append([text, 1])
    return [(text if count == 1 else f"{text} (x{count})")[:400] for text, count in flagged[-limit:]]


@contextmanager
def candidate(bundle, settings, discover=False, events=None):
    """An isolated gateway (and executor) for one bundle. `events(code, level="info", **values)`
    receives each step so the Builder can show a test log; codes are translated by the UI."""
    events = events or (lambda *args, **kwargs: None)
    with tempfile.TemporaryDirectory(prefix="factory-candidate-") as directory:
        port, admin = available_port(), available_port()
        while admin == port:
            admin = available_port()
        token = secrets.token_urlsafe(32)
        path = Path(directory) / "gateway.json"
        with (Path(directory) / "gateway.log").open("w") as log:
            executor = None
            try:
                # The gateway fails closed if a target is unreachable at startup, so the executor comes first.
                if bundle.get("python_tools"):
                    executor = start_executor(bundle, directory, log=log)
                    events("executor_started", port=executor.port, tools=len(bundle["python_tools"]))
                secret_files = materialize_secrets(bundle, Path(directory) / "secrets")
                if secret_files:
                    events("secrets_written", count=len(secret_files))
                config = gateway_config(bundle, "candidate", settings, port, admin, "127.0.0.1", token, executor, secret_files, forwarding=settings.jwt() is not None)
                validate_config(config, settings, path)
                events("config_validated", targets=len(config["mcp"]["targets"]))
                process = subprocess.Popen([settings.gateway_binary, "-f", str(path)], stdout=log, stderr=log, start_new_session=True)
                events("gateway_started", port=port)
            except BaseException:
                log.flush()
                for line in gateway_log_tail(Path(directory) / "gateway.log"):
                    events("process_log", level="error", line=line)
                if executor:
                    stop_process(executor.process)
                raise
            try:
                url = f"http://127.0.0.1:{port}/mcp"
                tools = wait_catalog(url, token, process, None if discover else expected_names(bundle))
                events("catalog_ready", version=MODERN, tools=", ".join(t["name"] for t in tools) or "-")
                # Both protocol branches are exercised before accepting a release.
                legacy = catalog(url, token, LEGACY)
                if [(t["name"], t.get("inputSchema")) for t in legacy] != [(t["name"], t.get("inputSchema")) for t in tools]:
                    raise GatewayError("Protocol profiles expose different catalogs")
                events("legacy_checked", version=LEGACY)
                yield url, token, tools
            except BaseException:
                log.flush()
                for line in gateway_log_tail(Path(directory) / "gateway.log"):
                    events("process_log", level="error", line=line)
                raise
            finally:
                stop_process(process)
                if executor:
                    stop_process(executor.process)
                events("candidate_stopped")


def verify_effective(bundle, release_id, settings, process, expected_catalog, executor=None):
    url = settings.verify_url()
    names = set(target_names(bundle, release_id))
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise GatewayError("Gateway exited during release activation")
        if executor and executor.process.poll() is not None:
            raise GatewayError("Executor exited during release activation")
        try:
            with httpx.Client(timeout=3, trust_env=False) as client:
                response = client.get("http://127.0.0.1:15000/config_dump")
                response.raise_for_status()
                dump = response.json()
            actual = {t["name"] for b in dump.get("backends", []) for t in b.get("backend", {}).get("mcp", {}).get("target", {}).get("targets", [])}
            if actual == names:
                observed = catalog(url, settings.gateway_token)
                if canonical(observed) == canonical(expected_catalog):
                    return
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.25)
    raise GatewayError("Effective gateway configuration/catalog did not match the candidate release")
