import os
import socket

import pytest

from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import candidate, rpc
from test_s3 import s3_available

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"


def connection(client, **spec):
    response = client.post("/api/connections", json={"name": spec.pop("name", "Mock"), "base_url": MOCK, **spec})
    assert response.status_code == 201, response.text
    return response.json()


def check(client, item):
    response = client.post(f"/api/connections/{item['id']}/check", headers={"If-Match": str(item["revision"])})
    assert response.status_code == 200, response.text
    return response.json()


@gateway
def test_connection_checks_run_each_protocols_probe(registry, monkeypatch):
    client, _, _ = registry
    rest = connection(client, name="REST")
    assert rest["probe_summary"] is None
    checked = check(client, rest)
    assert checked["probe_summary"]["success"] and "answered HTTP" in checked["probe_summary"]["message"] and checked["probe_summary"]["pack"] == "rest"
    hdfs = check(client, connection(client, name="HDFS", protocol="webhdfs"))
    assert hdfs["probe_summary"]["success"] and "WebHDFS answered" in hdfs["probe_summary"]["message"] and hdfs["probe_summary"]["pack"] == "hdfs"
    if s3_available():
        # Policy rows replace the bootstrap origins, so keep the mock API approved alongside the S3 fixture.
        for origin in (MOCK, "http://s3:8333"):
            assert client.post("/api/policies/origins", json={"origin": origin, "description": "fixture"}).status_code == 201
        monkeypatch.setenv("FACTORY_SECRET_S3", "daedalus:daedalus-secret-key")
        s3 = connection(client, name="S3", base_url="http://s3:8333", protocol="s3", auth_mode="s3-sigv4", secret_ref="FACTORY_SECRET_S3")
        assert "accepted the signature" in check(client, s3)["probe_summary"]["message"]
        monkeypatch.setenv("FACTORY_SECRET_S3", "daedalus:wrong")
        wrong = check(client, {**s3, "revision": 1})
        assert not wrong["probe_summary"]["success"]
    # A missing secret fails the check with its name; editing the connection clears the result.
    unset = connection(client, name="Unset", auth_mode="static", secret_ref="FACTORY_SECRET_NOT_SET")
    failed = check(client, unset)
    assert not failed["probe_summary"]["success"] and "FACTORY_SECRET_NOT_SET" in failed["probe_summary"]["message"]
    assert client.post(f"/api/connections/{unset['id']}/check", headers={"If-Match": "7"}).status_code == 409
    updated = client.patch(f"/api/connections/{unset['id']}", headers={"If-Match": "1"}, json={"name": "Unset", "base_url": MOCK, "auth_mode": "none"}).json()
    assert updated["probe_summary"] is None
    assert next(c for c in client.get("/api/workspace").json()["connections"] if c["name"] == "REST")["probe_summary"]["pack"] == "rest"


@gateway
def test_federated_mcp_connection_discovers_and_serves_upstream_tools(registry, monkeypatch):
    client, _, settings = registry
    upstream_tools = [{"id": n, "revision": 1, "spec": ToolSpec(name=n, description=f"{n} upstream", kind="python", pack="demo", function=n).model_dump()} for n in ("echo", "whoami")]
    with candidate(compile_bundle(upstream_tools, {}, []), settings) as (upstream_url, upstream_token, _):
        origin = upstream_url.rsplit("/", 1)[0]
        for approved in (MOCK, origin):
            assert client.post("/api/policies/origins", json={"origin": approved, "description": "fixture"}).status_code == 201
        monkeypatch.setenv("FACTORY_SECRET_UPSTREAM", upstream_token)
        helios = connection(client, name="Helios", base_url=upstream_url, protocol="mcp", auth_mode="static", secret_ref="FACTORY_SECRET_UPSTREAM", federate=True)
        # Federated but not yet checked: publishing is blocked with a clear reason.
        assert any("check the MCP connection" in p for p in client.get("/api/releases/preview").json()["problems"])
        checked = check(client, helios)
        assert checked["probe_summary"]["success"] and checked["probe_summary"]["message"] == "2 tools discovered"
        assert [t["name"] for t in checked["discovered"]] == ["echo", "whoami"] and "upstream" in checked["discovered"][0]["description"]
        preview = client.get("/api/releases/preview").json()
        assert preview["problems"] == [] and preview["added"] == ["echo", "whoami"]
        # Name collisions with local tools are refused before anything is published.
        local_echo = client.post("/api/tools", json={"name": "echo", "description": "Local echo.", "kind": "python", "pack": "demo", "function": "echo"}).json()
        assert any("unique" in p for p in client.get("/api/releases/preview").json()["problems"])
        assert client.delete(f"/api/tools/{local_echo['id']}", headers={"If-Match": "1"}).status_code == 204
        # The release serves the upstream tools through this server's gateway, with its own token in front.
        published = client.post("/api/releases", json={"revision": client.get("/api/workspace").json()["server"]["revision"]})
        assert published.status_code == 202, published.text
        release = next(r for r in client.get("/api/workspace").json()["releases"] if r["id"] == published.json()["id"])
        assert release["tool_names"] == ["echo", "whoami"]
        bundle = compile_bundle([], {helios["id"]: {**{k: v for k, v in helios.items() if k not in {"id", "revision", "probe_summary", "discovered"}}, "_discovered": ["echo", "whoami"]}}, [origin])
        assert bundle["federated"] == [{"connection_id": helios["id"], "tools": ["echo", "whoami"]}] and "_discovered" not in bundle["connections"][helios["id"]]
        with candidate(bundle, settings) as (url, token, tools):
            assert [t["name"] for t in tools] == ["echo", "whoami"]
            result = rpc(url, token, "tools/call", {"name": "echo", "arguments": {"body": {"text": "through two gateways"}}})
            assert result["structuredContent"] == {"text": "through two gateways"}
        # Turning federation off removes the tools from the next release.
        assert client.patch(f"/api/connections/{helios['id']}", headers={"If-Match": "1"}, json={"name": "Helios", "base_url": upstream_url, "protocol": "mcp", "auth_mode": "static", "secret_ref": "FACTORY_SECRET_UPSTREAM", "federate": False}).status_code == 200
        assert client.get("/api/releases/preview").json()["problems"] == []
