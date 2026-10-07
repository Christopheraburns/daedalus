"""Pinned agentgateway process and version-specific MCP probes."""

import hashlib
import json
import os
import secrets
import signal
import socket
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from .compiler import canonical
from .settings import LEGACY, MODERN, ROOT

MAX_RESPONSE = 1024 * 1024


class GatewayError(ValueError):
    pass


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
                raise GatewayError(f"Gateway returned HTTP {response.status_code} without an MCP result") from exc
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


def target_names(bundle, release_id):
    return [f"r-{release_id.replace('-', '')}-{i}" for i, _ in enumerate(bundle["targets"])] or [f"r-{release_id.replace('-', '')}-empty"]


def gateway_config(bundle, release_id, settings, port=None, admin_port=15000, host=None, token=None):
    targets = []
    for name, target in zip(target_names(bundle, release_id), bundle["targets"]):
        targets.append({"name": name, "openapi": {"host": target["host"], "schema": canonical(target["schema"])}})
    if not targets:
        targets = [{"name": target_names(bundle, release_id)[0], "openapi": {"host": "http://127.0.0.1:9", "schema": canonical({"openapi": "3.0.3", "info": {"title": "Empty server", "version": "1"}, "servers": [{"url": "/"}], "paths": {}})}}]
    origin_rule = '!("origin" in request.headers) || request.headers["origin"] in ' + canonical(settings.browser_origins)
    return {
        "config": {"adminAddr": f"127.0.0.1:{admin_port}", "statsAddr": "off", "readinessAddr": "off", "workerThreads": 2},
        "gateways": {"factory": {"port": port or settings.gateway_port, "bindAddress": host or settings.gateway_host,
            "apiKey": {"mode": "strict", "keys": [{"keyHash": "sha256:" + hashlib.sha256((token or settings.gateway_token).encode()).hexdigest()}]},
            "authorization": {"rules": [origin_rule]}}},
        "mcp": {"gateways": ["factory"], "statefulMode": "stateless", "prefixMode": "conditional", "failureMode": "failClosed", "targets": targets,
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


def wait_catalog(url, token, process, expected_names, timeout=15):
    deadline = time.monotonic() + timeout
    last_error = "Gateway not ready"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise GatewayError("Gateway process exited before verification")
        try:
            tools = catalog(url, token)
            if [t["name"] for t in tools] == sorted(expected_names):
                return tools
            last_error = "Gateway catalog has not converged"
        except (httpx.HTTPError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise GatewayError(last_error)


@contextmanager
def candidate(bundle, settings):
    with tempfile.TemporaryDirectory(prefix="factory-candidate-") as directory:
        port, admin = available_port(), available_port()
        while admin == port:
            admin = available_port()
        token = secrets.token_urlsafe(32)
        config = gateway_config(bundle, "candidate", settings, port, admin, "127.0.0.1", token)
        path = Path(directory) / "gateway.json"
        validate_config(config, settings, path)
        with (Path(directory) / "gateway.log").open("w") as log:
            process = subprocess.Popen([settings.gateway_binary, "-f", str(path)], stdout=log, stderr=log, start_new_session=True)
            try:
                url = f"http://127.0.0.1:{port}/mcp"
                tools = wait_catalog(url, token, process, [t["spec"]["name"] for t in bundle["tools"]])
                # Both protocol branches are exercised before accepting a release.
                legacy = catalog(url, token, LEGACY)
                if [(t["name"], t.get("inputSchema")) for t in legacy] != [(t["name"], t.get("inputSchema")) for t in tools]:
                    raise GatewayError("Protocol profiles expose different catalogs")
                yield url, token, tools
            finally:
                stop_process(process)


def verify_effective(bundle, release_id, settings, process, expected_catalog):
    url = f"http://127.0.0.1:{settings.gateway_port}/mcp"
    names = set(target_names(bundle, release_id))
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise GatewayError("Gateway exited during release activation")
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
