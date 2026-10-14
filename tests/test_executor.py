import json
import os
import subprocess
import sys

import httpx
import pytest

from factory import packs
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, available_port, candidate, catalog, rpc, start_executor, stop_process
from factory.settings import Settings
from test_publication import eventually

CONNECTION = {"name": "Mock", "base_url": "http://mock-api:8080", "auth_mode": "none"}
gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")


def python_tool(name, function, **extra):
    spec = ToolSpec(name=name, description=f"{name} tool", kind="python", pack="demo", function=function, **extra).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def unwrap(result):
    # The gateway returns the executor's JSON response as structuredContent; errors carry an "error" key.
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def test_pack_catalog_and_bundle_validation():
    demo = next(p for p in packs.catalog() if p["name"] == "demo")
    assert {t["function"] for t in demo["tools"]} == {"echo", "whoami", "fetch_json"}
    fetch = next(t for t in demo["tools"] if t["function"] == "fetch_json")
    assert fetch["requires_connection"] and fetch["effect"] == "read"
    assert fetch["parameters"] == [{"name": "path", "type": "string", "required": True}, {"name": "limit", "type": "integer", "required": False}]
    with pytest.raises(ValueError):
        compile_bundle([python_tool("missing", "nope")], {}, [])
    with pytest.raises(ValueError):
        compile_bundle([python_tool("needs_connection", "fetch_json")], {}, [])
    with pytest.raises(ValueError):
        compile_bundle([python_tool("wrong_effect", "echo", effect="write")], {}, [])
    with pytest.raises(ValueError):
        ToolSpec(name="http_without_connection", description="x")
    # Packs declare the protocol their tools need; the canvas and compiler only accept matching connections.
    catalog = {p["name"]: p for p in packs.catalog()}
    assert catalog["demo"]["protocol"] == "rest" and catalog["hdfs"]["protocol"] == "webhdfs" and catalog["s3"]["protocol"] == "s3"
    hdfs_list = {"id": "l", "revision": 1, "spec": ToolSpec(name="l", description="list", kind="python", pack="hdfs", function="list_directory", connection_id="c").model_dump()}
    with pytest.raises(ValueError, match="needs a webhdfs connection"):
        compile_bundle([hdfs_list], {"c": CONNECTION}, [CONNECTION["base_url"]])
    with pytest.raises(ValueError, match="REST tools need a rest connection"):
        compile_bundle([{"id": "r", "revision": 1, "spec": ToolSpec(name="r", description="get", connection_id="c", path="/x").model_dump()}], {"c": {**CONNECTION, "protocol": "webhdfs"}}, [CONNECTION["base_url"]])
    with pytest.raises(ValueError, match="S3 connections"):
        compile_bundle([hdfs_list], {"c": {**CONNECTION, "protocol": "webhdfs", "auth_mode": "s3-sigv4", "secret_ref": "FACTORY_SECRET_X"}}, [CONNECTION["base_url"]])
    bundle = compile_bundle([python_tool("echo", "echo"), python_tool("fetch", "fetch_json", connection_id="c")], {"c": CONNECTION}, [CONNECTION["base_url"]])
    assert [t["name"] for t in bundle["python_tools"]] == ["echo", "fetch"]
    assert bundle["targets"] == [] and set(bundle["connections"]) == {"c"}
    assert [t["spec"]["name"] for t in bundle["tools"]] == ["echo", "fetch"]


@gateway
def test_executor_requires_the_gateway_key(tmp_path):
    executor = start_executor(compile_bundle([python_tool("echo", "echo")], {}, []), tmp_path)
    try:
        base = f"http://127.0.0.1:{executor.port}"
        assert httpx.get(base + "/healthz").json() == {"status": "ok", "tools": 1}
        assert httpx.post(base + "/tools/echo", json={"text": "x"}).status_code == 401
        assert httpx.post(base + "/tools/echo", headers={KEY_HEADER: executor.key}, json={"text": "x"}).json() == {"text": "x"}
        assert httpx.post(base + "/tools/echo", headers={KEY_HEADER: executor.key}, json={"nope": 1}).status_code == 422
        assert httpx.post(base + "/tools/other", headers={KEY_HEADER: executor.key}, json={}).status_code == 404
    finally:
        stop_process(executor.process)


