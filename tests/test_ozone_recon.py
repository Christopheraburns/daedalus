"""The ozone_recon seed pack against the Recon fake: volumes, buckets and keys, namespace summaries, disk usage, quotas,
file size distributions, cluster state, storage distribution, file counts and the in-flight key summaries; anonymous
simple authentication, Knox credentials, a simple Recon that needs user.name, and an older Recon without the newer endpoints."""
import base64
import json
import os

import httpx
import pytest

from factory import packs, packstore
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, TOKEN_HEADER, USER_HEADER, start_executor, stop_process

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"
PACK = "ozone_recon"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "simple": {**BASE, "name": "Recon", "auth_mode": "none", "secret_ref": ""},
    "knox": {**BASE, "name": "Recon via Knox", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_RECON"},
    "knox_jwt": {**BASE, "name": "Recon via Knox JWT", "auth_mode": "forward-token", "secret_ref": ""},
}
KNOX = {"prefix": "/gateway/cdp-proxy/ozone-recon/api/v1"}
OLD = {"prefix": "/recon-1/api/v1", "simple_user": "caller"}
GB = 1024 ** 3


def recon_tool(name, function, connection="simple", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Recon", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_RECON"] = "auditor:auditor-secret"
    tools = [recon_tool(f, f) for f in FUNCTIONS]
    tools += [recon_tool("knox_volumes", "list_volumes", "knox", KNOX), recon_tool("jwt_cluster", "cluster_state", "knox_jwt", KNOX)]
    tools += [recon_tool(f"old_{f}", f, "simple", OLD) for f in ("describe_path", "list_keys", "storage_distribution", "deleted_directories_summary", "list_volumes")]
    tools += [recon_tool("old_anonymous", "list_volumes", "simple", {"prefix": "/recon-1/api/v1"}), recon_tool("old_fixed", "list_volumes", "simple", {"prefix": "/recon-1/api/v1", "simple_user": "recon-reader"})]
    tools += [recon_tool("tiny", "list_volumes", "simple", {"page_size": 2}), recon_tool("bad_prefix", "cluster_state", "simple", {"prefix": "/nowhere"})]
    bundle = compile_bundle(tools, CONNECTIONS, [MOCK], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)
        os.environ.pop("FACTORY_SECRET_RECON", None)


def call(executor, tool, caller="alice", token=None, **arguments):
    headers = {KEY_HEADER: executor.key, USER_HEADER: caller, **({TOKEN_HEADER: token} if token else {})}
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{tool}", headers=headers, json=arguments, timeout=30)
    return response.status_code, response.json()


