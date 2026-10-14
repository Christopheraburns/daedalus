import base64
import os

import httpx
import pytest

from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, USER_HEADER, candidate, rpc, start_executor, stop_process
from factory.settings import Settings

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
CONNECTION = {"name": "HDFS", "base_url": "http://mock-api:8080", "auth_mode": "none", "secret_ref": "", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
READ = {"list_directory", "get_file_status", "download_file"}
FUNCTIONS = ["list_directory", "get_file_status", "make_directory", "move", "delete", "download_file", "upload_file", "copy"]
NAMENODE = {"prefix": "/webhdfs-nn/v1", "follow_redirects": True, "pseudo_auth": True, "allow_recursive_delete": True}


def hdfs_tool(name, function, config=None):
    spec = ToolSpec(name=name, description=f"{function} on HDFS", kind="python", pack="hdfs", function=function, connection_id="c",
        effect="read" if function in READ else "write", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


@pytest.fixture
def executor(tmp_path):
    tools = [hdfs_tool(f, f) for f in FUNCTIONS] + [hdfs_tool(f"nn_{f}", f, NAMENODE) for f in FUNCTIONS] + [hdfs_tool("strict_download", "download_file", {"prefix": "/webhdfs-nn/v1"})]
    running = start_executor(compile_bundle(tools, {"c": CONNECTION}, [CONNECTION["base_url"]]), tmp_path)
    try:
        yield running
    finally:
        stop_process(running.process)


def call(executor, name, user="alice", **arguments):
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{name}", headers={KEY_HEADER: executor.key, USER_HEADER: user}, json=arguments, timeout=30)
    return response.status_code, response.json()


def ok(executor, name, **arguments):
    status, payload = call(executor, name, **arguments)
    assert status == 200, payload
    return payload


def error(executor, name, **arguments):
    status, payload = call(executor, name, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


@gateway
def test_hdfs_pack_manages_files_through_httpfs(executor):
    base = "/tests/alpha"
    call(executor, "nn_delete", path="/tests", recursive=True)  # the fake keeps state between runs
    assert ok(executor, "make_directory", path=base, permission="750") == {"path": base, "created": True}
    assert "octal" in error(executor, "make_directory", path=base, permission="abc")
    assert ok(executor, "upload_file", path=f"{base}/a.txt", content="hello")["length"] == 5
    assert "FileAlreadyExistsException" in error(executor, "upload_file", path=f"{base}/a.txt", content="again")
    assert ok(executor, "upload_file", path=f"{base}/a.txt", content="0123456789", overwrite=True)["overwritten"]
    binary = bytes(range(256))
    assert ok(executor, "upload_file", path=f"{base}/blob.bin", content=base64.b64encode(binary).decode(), encoding="base64")["length"] == 256
    assert "base64" in error(executor, "upload_file", path=f"{base}/bad.bin", content="not base64!", encoding="base64")
    listing = ok(executor, "list_directory", path=base)
    assert [e["name"] for e in listing["entries"]] == ["a.txt", "blob.bin"] and listing["total"] == 2 and not listing["truncated"]
    assert all(e["type"] == "file" and e["modified"].endswith("+00:00") for e in listing["entries"])
    assert ok(executor, "list_directory", path=base, limit=1)["truncated"]
    status = ok(executor, "get_file_status", path=f"{base}/a.txt")
    assert status["type"] == "file" and status["length"] == 10 and status["permission"] == "644"
    assert ok(executor, "get_file_status", path=base)["type"] == "directory"
    text = ok(executor, "download_file", path=f"{base}/a.txt")
    assert text["content"] == "0123456789" and text["encoding"] == "utf-8" and not text["truncated"]
    sliced = ok(executor, "download_file", path=f"{base}/a.txt", max_bytes=4)
    assert sliced["content"] == "0123" and sliced["truncated"]
    tail = ok(executor, "download_file", path=f"{base}/a.txt", offset=8)
    assert tail["content"] == "89" and not tail["truncated"]
    blob = ok(executor, "download_file", path=f"{base}/blob.bin")
    assert blob["encoding"] == "base64" and base64.b64decode(blob["content"]) == binary
    assert ok(executor, "copy", source=f"{base}/a.txt", destination=f"{base}/b.txt")["length"] == 10
    assert "FileAlreadyExistsException" in error(executor, "copy", source=f"{base}/a.txt", destination=f"{base}/b.txt")
    assert "Only files" in error(executor, "copy", source=base, destination="/tests/beta")
    assert ok(executor, "move", source=f"{base}/b.txt", destination=f"{base}/c.txt")["moved"]
    assert "FileNotFoundException" in error(executor, "move", source=f"{base}/missing.txt", destination=f"{base}/d.txt")
    assert "refused" in error(executor, "move", source=f"{base}/a.txt", destination=f"{base}/c.txt")  # destination exists
    assert [e["name"] for e in ok(executor, "list_directory", path=base)["entries"]] == ["a.txt", "blob.bin", "c.txt"]
    assert "FileNotFoundException" in error(executor, "get_file_status", path=f"{base}/missing.txt")
    assert "absolute" in error(executor, "list_directory", path="/tests/../etc")
    assert "absolute" in error(executor, "list_directory", path="relative")
    assert "non empty" in error(executor, "delete", path=base)
    assert "disabled" in error(executor, "delete", path=base, recursive=True)
    assert ok(executor, "delete", path=f"{base}/c.txt") == {"path": f"{base}/c.txt", "deleted": True}
    assert not ok(executor, "delete", path=f"{base}/c.txt")["deleted"]
    assert ok(executor, "nn_delete", path=base, recursive=True)["deleted"]
    assert "FileNotFoundException" in error(executor, "list_directory", path=base)


@gateway
def test_namenode_redirects_and_pseudo_auth(executor):
    call(executor, "nn_delete", path="/tests", recursive=True)
    assert "redirected" in error(executor, "strict_download", path="/data/readme.txt")
    assert ok(executor, "nn_download_file", path="/data/readme.txt")["content"].startswith("Hello from the HDFS fixture")
    assert ok(executor, "nn_upload_file", path="/tests/nn/by-alice.txt", content="via redirect")["length"] == 12
    assert ok(executor, "nn_get_file_status", path="/tests/nn/by-alice.txt")["owner"] == "alice"
    assert ok(executor, "nn_download_file", path="/tests/nn/by-alice.txt")["content"] == "via redirect"
    assert ok(executor, "nn_make_directory", user="bob", path="/tests/nn/bobs")["created"]
    assert ok(executor, "nn_get_file_status", path="/tests/nn/bobs")["owner"] == "bob"
    assert ok(executor, "nn_delete", path="/tests/nn", recursive=True)["deleted"]


@gateway
def test_hdfs_tools_are_served_through_the_gateway():
    bundle = compile_bundle([hdfs_tool("list_directory", "list_directory"), hdfs_tool("download_file", "download_file")], {"c": CONNECTION}, [CONNECTION["base_url"]])
    with candidate(bundle, Settings()) as (url, token, tools):
        schema = next(t for t in tools if t["name"] == "list_directory")["inputSchema"]["properties"]["body"]
        assert schema["required"] == ["path"] and schema["properties"]["limit"]["type"] == "integer"
        listing = rpc(url, token, "tools/call", {"name": "list_directory", "arguments": {"body": {"path": "/data"}}})["structuredContent"]
        assert any(e["name"] == "readme.txt" for e in listing["entries"])
        content = rpc(url, token, "tools/call", {"name": "download_file", "arguments": {"body": {"path": "/data/readme.txt", "max_bytes": 5}}})["structuredContent"]
        assert content == {"path": "/data/readme.txt", "offset": 0, "length": 5, "truncated": True, "encoding": "utf-8", "content": "Hello"}
