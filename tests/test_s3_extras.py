"""The s3_extras seed pack against the SeaweedFS S3 gateway, through the executor."""
import json
import os
import socket

import httpx
import pytest

from factory import packs, packstore
from factory.auth import SigV4Auth
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, start_executor, stop_process

S3 = "http://s3:8333"
PACK = "s3_extras"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
WRITES = {t["function"] for t in INFO["tools"] if t["effect"] == "write"}
CONNECTION = {"name": "S3", "base_url": S3, "protocol": "s3", "auth_mode": "s3-sigv4", "secret_ref": "FACTORY_SECRET_S3X", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
BUCKET = "daedalus-extras"


def s3_available():
    try:
        socket.create_connection(("s3", 8333), timeout=2).close()
        return os.path.exists("/opt/mcp-factory/bin/agentgateway")
    except OSError:
        return False


s3 = pytest.mark.skipif(not s3_available(), reason="S3 service (compose) and agentgateway required")


def seed_tool(name, function, config=None):
    spec = ToolSpec(name=name, description=f"{function} on S3", kind="python", pack=PACK, function=function, connection_id="c",
        effect="write" if function in WRITES else "read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def signed():
    return httpx.Client(base_url=S3, auth=SigV4Auth("daedalus", "daedalus-secret-key"), timeout=60)


@pytest.fixture
def bucket():
    with signed() as client:
        client.put(f"/{BUCKET}")
        for key in ("a.txt", "b.txt", "c.txt", "keep.txt", "with,comma.txt"):
            client.put(f"/{BUCKET}/{key}", content=key.encode())
        client.delete(f"/{BUCKET}/keep.txt", params={"tagging": ""})
    return BUCKET


@pytest.fixture
def executor(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_SECRET_S3X", "daedalus:daedalus-secret-key")
    tools = [seed_tool(t["function"], t["function"]) for t in INFO["tools"]] + [seed_tool("tiny_delete", "delete_objects", {"max_delete_keys": 2})]
    bundle = compile_bundle(tools, {"c": CONNECTION}, [S3], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path)
    try:
        yield running
    finally:
        stop_process(running.process)


def call(executor, tool, **arguments):
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{tool}", headers={KEY_HEADER: executor.key}, json=arguments, timeout=120)
    return response.status_code, response.json()


def ok(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status == 200, payload
    return payload


def error(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


def test_the_seed_declares_five_tools():
    assert INFO["error"] is None and INFO["protocol"] == "s3" and len(INFO["tools"]) == 5
    assert WRITES == {"delete_objects", "set_object_tags", "delete_object_tags"}


@s3
def test_bucket_checks_and_bulk_delete(executor, bucket):
    assert ok(executor, "check_bucket_access", bucket=bucket) == {"bucket": bucket, "accessible": True, "region": ""}
    assert ok(executor, "check_bucket_access", bucket="daedalus-no-such-bucket") == {"bucket": "daedalus-no-such-bucket", "accessible": False, "reason": "NoSuchBucket"}
    assert "lowercase" in error(executor, "check_bucket_access", bucket="Bad_Bucket")
    result = ok(executor, "delete_objects", bucket=bucket, keys="a.txt, b.txt\nmissing.txt")
    assert result == {"bucket": bucket, "deleted": ["a.txt", "b.txt", "missing.txt"], "errors": [], "requested": 3}
    result = ok(executor, "delete_objects", bucket=bucket, keys=json.dumps(["with,comma.txt"]))
    assert result["deleted"] == ["with,comma.txt"]
    with signed() as client:
        assert client.head(f"/{bucket}/a.txt").status_code == 404 and client.head(f"/{bucket}/with,comma.txt").status_code == 404
        assert client.head(f"/{bucket}/c.txt").status_code == 200
    assert "at least one key" in error(executor, "delete_objects", bucket=bucket, keys=" ")
    assert "JSON array" in error(executor, "delete_objects", bucket=bucket, keys="[1, 2]")
    assert "relative paths" in error(executor, "delete_objects", bucket=bucket, keys="../etc/passwd")
    assert "at most 2 keys" in error(executor, "tiny_delete", bucket=bucket, keys="x,y,z")


@s3
def test_object_tags(executor, bucket):
    assert ok(executor, "get_object_tags", bucket=bucket, key="keep.txt") == {"bucket": bucket, "key": "keep.txt", "tags": {}}
    first = ok(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags="owner_team=finance, pii=no")
    assert first == {"bucket": bucket, "key": "keep.txt", "tags": {"owner_team": "finance", "pii": "no"}, "replaced": False}
    merged = ok(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags=json.dumps({"retention": "7 years", "pii": "yes"}))
    assert merged["tags"] == {"owner_team": "finance", "pii": "yes", "retention": "7 years"}
    assert ok(executor, "get_object_tags", bucket=bucket, key="keep.txt")["tags"] == merged["tags"]
    replaced = ok(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags="source=erp", replace=True)
    assert replaced["tags"] == {"source": "erp"} and replaced["replaced"]
    assert "key=value" in error(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags="just-a-word")
    assert "1 to 128" in error(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags="bad*key=1")
    assert "at most 10 tags" in error(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags=",".join(f"k{i}=v" for i in range(11)))
    assert "NoSuchKey" in error(executor, "get_object_tags", bucket=bucket, key="missing.txt")
    ok(executor, "set_object_tags", bucket=bucket, key="keep.txt", tags="a=1,b=2")
    partial = ok(executor, "delete_object_tags", bucket=bucket, key="keep.txt", names="a, zzz")
    assert partial == {"bucket": bucket, "key": "keep.txt", "tags": {"b": "2", "source": "erp"}, "removed": ["a"]}
    assert ok(executor, "delete_object_tags", bucket=bucket, key="keep.txt") == {"bucket": bucket, "key": "keep.txt", "tags": {}, "removed": "all"}
    assert ok(executor, "get_object_tags", bucket=bucket, key="keep.txt")["tags"] == {}
    with signed() as client:
        assert client.get(f"/{bucket}/keep.txt").content == b"keep.txt"  # tagging never touches the object
