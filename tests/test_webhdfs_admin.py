"""The webhdfs_admin seed pack against the in-memory WebHDFS fake, through the executor."""
import base64
import os

import httpx
import pytest

from factory import packs, packstore
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, USER_HEADER, start_executor, stop_process

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
CONNECTION = {"name": "HDFS", "base_url": "http://mock-api:8080", "protocol": "webhdfs", "auth_mode": "none", "secret_ref": "", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
PACK = "webhdfs_admin"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
WRITES = {t["function"] for t in INFO["tools"] if t["effect"] == "write"}
NAMENODE = {"prefix": "/webhdfs-nn/v1", "follow_redirects": True, "pseudo_auth": True}


def seed_tool(name, function, config=None):
    spec = ToolSpec(name=name, description=f"{function} on HDFS", kind="python", pack=PACK, function=function, connection_id="c",
        effect="write" if function in WRITES else "read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    functions = [t["function"] for t in INFO["tools"]]
    tools = [seed_tool(f, f) for f in functions] + [seed_tool(f"nn_{f}", f, NAMENODE) for f in ("append", "check_access", "get_home_directory")] + [seed_tool("strict_append", "append", {"prefix": "/webhdfs-nn/v1"})]
    bundle = compile_bundle(tools, {"c": CONNECTION}, [CONNECTION["base_url"]], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    assert bundle["pack_sources"] == {PACK: SOURCE}
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)


def call(executor, tool, user="alice", **arguments):
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{tool}", headers={KEY_HEADER: executor.key, USER_HEADER: user}, json=arguments, timeout=30)
    return response.status_code, response.json()


def ok(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status == 200, payload
    return payload


def error(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


def webhdfs(method, path, op, **params):
    """Drive the fake directly for setup the pack deliberately has no tool for (allowing snapshots, creating files)."""
    response = httpx.request(method, f"http://mock-api:8080/webhdfs/v1{path}", params={"op": op, **params}, content=params.pop("content", None), timeout=10)
    assert response.status_code < 400, response.text
    return response


def test_the_seed_declares_twenty_six_tools():
    assert INFO["error"] is None and INFO["protocol"] == "webhdfs" and len(INFO["tools"]) == 26
    assert INFO["probe"]["function"] == "probe"
    assert WRITES == {"set_permission", "set_owner", "set_replication", "set_times", "set_xattr", "remove_xattr", "create_snapshot", "rename_snapshot", "delete_snapshot", "append", "concat"}


@gateway
def test_space_listing_and_locations(executor):
    webhdfs("DELETE", "/admin", "DELETE", recursive="true")
    for name, body in (("a.txt", b"alpha\n"), ("b.txt", b"bravo\n"), ("c.txt", b"charlie\n")):
        webhdfs("PUT", f"/admin/files/{name}", "CREATE", data="true", content=body)
    summary = ok(executor, "get_content_summary", path="/admin")
    assert summary["files"] == 3 and summary["directories"] == 2 and summary["bytes"] == 20
    quota = ok(executor, "get_quota_usage", path="/admin")
    assert quota["files_and_directories"] == 5 and quota["space_consumed"] == 20 and quota["quota"] == -1
    fs = ok(executor, "get_filesystem_status")
    assert fs["used"] >= 20 and fs["capacity"] == fs["used"] + fs["remaining"]
    assert ok(executor, "get_checksum", path="/admin/files/a.txt")["algorithm"].startswith("MD5")
    page = ok(executor, "list_directory_page", path="/admin/files")
    assert [e["name"] for e in page["entries"]] == ["a.txt", "b.txt"] and page["remaining"] == 1 and page["next_start_after"] == "b.txt"
    page = ok(executor, "list_directory_page", path="/admin/files", start_after=page["next_start_after"])
    assert [e["name"] for e in page["entries"]] == ["c.txt"] and page["remaining"] == 0 and page["next_start_after"] is None
    assert ok(executor, "get_home_directory") == {"path": "/user/anonymous", "user": "alice"}  # no pseudo auth: the endpoint does not know who asks
    assert ok(executor, "nn_get_home_directory", user="bob") == {"path": "/user/bob", "user": "bob"}
    assert ok(executor, "get_trash_root", path="/admin/files")["trash"].endswith("/.Trash")
    assert "FileNotFoundException" in error(executor, "get_quota_usage", path="/admin/missing")
    assert "absolute" in error(executor, "get_content_summary", path="../etc")


@gateway
def test_permissions_acls_access_and_storage(executor):
    webhdfs("DELETE", "/admin", "DELETE", recursive="true")
    webhdfs("PUT", "/admin/secret.txt", "CREATE", data="true", content=b"shh", **{"user.name": "alice"})
    assert ok(executor, "set_permission", path="/admin/secret.txt", permission="600") == {"path": "/admin/secret.txt", "permission": "600"}
    assert "octal" in error(executor, "set_permission", path="/admin/secret.txt", permission="rwx")
    acl = ok(executor, "get_acl_status", path="/admin/secret.txt")
    assert acl["permission"] == "600" and acl["owner"] == "alice" and acl["entries"] == [] and acl["sticky_bit"] is False
    assert ok(executor, "set_owner", path="/admin/secret.txt", owner="alice", group="finance")["group"] == "finance"
    assert "Give an owner" in error(executor, "set_owner", path="/admin/secret.txt")
    assert "not a valid" in error(executor, "set_owner", path="/admin/secret.txt", owner="a b")
    assert ok(executor, "get_acl_status", path="/admin/secret.txt")["owner"] == "alice"
    assert ok(executor, "nn_check_access", path="/admin/secret.txt", action="rw-") == {"path": "/admin/secret.txt", "action": "rw-", "allowed": True}
    denied = ok(executor, "nn_check_access", user="bob", path="/admin/secret.txt", action="r--")
    assert denied["allowed"] is False and "AccessControlException" in denied["reason"]
    assert "three characters" in error(executor, "check_access", path="/admin/secret.txt", action="read")
    assert ok(executor, "set_replication", path="/admin/secret.txt", replication=3)["changed"]
    assert "between 1 and 10" in error(executor, "set_replication", path="/admin/secret.txt", replication=0)
    policy = ok(executor, "get_storage_policy", path="/admin/secret.txt")
    assert policy["name"] == "HOT" and policy["storage_types"] == ["DISK"]
    times = ok(executor, "set_times", path="/admin/secret.txt", modified="2026-01-31T09:00:00Z")
    assert times == {"path": "/admin/secret.txt", "modified": "2026-01-31T09:00:00+00:00", "accessed": None}
    assert ok(executor, "set_times", path="/admin/secret.txt", accessed="1700000000000")["accessed"] == "2023-11-14T22:13:20+00:00"
    assert "Give a modification time" in error(executor, "set_times", path="/admin/secret.txt")
    assert "ISO 8601" in error(executor, "set_times", path="/admin/secret.txt", modified="yesterday")
    status = webhdfs("GET", "/admin/secret.txt", "GETFILESTATUS").json()["FileStatus"]
    assert status["modificationTime"] == 1769850000000 and status["accessTime"] == 1700000000000


@gateway
def test_extended_attributes(executor):
    webhdfs("DELETE", "/admin", "DELETE", recursive="true")
    webhdfs("PUT", "/admin/tagged.csv", "CREATE", data="true", content=b"a,b\n")
    assert ok(executor, "list_xattrs", path="/admin/tagged.csv") == {"path": "/admin/tagged.csv", "names": []}
    assert ok(executor, "set_xattr", path="/admin/tagged.csv", name="user.owner_team", value="finance")["replaced"] is False
    assert ok(executor, "set_xattr", path="/admin/tagged.csv", name="user.retention", value="7 years, café ☕")["value"] == "7 years, café ☕"
    assert "already exists" in error(executor, "set_xattr", path="/admin/tagged.csv", name="user.owner_team", value="sales")
    assert ok(executor, "set_xattr", path="/admin/tagged.csv", name="user.owner_team", value="sales", replace=True)["replaced"]
    assert "does not exist" in error(executor, "set_xattr", path="/admin/tagged.csv", name="user.nope", value="x", replace=True)
    assert "namespace" in error(executor, "set_xattr", path="/admin/tagged.csv", name="owner_team", value="x")
    assert ok(executor, "list_xattrs", path="/admin/tagged.csv")["names"] == ["user.owner_team", "user.retention"]
    both = ok(executor, "get_xattrs", path="/admin/tagged.csv")["attributes"]
    assert both == [{"name": "user.owner_team", "value": "sales", "encoding": "utf-8"}, {"name": "user.retention", "value": "7 years, café ☕", "encoding": "utf-8"}]
    one = ok(executor, "get_xattrs", path="/admin/tagged.csv", names="user.retention")["attributes"]
    assert [a["name"] for a in one] == ["user.retention"]
    assert "not found" in error(executor, "get_xattrs", path="/admin/tagged.csv", names="user.missing")
    webhdfs("PUT", "/admin/tagged.csv", "SETXATTR", **{"xattr.name": "user.blob", "xattr.value": "0x00ff", "flag": "CREATE"})
    blob = ok(executor, "get_xattrs", path="/admin/tagged.csv", names="user.blob")["attributes"][0]
    assert blob["encoding"] == "base64" and base64.b64decode(blob["value"]) == b"\x00\xff"
    assert ok(executor, "remove_xattr", path="/admin/tagged.csv", name="user.blob")["removed"]
    assert "No matching" in error(executor, "remove_xattr", path="/admin/tagged.csv", name="user.blob")
    assert ok(executor, "list_xattrs", path="/admin/tagged.csv")["names"] == ["user.owner_team", "user.retention"]


@gateway
def test_snapshots(executor):
    webhdfs("DELETE", "/admin", "DELETE", recursive="true")
    webhdfs("PUT", "/admin/snap/one.txt", "CREATE", data="true", content=b"1")
    assert "not a snapshottable" in error(executor, "create_snapshot", path="/admin/snap", name="s1")
    webhdfs("PUT", "/admin/snap", "ALLOWSNAPSHOT")  # an administrator's job, deliberately not a tool
    listed = ok(executor, "list_snapshottable_directories")["directories"]
    mine = next(d for d in listed if d["path"] == "/admin/snap")
    assert mine["snapshots"] == 0 and mine["type"] == "directory"
    first = ok(executor, "create_snapshot", path="/admin/snap", name="s1")
    assert first == {"path": "/admin/snap", "name": "s1", "snapshot_path": "/admin/snap/.snapshot/s1"}
    assert "already" in error(executor, "create_snapshot", path="/admin/snap", name="s1")
    assert "without slashes" in error(executor, "create_snapshot", path="/admin/snap", name="a/b")
    webhdfs("PUT", "/admin/snap/two.txt", "CREATE", data="true", content=b"2")
    webhdfs("PUT", "/admin/snap/one.txt", "CREATE", data="true", overwrite="true", content=b"one")
    auto = ok(executor, "create_snapshot", path="/admin/snap")
    assert auto["name"].startswith("s") and auto["snapshot_path"].endswith(auto["name"])
    diff = ok(executor, "get_snapshot_diff", path="/admin/snap", from_snapshot="s1", to_snapshot=auto["name"])
    assert diff["changes"] == [{"type": "create", "path": "/two.txt"}, {"type": "modify", "path": "/one.txt"}]
    webhdfs("DELETE", "/admin/snap/two.txt", "DELETE")
    current = ok(executor, "get_snapshot_diff", path="/admin/snap", from_snapshot=auto["name"])
    assert current["to_snapshot"] == "." and current["changes"] == [{"type": "delete", "path": "/two.txt"}]
    assert "Cannot find" in error(executor, "get_snapshot_diff", path="/admin/snap", from_snapshot="nope")
    assert ok(executor, "rename_snapshot", path="/admin/snap", name=auto["name"], new_name="s2") == {"path": "/admin/snap", "name": "s2", "previous_name": auto["name"]}
    snapshots = ok(executor, "list_snapshots", path="/admin/snap")["snapshots"]
    assert [s["name"] for s in snapshots] == ["s1", "s2"] and snapshots[0]["path"] == "/admin/snap/.snapshot/s1" and snapshots[0]["status"] == "active"
    assert next(d for d in ok(executor, "list_snapshottable_directories")["directories"] if d["path"] == "/admin/snap")["snapshots"] == 2
    assert ok(executor, "delete_snapshot", path="/admin/snap", name="s1")["deleted"]
    assert "Cannot find" in error(executor, "delete_snapshot", path="/admin/snap", name="s1")
    assert [s["name"] for s in ok(executor, "list_snapshots", path="/admin/snap")["snapshots"]] == ["s2"]
    assert "Not a directory" in error(executor, "list_snapshots", path="/admin/snap/one.txt")


@gateway
def test_append_and_concat(executor):
    webhdfs("DELETE", "/admin", "DELETE", recursive="true")
    webhdfs("PUT", "/admin/log.txt", "CREATE", data="true", content=b"line 1\n")
    assert ok(executor, "append", path="/admin/log.txt", content="line 2\n") == {"path": "/admin/log.txt", "appended": 7}
    assert ok(executor, "append", path="/admin/log.txt", content=base64.b64encode(b"\x00\x01").decode(), encoding="base64")["appended"] == 2
    assert "base64" in error(executor, "append", path="/admin/log.txt", content="not base64!", encoding="base64")
    assert "utf-8 or base64" in error(executor, "append", path="/admin/log.txt", content="x", encoding="latin-1")
    assert "FileNotFoundException" in error(executor, "append", path="/admin/missing.txt", content="x")
    assert webhdfs("GET", "/admin/log.txt", "OPEN").content == b"line 1\nline 2\n\x00\x01"
    assert "redirected" in error(executor, "strict_append", path="/admin/log.txt", content="x")
    assert ok(executor, "nn_append", path="/admin/log.txt", content="via redirect\n")["appended"] == 13
    assert webhdfs("GET", "/admin/log.txt", "OPEN").content.endswith(b"via redirect\n")
    for name in ("p1", "p2", "p3"):
        webhdfs("PUT", f"/admin/parts/{name}", "CREATE", data="true", content=name.encode())
    joined = ok(executor, "concat", target="/admin/parts/p1", sources="/admin/parts/p2, /admin/parts/p3")
    assert joined == {"target": "/admin/parts/p1", "sources": ["/admin/parts/p2", "/admin/parts/p3"], "concatenated": 2}
    assert webhdfs("GET", "/admin/parts/p1", "OPEN").content == b"p1p2p3"
    assert webhdfs("GET", "/admin/parts", "LISTSTATUS").json()["FileStatuses"]["FileStatus"][0]["pathSuffix"] == "p1"
    assert len(webhdfs("GET", "/admin/parts", "LISTSTATUS").json()["FileStatuses"]["FileStatus"]) == 1
    assert "at least one source" in error(executor, "concat", target="/admin/parts/p1", sources="")
    assert "same directory" in error(executor, "concat", target="/admin/parts/p1", sources="/admin/log.txt")