def ok(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status == 200, payload
    return payload


def error(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


def names(items, key="name"):
    return [i[key] for i in items]


def test_the_seed_declares_thirteen_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 13
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_volumes_buckets_and_keys(executor):
    volumes = ok(executor, "list_volumes")
    assert names(volumes["volumes"]) == ["finance", "s3v", "sales"] and volumes["total"] == 3 and volumes["count"] == 3 and not volumes["truncated"]
    finance = volumes["volumes"][0]
    assert finance == {"name": "finance", "owner": "bob", "admin": "hadoop", "quota_bytes": 10 * GB, "quota_namespace": 1000, "used_namespace": 1, "created": "2026-02-25T06:13:20Z", "modified": "2026-02-25T06:13:20Z", "acls": ["USER bob: ALL"]}
    assert volumes["volumes"][2]["acls"] == ["USER alice: ALL", "GROUP analysts: READ, LIST"] and "quota_bytes" not in volumes["volumes"][2]
    first = ok(executor, "tiny", limit=50)
    assert names(first["volumes"]) == ["finance", "s3v"] and first["truncated"] and first["next_start_after"] == "s3v"
    rest = ok(executor, "tiny", start_after="s3v")
    assert names(rest["volumes"]) == ["sales"] and not rest["truncated"] and "next_start_after" not in rest

    buckets = ok(executor, "list_buckets")
    assert [(b["volume"], b["name"]) for b in buckets["buckets"]] == [("finance", "ledger"), ("s3v", "landing"), ("sales", "archive"), ("sales", "orders")] and buckets["total"] == 4
    archive = ok(executor, "list_buckets", volume="sales")["buckets"][0]
    assert archive["layout"] == "FILE_SYSTEM_OPTIMIZED" and archive["storage_type"] == "ARCHIVE" and archive["versioning"] is True and archive["replication"] == "EC RS-6-3-1024k"
    assert archive["used_bytes"] == 1610612736 and archive["used_namespace"] == 1 and archive["owner"] == "alice" and "quota_bytes" not in archive
    ledger = ok(executor, "list_buckets", volume="finance")["buckets"][0]
    assert ledger["quota_bytes"] == 5 * GB and ledger["quota_namespace"] == 500 and ledger["used_bytes"] == 3145728 and ledger["versioning"] is False
    assert ok(executor, "list_buckets", volume="nope") == {"buckets": [], "count": 0, "total": 0, "truncated": False}
    assert "without slashes" in error(executor, "list_buckets", volume="a/b")

    keys = ok(executor, "list_keys", prefix="/sales/orders")
    assert names(keys["keys"], "path") == ["/sales/orders/2026/01/orders.parquet", "/sales/orders/2026/02/orders.parquet", "/sales/orders/README.md"]
    assert keys["count"] == 3 and keys["total_bytes"] == 114296832 and keys["total_replicated_bytes"] == 342890496 and not keys["truncated"] and "last_key" not in keys
    readme = keys["keys"][2]
    assert readme == {"path": "/sales/orders/README.md", "size_bytes": 2048, "replicated_bytes": 6144, "replication": "RATIS/THREE", "created": "2026-05-28T20:26:40Z", "modified": "2026-05-28T20:26:40Z"}
    assert names(ok(executor, "list_keys", prefix="/sales/archive")["keys"], "path") == ["/sales/archive/2019.tar"] and ok(executor, "list_keys", prefix="/sales/archive")["keys"][0]["replication"] == "EC RS-6-3-1024k"
    assert names(ok(executor, "list_keys", prefix="/sales/orders", min_size_bytes=50 * 1024 * 1024)["keys"], "path") == ["/sales/orders/2026/01/orders.parquet", "/sales/orders/2026/02/orders.parquet"]
    assert names(ok(executor, "list_keys", prefix="/sales/orders", created_after="10-01-2026 00:00:00")["keys"], "path") == ["/sales/orders/2026/02/orders.parquet"]
    assert names(ok(executor, "list_keys", prefix="/sales/orders", replication_type="ec")["keys"], "path") == []
    paged = ok(executor, "list_keys", prefix="/sales/orders", limit=2)
    assert paged["count"] == 2 and paged["truncated"] and paged["last_key"] == "/sales/orders/2026/02/orders.parquet"
    assert names(ok(executor, "list_keys", prefix="/sales/orders", limit=2, start_after=paged["last_key"])["keys"], "path") == ["/sales/orders/README.md"]
    assert ok(executor, "list_keys", prefix="/sales/orders/nothing") == {"prefix": "/sales/orders/nothing", "keys": [], "count": 0, "truncated": False, "total_bytes": 0, "total_replicated_bytes": 0}
    assert "at least a volume and a bucket" in error(executor, "list_keys", prefix="/sales")
    assert "RATIS or EC" in error(executor, "list_keys", prefix="/sales/orders", replication_type="three")
    assert "MM-dd-yyyy" in error(executor, "list_keys", prefix="/sales/orders", created_after="2026-10-01")
    assert "must be absolute" in error(executor, "list_keys", prefix="sales/orders")


@gateway
def test_namespace_views(executor):
    root = ok(executor, "describe_path", path="/")
    assert root == {"path": "/", "type": "root", "counts": {"volumes": 3, "buckets": 4, "directories": 3, "keys": 6}}
    sales = ok(executor, "describe_path", path="/sales/")
    assert sales["path"] == "/sales" and sales["type"] == "volume" and sales["counts"] == {"buckets": 2, "directories": 3, "keys": 4} and sales["owner"] == "alice" and sales["acls"] == ["USER alice: ALL", "GROUP analysts: READ, LIST"]
    orders = ok(executor, "describe_path", path="/sales/orders")
    assert orders["type"] == "bucket" and orders["layout"] == "FILE_SYSTEM_OPTIMIZED" and orders["counts"] == {"directories": 3, "keys": 3} and orders["used_namespace"] == 6
    directory = ok(executor, "describe_path", path="/sales/orders/2026")
    assert directory["type"] == "directory" and directory["name"] == "2026" and directory["counts"] == {"directories": 2, "keys": 2} and directory["modified"] == "2026-10-26T07:33:20Z"
    key = ok(executor, "describe_path", path="/sales/orders/README.md")
    assert key["type"] == "key" and key["size_bytes"] == 2048 and key["replication"] == "RATIS/THREE" and key["counts"] == {"keys": 0}
    finance = ok(executor, "describe_path", path="/finance")
    assert finance["quota_bytes"] == 10 * GB and finance["metadata"] == {"department": "finance"}
    assert "Nothing in Ozone at /nope" in error(executor, "describe_path", path="/nope")
    assert "must be absolute" in error(executor, "describe_path", path="sales")

    usage = ok(executor, "disk_usage", path="/")
    assert usage["size_bytes"] == 1728056196 and usage["size"] == "1.60938 GB" and usage["total_children"] == 3 and not usage["truncated"]
    assert [(c["path"], c["size_bytes"]) for c in usage["children"]] == [("/sales", 1724909568), ("/finance", 3145728), ("/s3v", 900)] and usage["children"][2]["size"] == "900 B"
    assert "replicated_bytes" not in usage and "is_key" not in usage["children"][0]
    bucket = ok(executor, "disk_usage", path="/sales/orders")
    assert names(bucket["children"], "path") == ["/sales/orders/2026"] and bucket["direct_keys_bytes"] == 2048 and bucket["size_bytes"] == 114296832
    with_files = ok(executor, "disk_usage", path="/sales/orders", include_files=True, with_replication=True)
    assert [(c["path"], c.get("is_key")) for c in with_files["children"]] == [("/sales/orders/2026", None), ("/sales/orders/README.md", True)]
    assert with_files["replicated_bytes"] == 342890496 and with_files["children"][1]["replicated_bytes"] == 6144
    assert ok(executor, "disk_usage", path="/sales/orders/README.md")["children"] == [] and ok(executor, "disk_usage", path="/sales/orders/README.md")["size_bytes"] == 2048
    paged = ok(executor, "disk_usage", path="/", limit=2)
    assert names(paged["children"], "path") == ["/sales", "/finance"] and paged["truncated"] and paged["count"] == 2
    assert names(ok(executor, "disk_usage", path="/", limit=2, offset=2)["children"], "path") == ["/s3v"]
    assert "Nothing in Ozone" in error(executor, "disk_usage", path="/sales/nothing")

    assert ok(executor, "quota_usage", path="/finance") == {"path": "/finance", "quota_bytes": 10 * GB, "quota": "10 GB", "used_bytes": 3145728, "used": "3 MB", "percent_used": 0.0}
    assert ok(executor, "quota_usage", path="/finance/ledger")["quota"] == "5 GB" and ok(executor, "quota_usage", path="/finance/ledger")["percent_used"] == 0.1
    assert ok(executor, "quota_usage", path="/sales") == {"path": "/sales", "quota": "unlimited", "used_bytes": 1724909568, "used": "1.60645 GB"}
    assert ok(executor, "quota_usage", path="/")["quota_bytes"] == 10 * GB
    assert "Only volumes and buckets" in ok(executor, "quota_usage", path="/sales/orders/2026")["note"]
    assert "Nothing in Ozone" in error(executor, "quota_usage", path="/nope")

    dist = ok(executor, "file_size_distribution", path="/sales")
    assert dist == {"path": "/sales", "total_files": 4, "bins": [{"up_to": "2 KB", "upper_bound_bytes": 2048, "count": 1}, {"up_to": "64 MB", "upper_bound_bytes": 67108864, "count": 2}, {"up_to": "2 GB", "upper_bound_bytes": 2147483648, "count": 1}]}
    assert ok(executor, "file_size_distribution", path="/s3v")["bins"] == [{"up_to": "1 KB", "upper_bound_bytes": 1024, "count": 1}]
    assert "not to a single key" in ok(executor, "file_size_distribution", path="/finance/ledger/gl.csv")["note"]


@gateway
def test_cluster_views_and_summaries(executor):
    state = ok(executor, "cluster_state")
    assert state["datanodes"] == {"total": 3, "healthy": 3} and state["pipelines"] == 4 and state["containers"] == {"total": 120, "open": 8, "missing": 0, "deleted": 2}
    assert state["namespace"] == {"volumes": 3, "buckets": 4, "keys": 6, "keys_pending_deletion": 2, "directories_pending_deletion": 1} and state["om_service_id"] == "om1" and state["scm_service_id"] == "scm1"
    assert state["storage"]["capacity"] == "3 TB" and state["storage"]["used_bytes"] == 5184168588 and state["storage"]["filesystem_available_bytes"] == 3300000000000
    assert "missing" in state["containers"]  # a zero count is still worth saying
    storage = ok(executor, "storage_distribution")
    assert storage["global"]["capacity"] == "3 TB" and storage["global"]["free_bytes"] == 3200000000000 and storage["namespace"] == {"used_bytes": 1728056196, "keys": 6}
    assert storage["used_space"] == {"finalized_key_bytes": 1728056196, "open_key_bytes": 31457280, "open_key_and_file_bytes": 31457280, "multipart_open_bytes": 0} and len(storage["datanodes"]) == 3
    assert storage["datanodes"][0] == {"host": "dn1.example.com", "uuid": "dn-1", "capacity_bytes": 1099511627776, "used_bytes": 1728056196, "used": "1.60938 GB", "remaining_bytes": 1066666666666, "committed_bytes": 2863311530}
    counts = ok(executor, "file_counts")
    assert [(r["volume"], r["bucket"], r["up_to"], r["count"]) for r in counts["rows"]] == [("finance", "ledger", "4 MB", 1), ("s3v", "landing", "1 KB", 1), ("sales", "archive", "2 GB", 1), ("sales", "orders", "2 KB", 1), ("sales", "orders", "64 MB", 2)]
    assert counts["total_files"] == 6 and counts["count"] == 5 and not counts["truncated"]
    assert len(ok(executor, "file_counts", volume="sales")["rows"]) == 3 and ok(executor, "file_counts", volume="sales", bucket="orders")["total_files"] == 3
    assert ok(executor, "file_counts", volume="sales", limit=2, offset=2)["rows"] == [{"volume": "sales", "bucket": "orders", "up_to": "64 MB", "upper_bound_bytes": 67108864, "count": 2}]
    assert "Name the volume" in error(executor, "file_counts", bucket="orders")
    assert ok(executor, "open_keys_summary") == {"open_keys": 3, "data_bytes": 31457280, "data": "30 MB", "replicated_bytes": 94371840}
    assert ok(executor, "pending_deletion_summary") == {"keys_pending_deletion": 2, "data_bytes": 2097152, "data": "2 MB", "replicated_bytes": 6291456}
    assert ok(executor, "deleted_directories_summary") == {"directories_pending_deletion": 1}
    assert "check the prefix" in error(executor, "bad_prefix")


@gateway
def test_authentication_variants_and_an_older_recon(executor):
    assert ok(executor, "knox_volumes")["total"] == 3  # Basic through Knox
    assert "credentials" in error(executor, "jwt_cluster")  # forward-token without a token
    assert ok(executor, "jwt_cluster", caller="bob", token=jwt_for("bob"))["pipelines"] == 4
    assert "simple_user" in error(executor, "old_anonymous")  # this Recon refuses anonymous simple callers
    assert ok(executor, "old_fixed")["total"] == 3  # a fixed user.name
    assert ok(executor, "old_list_volumes", caller="carol")["total"] == 3  # the caller's name
    old = ok(executor, "old_describe_path", path="/sales/orders")
    assert old == {"path": "/sales/orders", "type": "bucket", "counts": {"directories": 3, "keys": 3}}  # the flat shape has no object details
    assert "does not offer key listing" in error(executor, "old_list_keys", prefix="/sales/orders")
    assert "does not offer the storage distribution" in error(executor, "old_storage_distribution")
    assert "does not offer the deleted directory summary" in error(executor, "old_deleted_directories_summary")


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry):
    client, _, _ = registry
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Recon", "base_url": MOCK, "protocol": "rest", "auth_mode": "none", "secret_ref": ""}).json()
    tool = client.post("/api/tools", json={"name": "ozone_usage", "description": "How much data sits under a path.", "kind": "python", "pack": PACK, "function": "disk_usage", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Recon answered: 3 volumes, 4 buckets, 6 keys on 3 datanodes (3 healthy)"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"path": "/sales"}}}).json()
    assert result["success"], result
    assert [c["path"] for c in result["result"]["structuredContent"]["children"]] == ["/sales/archive", "/sales/orders"]
