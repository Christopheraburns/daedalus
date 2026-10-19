import base64
import json
import os
import subprocess
import sys
import time

import httpx
import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from factory import auth
from factory.gateway import available_port, catalog, rpc
from factory.packs import Caller
from test_publication import eventually

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"


def unwrap(result):
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def test_credentials_by_mode():
    user = Caller("alice", token="caller-token")
    assert auth.credentials({"auth_mode": "none"}, user) == ({}, {})
    assert auth.credentials(None, user) == ({}, {})
    assert auth.credentials({"auth_mode": "static", "secret_ref": "FACTORY_SECRET_X"}, user, {"FACTORY_SECRET_X": "s"}) == ({"Authorization": "Bearer s"}, {})
    with pytest.raises(ValueError, match="FACTORY_SECRET_X is not set"):
        auth.credentials({"auth_mode": "static", "secret_ref": "FACTORY_SECRET_X"}, user, {})
    assert auth.credentials({"auth_mode": "forward-token"}, user) == ({"Authorization": "Bearer caller-token"}, {})
    assert auth.credentials({"auth_mode": "forward-token"}, Caller("alice")) == ({}, {})  # tests and probes carry no caller token
    with pytest.raises(ValueError, match="Kerberos"):
        auth.credentials({"auth_mode": "proxy-doas", "proxy_principal": "svc@EXAMPLE", "keytab_ref": "FACTORY_SECRET_KT", "doas_parameter": "doAs"}, user)
    for bad in ({"auth_mode": "static"}, {"auth_mode": "static", "secret_ref": "PASSWORD"}, {"auth_mode": "proxy-doas"}, {"auth_mode": "proxy-doas", "proxy_principal": "svc", "keytab_ref": "FACTORY_SECRET_KT", "doas_parameter": "do as"}):
        with pytest.raises(ValueError):
            auth.validate(bad)


def connection(client, **spec):
    response = client.post("/api/connections", json={"name": spec.get("name", "Mock"), "base_url": MOCK, **spec})
    assert response.status_code == 201, response.text
    return response.json()