@gateway
def test_python_tools_are_served_through_the_gateway(monkeypatch):
    monkeypatch.setenv("FACTORY_EXECUTOR_DEFAULT_USER", "tester")
    bundle = compile_bundle([python_tool("echo", "echo"), python_tool("whoami", "whoami"), python_tool("fetch", "fetch_json", connection_id="c")], {"c": CONNECTION}, [CONNECTION["base_url"]])
    with candidate(bundle, Settings()) as (url, token, tools):
        assert [t["name"] for t in tools] == ["echo", "fetch", "whoami"]
        echo = next(t for t in tools if t["name"] == "echo")
        # agentgateway nests JSON request bodies under "body", exactly as for HTTP tools.
        assert echo["inputSchema"]["properties"]["body"]["required"] == ["text"] and echo["description"] == "echo tool"
        assert unwrap(rpc(url, token, "tools/call", {"name": "echo", "arguments": {"body": {"text": "hi"}}})) == {"text": "hi"}
        assert unwrap(rpc(url, token, "tools/call", {"name": "whoami", "arguments": {}})) == {"username": "tester", "token_presented": False}
        fetched = unwrap(rpc(url, token, "tools/call", {"name": "fetch", "arguments": {"body": {"path": "/inventory/items/SKU-001", "limit": 2}}}))
        assert fetched["items"]["id"] == "SKU-001" and len(fetched["items"]) == 2
        assert "error" in unwrap(rpc(url, token, "tools/call", {"name": "fetch", "arguments": {"body": {"path": "../etc"}}}))


@gateway
def test_python_tool_lifecycle_in_builder(registry):
    client, _, _ = registry
    assert client.post("/api/tools", json={"name": "nope", "description": "x", "kind": "python", "pack": "demo", "function": "missing"}).status_code == 422
    assert client.post("/api/tools", json={"name": "bare", "description": "x"}).status_code == 422
    response = client.post("/api/tools", json={"name": "echo", "description": "Echo text.", "kind": "python", "pack": "demo", "function": "echo"})
    assert response.status_code == 201, response.text
    tool = response.json()
    assert tool["kind"] == "python" and tool["connection_id"] is None and not tool["tested"]
    assert client.post(f"/api/tools/{tool['id']}/validate", headers={"If-Match": "1"}).json()["profile"].startswith("Python pack demo.echo")
    result = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"text": "ping"}}})
    assert result.json()["success"], result.text
    assert client.get("/api/workspace").json()["tools"][0]["tested"]
    assert client.get("/api/releases/preview").json()["problems"] == []
    assert [p["name"] for p in client.get("/api/packs").json()] == ["demo", "hdfs", "rest", "s3"]


@gateway
def test_controller_switches_executors_between_releases(registry, monkeypatch, tmp_path):
    client, _, settings = registry
    port = available_port()
    monkeypatch.setenv("FACTORY_GATEWAY_PORT", str(port))
    monkeypatch.setenv("FACTORY_GATEWAY_BIND", "127.0.0.1")
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "server"))
    url, token = f"http://127.0.0.1:{port}/mcp", settings.gateway_token
    log = (tmp_path / "controller.log").open("w")
    process = subprocess.Popen([sys.executable, "-m", "factory.controller"], env=os.environ.copy(), stdout=log, stderr=log)

    def runtime():
        return client.get("/api/workspace").json()["server"]["runtime"]

    def publish():
        preview = client.get("/api/releases/preview").json()
        assert not preview["problems"], preview
        response = client.post("/api/releases", json={"revision": preview["revision"]})
        assert response.status_code == 202, response.text
        eventually(lambda: client.get("/api/workspace").json()["server"]["active_release_id"] == response.json()["id"])

    try:
        eventually(lambda: runtime().get("ready"))
        assert runtime()["executor_pid"] is None
        tool = client.post("/api/tools", json={"name": "echo", "description": "Echo text.", "kind": "python", "pack": "demo", "function": "echo"}).json()
        assert client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"text": "ping"}}}).json()["success"]
        publish()
        first_pid = runtime()["executor_pid"]
        assert first_pid and runtime()["gateway_pid"]
        assert [t["name"] for t in catalog(url, token)] == ["echo"]
        assert unwrap(rpc(url, token, "tools/call", {"name": "echo", "arguments": {"body": {"text": "live"}}})) == {"text": "live"}
        changed = {**{k: v for k, v in tool.items() if k not in {"id", "revision", "validated", "tested", "test_summary", "published"}}, "description": "Echo text back."}
        assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}, json=changed).status_code == 200
        assert client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "2"}, json={"arguments": {"body": {"text": "ping"}}}).json()["success"]
        publish()
        assert runtime()["executor_pid"] not in (None, first_pid)
        assert catalog(url, token)[0]["description"] == "Echo text back."
        assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "2"}, json={**changed, "enabled": False}).status_code == 200
        publish()
        assert runtime()["executor_pid"] is None
        assert catalog(url, token) == []
        remaining = list((tmp_path / "server" / "releases").iterdir())
        assert len(remaining) == 1 and not (remaining[0] / "executor").exists()  # only the active release's assets stay
    except Exception:
        print((tmp_path / "controller.log").read_text()[-12000:])
        raise
    finally:
        process.terminate()
        process.wait(timeout=20)
        log.close()


