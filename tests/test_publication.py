import os
import subprocess
import sys
import time

import httpx
import pytest

from conftest import add_tool, spec
from factory.db import Release, Server, new_id
from factory.gateway import GatewayError, available_port, catalog, rpc
from factory.settings import LEGACY, SERVER_ID


def eventually(probe, timeout=25):
    end = time.monotonic() + timeout
    last = None
    while time.monotonic() < end:
        try:
            value = probe()
            if value:
                return value
        except (httpx.HTTPError, ValueError) as exc:
            last = exc
        time.sleep(0.25)
    raise AssertionError(f"Condition did not converge: {last}")


def test_publish_reload_remove_rollback_recovery(registry, monkeypatch, tmp_path):
    client, sessions, settings = registry
    port = available_port()
    monkeypatch.setenv("FACTORY_GATEWAY_PORT", str(port))
    monkeypatch.setenv("FACTORY_GATEWAY_BIND", "127.0.0.1")
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "server"))
    url = f"http://127.0.0.1:{port}/mcp"
    token = settings.gateway_token
    log_path = tmp_path / "controller.log"
    log = log_path.open("w")

    def start():
        return subprocess.Popen([sys.executable, "-m", "factory.controller"], env=os.environ.copy(), stdout=log, stderr=log)

    process = start()

    def workspace():
        return client.get("/api/workspace").json()

    def publish():
        preview = client.get("/api/releases/preview").json()
        assert not preview["problems"], preview
        response = client.post("/api/releases", json={"revision": preview["revision"]})
        assert response.status_code == 202, response.text
        id = response.json()["id"]
        eventually(lambda: workspace()["server"]["active_release_id"] == id)
        return id

    try:
        eventually(lambda: workspace()["server"]["runtime"].get("ready"))
        initial = workspace()["server"]["runtime"]
        assert catalog(url, token) == []
        tool, _ = add_tool(client)
        assert catalog(url, token) == []
        with pytest.raises(GatewayError):
            rpc(url, token, "tools/call", {"name": "get_item", "arguments": {"path": {"item_id": "SKU-001"}}})
        result = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"path": {"item_id": "SKU-001"}}})
        assert result.json()["success"], result.text
        assert catalog(url, token) == []
        first_id = publish()
        assert workspace()["tools"][0]["published"]
        assert [t["name"] for t in catalog(url, token)] == ["get_item"]
        assert [t["name"] for t in catalog(url, token, LEGACY)] == ["get_item"]
        result = rpc(url, token, "tools/call", {"name": "get_item", "arguments": {"path": {"item_id": "SKU-002"}}})
        assert result["structuredContent"]["id"] == "SKU-002"
        assert httpx.post(url, json={}).status_code == 401
        assert httpx.post(url, headers={"Authorization": "Bearer " + token, "Origin": "https://evil.example"}, json={}).status_code == 403
        for path in ("/ui", "/config_dump"):
            assert httpx.get(url.replace("/mcp", path), headers={"Authorization": "Bearer " + token}).status_code == 404
        changed = {**spec(tool), "description": "Updated inventory lookup."}
        response = client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}, json=changed)
        assert response.status_code == 200
        assert not workspace()["tools"][0]["published"]
        assert client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "2"}, json={"arguments": {"path": {"item_id": "SKU-001"}}}).json()["success"]
        second_id = publish()
        assert catalog(url, token)[0]["description"] == changed["description"]
        assert workspace()["server"]["runtime"]["gateway_pid"] == initial["gateway_pid"]
        assert workspace()["server"]["runtime"]["gateway_started_at"] == initial["gateway_started_at"]
        with sessions.begin() as session:
            active = session.get(Release, second_id)
            bad = Release(id=new_id(), server_id=SERVER_ID, bundle=active.bundle, checksum="0" * 64, created_by="test")
            session.add(bad)
            server = session.get(Server, SERVER_ID)
            server.desired_release_id = bad.id
            bad_id = bad.id
        eventually(lambda: any(r["id"] == bad_id and r["status"] == "failed" for r in workspace()["releases"]))
        assert workspace()["server"]["active_release_id"] == second_id
        assert catalog(url, token)[0]["description"] == changed["description"]
        assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "2"}, json={**changed, "enabled": False}).status_code == 200
        publish()
        assert catalog(url, token) == []
        with pytest.raises(GatewayError):
            rpc(url, token, "tools/call", {"name": "get_item", "arguments": {"path": {"item_id": "SKU-001"}}})
        response = client.post("/api/releases/rollback", json={"revision": workspace()["server"]["revision"], "release_id": first_id})
        assert response.status_code == 202, response.text
        restored = response.json()["id"]
        eventually(lambda: workspace()["server"]["active_release_id"] == restored)
        assert catalog(url, token)[0]["description"] == tool["description"]
        assert workspace()["server"]["runtime"]["gateway_pid"] == initial["gateway_pid"]
        assert not workspace()["tools"][0]["enabled"]
        process.terminate()
        process.wait(timeout=15)
        process = start()
        eventually(lambda: workspace()["server"]["runtime"].get("ready") and workspace()["server"]["runtime"].get("gateway_started_at") != initial["gateway_started_at"])
        assert catalog(url, token)[0]["description"] == tool["description"]
        assert workspace()["server"]["active_release_id"] == restored
    except Exception:
        print(log_path.read_text()[-12000:])
        raise
    finally:
        process.terminate()
        process.wait(timeout=15)
        log.close()
