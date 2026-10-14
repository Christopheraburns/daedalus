import base64
import os
import re
import socket

import httpx
import pytest

from factory.auth import SigV4Auth
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, candidate, rpc, start_executor, stop_process
from factory.settings import Settings

MINIO = "http://s3:8333"  # SeaweedFS S3 gateway in compose; the Ozone S3 Gateway speaks the same protocol


def s3_available():
    try:
        socket.create_connection(("s3", 8333), timeout=2).close()
        return os.path.exists("/opt/mcp-factory/bin/agentgateway")
    except OSError:
        return False


minio = pytest.mark.skipif(not s3_available(), reason="S3 service (compose) and agentgateway required")
CONNECTION = {"name": "MinIO", "base_url": MINIO, "protocol": "s3", "auth_mode": "s3-sigv4", "secret_ref": "FACTORY_SECRET_MINIO", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
READ = {"list_buckets", "list_objects", "get_object_info", "download_object"}
FUNCTIONS = ["list_buckets", "list_objects", "get_object_info", "download_object", "upload_object", "copy_object", "move_object", "delete_object"]
SMALL_PARTS = {"multipart_threshold": 1024 * 1024, "part_size": 5 * 1024 * 1024}


def s3_tool(name, function, config=None):
    spec = ToolSpec(name=name, description=f"{function} on S3", kind="python", pack="s3", function=function, connection_id="c",
        effect="read" if function in READ else "write", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def signed():
    return httpx.Client(base_url=MINIO, auth=SigV4Auth("daedalus", "daedalus-secret-key"), timeout=60)


@pytest.fixture
def bucket():
    """An empty test bucket. SeaweedFS keeps empty directories as prefixes, so those are removed too."""
    with signed() as client:
        client.put("/daedalus-tests")
        for _ in range(4):
            listing = client.get("/daedalus-tests", params={"list-type": "2"}).text
            for key in re.findall(r"<Key>([^<]+)</Key>", listing):
                client.delete(f"/daedalus-tests/{key}")
            folders = client.get("/daedalus-tests", params={"list-type": "2", "delimiter": "/"}).text
            for prefix in re.findall(r"<Prefix>([^<]+)</Prefix>", folders):
                client.delete(f"/daedalus-tests/{prefix}")
    return "daedalus-tests"


@pytest.fixture
def executor(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_SECRET_MINIO", "daedalus:daedalus-secret-key")
    tools = [s3_tool(f, f) for f in FUNCTIONS] + [s3_tool("multipart_copy", "copy_object", SMALL_PARTS)]
    running = start_executor(compile_bundle(tools, {"c": CONNECTION}, [MINIO]), tmp_path)
    try:
        yield running
    finally:
        stop_process(running.process)


def call(executor, name, **arguments):
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{name}", headers={KEY_HEADER: executor.key}, json=arguments, timeout=120)
    return response.status_code, response.json()


def ok(executor, name, **arguments):
    status, payload = call(executor, name, **arguments)
    assert status == 200, payload
    return payload


def error(executor, name, **arguments):
    status, payload = call(executor, name, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


@minio
def test_s3_pack_manages_objects(executor, bucket):
    assert any(b["name"] == bucket for b in ok(executor, "list_buckets")["buckets"])
    assert ok(executor, "upload_object", bucket=bucket, key="docs/a.txt", content="hello")["length"] == 5
    assert "already exists" in error(executor, "upload_object", bucket=bucket, key="docs/a.txt", content="again")
    assert ok(executor, "upload_object", bucket=bucket, key="docs/a.txt", content="0123456789", overwrite=True)["overwritten"]
    binary = bytes(range(256))
    uploaded = ok(executor, "upload_object", bucket=bucket, key="docs/blob.bin", content=base64.b64encode(binary).decode(), encoding="base64")
    assert uploaded["length"] == 256 and uploaded["etag"]
    assert ok(executor, "upload_object", bucket=bucket, key="other/x.txt", content="x")["length"] == 1
    listing = ok(executor, "list_objects", bucket=bucket)
    assert listing["prefixes"] == ["docs/", "other/"] and listing["objects"] == [] and not listing["truncated"]
    docs = ok(executor, "list_objects", bucket=bucket, prefix="docs/")
    assert [o["key"] for o in docs["objects"]] == ["docs/a.txt", "docs/blob.bin"] and docs["objects"][0]["size"] == 10
    page = ok(executor, "list_objects", bucket=bucket, prefix="docs/", limit=1)
    assert page["truncated"] and page["continuation_token"]
    second = ok(executor, "list_objects", bucket=bucket, prefix="docs/", limit=1, continuation_token=page["continuation_token"])
    assert [o["key"] for o in second["objects"]] == ["docs/blob.bin"]
    info = ok(executor, "get_object_info", bucket=bucket, key="docs/a.txt")
    assert info["size"] == 10 and info["content_type"].startswith("text/plain") and info["etag"]
    text = ok(executor, "download_object", bucket=bucket, key="docs/a.txt")
    assert text["content"] == "0123456789" and text["encoding"] == "utf-8" and not text["truncated"] and text["total"] == 10
    sliced = ok(executor, "download_object", bucket=bucket, key="docs/a.txt", max_bytes=4)
    assert sliced["content"] == "0123" and sliced["truncated"]
    assert ok(executor, "download_object", bucket=bucket, key="docs/a.txt", offset=8)["content"] == "89"
    blob = ok(executor, "download_object", bucket=bucket, key="docs/blob.bin")
    assert blob["encoding"] == "base64" and base64.b64decode(blob["content"]) == binary
    copied = ok(executor, "copy_object", source_bucket=bucket, source_key="docs/a.txt", destination_bucket=bucket, destination_key="docs/b.txt")
    assert copied["size"] == 10 and not copied["multipart"]
    assert "already exists" in error(executor, "copy_object", source_bucket=bucket, source_key="docs/a.txt", destination_bucket=bucket, destination_key="docs/b.txt")
    moved = ok(executor, "move_object", source_bucket=bucket, source_key="docs/b.txt", destination_bucket=bucket, destination_key="archive/b.txt")
    assert moved["moved"] and "NoSuchKey" in error(executor, "get_object_info", bucket=bucket, key="docs/b.txt") or "NotFound" in error(executor, "get_object_info", bucket=bucket, key="docs/b.txt")
    assert ok(executor, "download_object", bucket=bucket, key="archive/b.txt")["content"] == "0123456789"
    assert "NoSuchKey" in error(executor, "download_object", bucket=bucket, key="docs/missing.txt")
    assert "Bucket names" in error(executor, "list_objects", bucket="Bad_Bucket")
    assert "relative" in error(executor, "get_object_info", bucket=bucket, key="../etc")
    assert ok(executor, "delete_object", bucket=bucket, key="docs/a.txt")["deleted"]
    assert ok(executor, "delete_object", bucket=bucket, key="docs/a.txt")["deleted"]  # idempotent
    assert [o["key"] for o in ok(executor, "list_objects", bucket=bucket, prefix="docs/")["objects"]] == ["docs/blob.bin"]


@minio
def test_large_objects_copy_in_parts_without_passing_through_the_executor(executor, bucket):
    payload = os.urandom(11 * 1024 * 1024)
    with signed() as client:
        assert client.put(f"/{bucket}/big.bin", content=payload, headers={"Content-Type": "application/octet-stream"}).status_code == 200
    copied = ok(executor, "multipart_copy", source_bucket=bucket, source_key="big.bin", destination_bucket=bucket, destination_key="big-copy.bin")
    assert copied["multipart"] and copied["parts"] == 3 and copied["size"] == len(payload)
    info = ok(executor, "get_object_info", bucket=bucket, key="big-copy.bin")
    assert info["size"] == len(payload) and "-" in info["etag"]  # multipart ETags carry a part suffix; its value is implementation-specific
    with signed() as client:
        assert client.get(f"/{bucket}/big-copy.bin").content == payload
    tail = ok(executor, "download_object", bucket=bucket, key="big-copy.bin", offset=len(payload) - 16, max_bytes=16)
    assert base64.b64decode(tail["content"]) == payload[-16:] and not tail["truncated"]


@minio
def test_s3_tools_are_served_through_the_gateway(monkeypatch, bucket):
    monkeypatch.setenv("FACTORY_SECRET_MINIO", "daedalus:daedalus-secret-key")
    bundle = compile_bundle([s3_tool("list_objects", "list_objects"), s3_tool("upload_object", "upload_object")], {"c": CONNECTION}, [MINIO])
    with candidate(bundle, Settings()) as (url, token, tools):
        schema = next(t for t in tools if t["name"] == "upload_object")["inputSchema"]["properties"]["body"]
        assert set(schema["required"]) == {"bucket", "key", "content"}
        rpc(url, token, "tools/call", {"name": "upload_object", "arguments": {"body": {"bucket": bucket, "key": "via-gateway.txt", "content": "hi"}}})
        listing = rpc(url, token, "tools/call", {"name": "list_objects", "arguments": {"body": {"bucket": bucket, "delimiter": ""}}})["structuredContent"]
        assert any(o["key"] == "via-gateway.txt" for o in listing["objects"])
    monkeypatch.delenv("FACTORY_SECRET_MINIO")
    with candidate(bundle, Settings()) as (url, token, tools):
        failed = rpc(url, token, "tools/call", {"name": "list_objects", "arguments": {"body": {"bucket": bucket}}})["structuredContent"]
        assert "FACTORY_SECRET_MINIO" in failed["error"]