PROJECT_PACK = '''"""Project pack written from the Builder."""
from factory.packs import ToolContext, pack_tool


@pack_tool(effect="read")
def shout(ctx: ToolContext, text: str, times: int = 1) -> dict:
    """Upper-case the text and repeat it."""
    return {"text": " ".join([text.upper()] * times), "user": ctx.caller.username}
'''


@gateway
def test_project_packs_are_authored_snapshotted_and_served(registry, monkeypatch, tmp_path):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_PACKS_DIR", str(tmp_path / "packs"))
    author = {"Authorization": "Bearer " + os.environ["FACTORY_AUTHOR_TOKEN"]}
    assert client.put("/api/packs/custom", headers=author, json={"source": PROJECT_PACK}).status_code == 403
    assert client.put("/api/packs/Bad-Name", json={"source": PROJECT_PACK}).status_code == 422
    assert client.put("/api/packs/demo", json={"source": PROJECT_PACK}).status_code == 422
    broken = client.put("/api/packs/custom", json={"source": "def nope(:\n"})
    assert broken.status_code == 422 and "line 1" in broken.json()["detail"]
    no_tools = client.put("/api/packs/custom", json={"source": "x = 1\n"})
    assert no_tools.status_code == 422 and "pack_tool" in no_tools.json()["detail"]
    hostile = client.put("/api/packs/custom", json={"source": "import sys\nsys.exit(3)\n"})
    assert hostile.status_code == 422
    assert client.get("/api/packs/custom").status_code == 404
    saved = client.put("/api/packs/custom", json={"source": PROJECT_PACK})
    assert saved.status_code == 200, saved.text
    assert saved.json()["origin"] == "project" and saved.json()["editable"] and [t["function"] for t in saved.json()["tools"]] == ["shout"]
    assert "def shout" in saved.json()["tools"][0]["source"]
    catalog = client.get("/api/packs").json()
    assert [p["name"] for p in catalog] == ["demo", "hdfs", "rest", "s3", "custom"] and "source" not in catalog[0]
    assert client.get("/api/packs/demo").json()["editable"] is False
    tool = client.post("/api/tools", json={"name": "shout", "description": "Shout.", "kind": "python", "pack": "custom", "function": "shout"}).json()
    result = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"text": "hi", "times": 2}}})
    assert result.json()["success"], result.text
    assert result.json()["result"]["structuredContent"]["text"] == "HI HI"
    assert client.get("/api/workspace").json()["tools"][0]["tested"]
    assert client.delete("/api/packs/custom").status_code == 409
    # Editing the pack invalidates test evidence and changes the release snapshot.
    assert client.put("/api/packs/custom", json={"source": PROJECT_PACK.replace("text.upper()", "text.lower()")}).status_code == 200
    assert not client.get("/api/workspace").json()["tools"][0]["tested"]
    assert client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"text": "HI"}}}).json()["result"]["structuredContent"]["text"] == "hi"
    preview = client.get("/api/releases/preview").json()
    assert preview["problems"] == []
    published = client.post("/api/releases", json={"revision": preview["revision"]})
    assert published.status_code == 202, published.text
    release = next(r for r in client.get("/api/workspace").json()["releases"] if r["id"] == published.json()["id"])
    assert release["tool_names"] == ["shout"]
    assert client.delete(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}).status_code == 204
    assert client.delete("/api/packs/custom").status_code == 204
    assert [p["name"] for p in client.get("/api/packs").json()] == ["demo", "hdfs", "rest", "s3"]