def tool(client, name, connection_id, **spec):
    body = {"name": name, "description": f"{name} tool", "connection_id": connection_id, **spec}
    response = client.post("/api/tools", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def run_tool(client, item, arguments):
    response = client.post(f"/api/tools/{item['id']}/test", headers={"If-Match": str(item["revision"])}, json={"arguments": arguments})
    assert response.status_code == 200, response.text
    outcome = response.json()
    assert outcome["success"] or "error" in outcome or "result" in outcome, outcome
    return outcome


def result_of(client, item, arguments):
    outcome = run_tool(client, item, arguments)
    assert "result" in outcome, outcome
    return outcome["result"]


@gateway
def test_static_and_forwarded_credentials_reach_the_backend(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_MOCK", "s3cret-value-123")
    assert client.post("/api/connections", json={"name": "Bad", "base_url": MOCK, "auth_mode": "static"}).status_code == 422
    assert client.post("/api/connections", json={"name": "Bad", "base_url": MOCK, "auth_mode": "static", "secret_ref": "PASSWORD"}).status_code == 422
    static = connection(client, name="Static", auth_mode="static", secret_ref="FACTORY_SECRET_MOCK")
    assert "s3cret" not in client.get("/api/workspace").text
    # Python tool: ctx.client() carries the static secret.
    fetch = tool(client, "fetch_static", static["id"], kind="python", pack="demo", function="fetch_json")
    seen = unwrap(result_of(client, fetch, {"body": {"path": "/fixture/echo"}}))["items"]
    assert seen["authorization"] == "Bearer s3cret-value-123"
    # HTTP tool: the gateway injects the same secret through its backend policy.
    rest = tool(client, "echo_static", static["id"], method="GET", path="/fixture/echo")
    assert unwrap(result_of(client, rest, {}))["authorization"] == "Bearer s3cret-value-123"
    # A missing secret fails the candidate with a clear message instead of a silent unauthenticated call.
    monkeypatch.delenv("FACTORY_SECRET_MOCK")
    failed = run_tool(client, rest, {})
    assert not failed["success"] and "FACTORY_SECRET_MOCK is not set" in failed["error"]
    monkeypatch.setenv("FACTORY_SECRET_MOCK", "s3cret-value-123")
    # forward-token without caller identity on this server: Python tools report it, HTTP tools cannot be configured.
    forward = connection(client, name="Forward", auth_mode="forward-token")
    whoami_fetch = tool(client, "fetch_forward", forward["id"], kind="python", pack="demo", function="fetch_json")
    assert unwrap(result_of(client, whoami_fetch, {"body": {"path": "/fixture/echo"}}))["items"]["authorization"] is None  # no caller in a Builder test
    rest_forward = tool(client, "echo_forward", forward["id"], method="GET", path="/fixture/echo")
    outcome = run_tool(client, rest_forward, {})
    assert not outcome["success"] and "FACTORY_JWT_ISSUER" in outcome["error"]
    # proxy-doas: Python only, and the Kerberos step is the on-cluster integration point.
    proxy = connection(client, name="Proxy", auth_mode="proxy-doas", proxy_principal="clouderabind@EXAMPLE.COM", keytab_ref="FACTORY_SECRET_KEYTAB")
    assert client.post("/api/tools", json={"name": "rest_proxy", "description": "x", "connection_id": proxy["id"], "method": "GET", "path": "/fixture/echo"}).status_code == 201
    rest_proxy = next(t for t in client.get("/api/workspace").json()["tools"] if t["name"] == "rest_proxy")
    assert client.post(f"/api/tools/{rest_proxy['id']}/validate", headers={"If-Match": "1"}).status_code == 422
    py_proxy = tool(client, "fetch_proxy", proxy["id"], kind="python", pack="demo", function="fetch_json")
    assert "Kerberos" in unwrap(result_of(client, py_proxy, {"body": {"path": "/fixture/echo"}}))["error"]


def issuer_fixture(directory):
    """A throwaway RSA issuer: JWKS file for the gateway and a signer for tests."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = key.public_key().public_numbers()
    b64 = lambda n: base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()
    jwks = {"keys": [{"kty": "RSA", "kid": "test-key", "use": "sig", "alg": "RS256", "n": b64(numbers.n), "e": b64(numbers.e)}]}
    path = directory / "jwks.json"
    path.write_text(json.dumps(jwks))
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())

    def sign(subject, **claims):
        now = int(time.time())
        return pyjwt.encode({"iss": "https://knox.example/gateway", "aud": "daedalus", "sub": subject, "iat": now, "exp": now + 600, **claims}, pem, algorithm="RS256", headers={"kid": "test-key"})
    return path, sign


@gateway
def test_caller_identity_flows_from_jwt_to_tools_and_backends(registry, monkeypatch, tmp_path):
    client, sessions, settings = registry
    jwks, sign = issuer_fixture(tmp_path)
    port, probe = available_port(), available_port()
    monkeypatch.setenv("FACTORY_GATEWAY_PORT", str(port))
    monkeypatch.setenv("FACTORY_PROBE_PORT", str(probe))
    monkeypatch.setenv("FACTORY_GATEWAY_BIND", "127.0.0.1")
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "server"))
    monkeypatch.setenv("FACTORY_JWT_ISSUER", "https://knox.example/gateway")
    monkeypatch.setenv("FACTORY_JWT_AUDIENCE", "daedalus")
    monkeypatch.setenv("FACTORY_JWT_JWKS_FILE", str(jwks))
    # In Workbench the Builder and Server applications share these settings; build a Builder that sees them.
    from fastapi.testclient import TestClient
    from factory.api import create_app
    from factory.settings import Settings
    client = TestClient(create_app(Settings()))
    client.headers["Authorization"] = registry[0].headers["Authorization"]
    forward = connection(client, name="Forward", auth_mode="forward-token")
    whoami = tool(client, "whoami", None, kind="python", pack="demo", function="whoami")
    fetch = tool(client, "fetch", forward["id"], kind="python", pack="demo", function="fetch_json")
    rest = tool(client, "echo", forward["id"], method="GET", path="/fixture/echo")
    for item, arguments in ((whoami, {}), (fetch, {"body": {"path": "/fixture/echo"}}), (rest, {})):
        assert run_tool(client, item, arguments)["success"]
    # Candidate verification has no caller, so the backend saw no credential; the live server forwards it.
    assert unwrap(result_of(client, rest, {}))["authorization"] is None
    preview = client.get("/api/releases/preview").json()
    assert preview["problems"] == [], preview
    log = (tmp_path / "controller.log").open("w")
    process = subprocess.Popen([sys.executable, "-m", "factory.controller"], env=os.environ.copy(), stdout=log, stderr=log)
    public, loopback = f"http://127.0.0.1:{port}/mcp", f"http://127.0.0.1:{probe}/mcp"
    try:
        eventually(lambda: client.get("/api/workspace").json()["server"]["runtime"].get("ready"))
        response = client.post("/api/releases", json={"revision": preview["revision"]})
        assert response.status_code == 202, response.text
        eventually(lambda: client.get("/api/workspace").json()["server"]["active_release_id"] == response.json()["id"])
        # The public port accepts only the issuer's tokens; Daedalus's own token works on loopback.
        assert httpx.post(public, json={}).status_code == 401
        assert httpx.post(public, headers={"Authorization": "Bearer " + settings.gateway_token}, json={}).status_code == 401
        assert [t["name"] for t in catalog(loopback, settings.gateway_token)] == ["echo", "fetch", "whoami"]
        alice = sign("alice")
        assert [t["name"] for t in catalog(public, alice)] == ["echo", "fetch", "whoami"]
        assert unwrap(rpc(public, alice, "tools/call", {"name": "whoami", "arguments": {}})) == {"username": "alice", "token_presented": True}
        assert unwrap(rpc(public, alice, "tools/call", {"name": "fetch", "arguments": {"body": {"path": "/fixture/echo"}}}))["items"]["authorization"] == "Bearer " + alice
        assert unwrap(rpc(public, alice, "tools/call", {"name": "echo", "arguments": {}}))["authorization"] == "Bearer " + alice
        bob = sign("bob")
        assert unwrap(rpc(public, bob, "tools/call", {"name": "whoami", "arguments": {}}))["username"] == "bob"
        assert httpx.post(public, headers={"Authorization": "Bearer " + sign("eve", aud="other")}, json={}).status_code == 401
        # Without a JWT (loopback probe) tools act as the development user and forward nothing.
        assert unwrap(rpc(loopback, settings.gateway_token, "tools/call", {"name": "whoami", "arguments": {}})) == {"username": "development", "token_presented": False}
    except Exception:
        print((tmp_path / "controller.log").read_text()[-12000:])
        raise
    finally:
        process.terminate()
        process.wait(timeout=20)
        log.close()
