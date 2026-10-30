"""Two unrelated, deterministic development fixtures. No customer data."""
import threading

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

# An upstream MCP server built on the Python SDK: earlier protocol profile with initialize and
# session ids, so tests exercise Daedalus's fallback. Served at /upstream/mcp.
upstream = FastMCP("fixture-upstream", stateless_http=False, transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))


@upstream.tool(annotations=ToolAnnotations(readOnlyHint=True))
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@upstream.tool(annotations=ToolAnnotations(readOnlyHint=True))
def lookup_ticket(ticket_id: str) -> dict:
    """Look up a support ticket by its identifier."""
    if ticket_id == "missing":
        raise ValueError("Ticket not found")
    return {"id": ticket_id, "title": "Replace workstation", "status": "open"}


@upstream.tool()
def file_ticket(title: str, priority: str = "normal") -> dict:
    """File a new support ticket."""
    return {"id": "T-900", "title": title, "priority": priority}


upstream_app = upstream.streamable_http_app()


@asynccontextmanager
async def lifespan(_):
    async with upstream.session_manager.run():
        yield

app = FastAPI(title="Daedalus fixtures", lifespan=lifespan)
app.mount("/upstream", upstream_app)
counter_lock = threading.Lock()
calls = {"inventory": 0, "tickets": 0}
tickets = []


class Ticket(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/inventory/items/{item_id}")
def inventory(item_id: str, warehouse: str = "central"):
    with counter_lock:
        calls["inventory"] += 1
    if item_id == "missing":
        raise HTTPException(404, "Item not found")
    return {"id": item_id, "name": "Precision bearing", "quantity": 42, "warehouse": warehouse}


@app.get("/tickets/{ticket_id}")
def ticket(ticket_id: str):
    with counter_lock:
        calls["tickets"] += 1
    return {"id": ticket_id, "title": "Replace workstation", "status": "open"}


@app.post("/tickets")
def create_ticket(body: Ticket):
    with counter_lock:
        calls["tickets"] += 1
        result = {"id": f"T-{len(tickets) + 1}", "title": body.title, "status": "open"}
        tickets.append(result)
    return result


@app.get("/fixture/echo")
def echo(request: Request):
    """What the backend received: lets tests confirm which credential a connection sent."""
    return {"authorization": request.headers.get("authorization"), "query": dict(request.query_params)}


@app.post("/ratelimited/mcp")
def rate_limited():
    """An MCP endpoint behind a rate-limiting proxy: a plain HTTP error, not a JSON-RPC reply."""
    return JSONResponse({"title": "Error 1015: You are being rate limited", "status": 429, "detail": "Wait and retry."}, status_code=429, headers={"Retry-After": "30"})


@app.get("/fixture/counters")
def counters():
    return dict(calls)


# ---- WebHDFS fake -------------------------------------------------------------
# In-memory HDFS for tests and the playground. /webhdfs/v1 behaves like HttpFS (data
# flows directly); /webhdfs-nn/v1 behaves like a NameNode (OPEN and CREATE answer with a
# 307 redirect to the HttpFS path, as a real NameNode redirects to a DataNode).
import base64
import hashlib
import json
import time
from fastapi import Response
from fastapi.responses import JSONResponse

fs_lock = threading.Lock()


def fs_entry(kind, content=b"", owner="hdfs"):
    return {"type": kind, "content": content, "owner": owner, "mtime": int(time.time() * 1000)}


fs = {"/": fs_entry("DIRECTORY"), "/data": fs_entry("DIRECTORY"), "/data/readme.txt": fs_entry("FILE", b"Hello from the HDFS fixture.\n")}
snapshottable = {"/data"}  # directories on which snapshots may be taken (hdfs dfsadmin -allowSnapshot)
snapshots = {}  # (directory, name) -> {path: entry} copy of the subtree when the snapshot was taken


def fs_status(entry, suffix):
    directory = entry["type"] == "DIRECTORY"
    return {"pathSuffix": suffix, "type": entry["type"], "length": 0 if directory else len(entry["content"]), "modificationTime": entry["mtime"], "accessTime": entry.get("atime", entry["mtime"]),
        "owner": entry["owner"], "group": entry.get("group", "supergroup"), "permission": entry.get("permission", "755" if directory else "644"),
        "replication": 0 if directory else entry.get("replication", 1), "blockSize": 0 if directory else 134217728}


def remote_exception(status, exception, message):
    return JSONResponse({"RemoteException": {"exception": exception, "javaClassName": f"org.apache.hadoop.fs.{exception}", "message": message}}, status_code=status)


def fs_children(path):
    prefix = path.rstrip("/") + "/"
    return sorted(p for p in fs if p.startswith(prefix) and p[len(prefix):] and "/" not in p[len(prefix):])


def fs_parent(path):
    return path.rsplit("/", 1)[0] or "/"


@app.api_route("/webhdfs/v1/{path:path}", methods=["GET", "PUT", "POST", "DELETE"])
async def webhdfs(path: str, request: Request):
    return await webhdfs_operation(path, request, redirects=False)


@app.api_route("/webhdfs-nn/v1/{path:path}", methods=["GET", "PUT", "POST", "DELETE"])
async def webhdfs_namenode(path: str, request: Request):
    return await webhdfs_operation(path, request, redirects=True)


async def webhdfs_operation(raw_path, request, redirects):
    query = request.query_params
    op = query.get("op", "").upper()
    user = query.get("user.name", "anonymous")
    path = "/" + raw_path.strip("/") if raw_path.strip("/") else "/"
    body = await request.body() if request.method in {"PUT", "POST"} else b""
    if redirects and op in {"OPEN", "CREATE", "APPEND"}:  # a NameNode always redirects data operations to a DataNode
        location = str(request.base_url).rstrip("/") + "/webhdfs/v1" + path + "?" + "&".join(f"{k}={v}" for k, v in {**dict(query), "data": "true"}.items())
        return Response(status_code=307, headers={"Location": location})
    with fs_lock:
        entry = fs.get(path)
        if op == "LISTSTATUS":
            if entry is None:
                return remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
            if entry["type"] == "FILE":
                return {"FileStatuses": {"FileStatus": [fs_status(entry, "")]}}
            return {"FileStatuses": {"FileStatus": [fs_status(fs[child], child.rsplit("/", 1)[1]) for child in fs_children(path)]}}
        if op == "GETFILESTATUS":
            if entry is None:
                return remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
            return {"FileStatus": fs_status(entry, "")}
        if op == "MKDIRS":
            if entry is not None and entry["type"] == "FILE":
                return remote_exception(403, "FileAlreadyExistsException", f"Path is a file: {path}")
            current = ""
            for part in path.strip("/").split("/") if path != "/" else []:
                current += "/" + part
                fs.setdefault(current, fs_entry("DIRECTORY", owner=user))
            return {"boolean": True}
        if op == "RENAME":
            destination = query.get("destination", "")
            if entry is None:
                return remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
            if destination in fs or fs.get(fs_parent(destination), {}).get("type") != "DIRECTORY":
                return {"boolean": False}
            for key in [p for p in fs if p == path or p.startswith(path.rstrip("/") + "/")]:
                fs[destination + key[len(path):]] = fs.pop(key)
            return {"boolean": True}
        if op == "DELETE":
            if entry is None:
                return {"boolean": False}
            if entry["type"] == "DIRECTORY" and fs_children(path) and query.get("recursive") != "true":
                return remote_exception(403, "PathIsNotEmptyDirectoryException", f"`{path} is non empty': Directory is not empty")
            for key in [p for p in fs if p == path or p.startswith(path.rstrip("/") + "/")]:
                del fs[key]
                snapshottable.discard(key)
                for snapshot in [k for k in snapshots if k[0] == key]:
                    del snapshots[snapshot]
            return {"boolean": True}
        if op == "OPEN":
            if entry is None or entry["type"] != "FILE":
                return remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
            offset = int(query.get("offset", 0))
            length = int(query["length"]) if query.get("length") else None
            data = entry["content"][offset:]
            return Response(content=data if length is None else data[:length], media_type="application/octet-stream")
        if op == "CREATE":
            if entry is not None and query.get("overwrite") != "true":
                return remote_exception(403, "FileAlreadyExistsException", f"{path} for client already exists")
            if fs.get(fs_parent(path), {}).get("type") != "DIRECTORY":
                current = ""
                for part in fs_parent(path).strip("/").split("/"):
                    current += "/" + part
                    fs.setdefault(current, fs_entry("DIRECTORY", owner=user))
            fs[path] = fs_entry("FILE", body, owner=user)
            return Response(status_code=201, headers={"Location": str(request.url)})
        if op in {"GETCONTENTSUMMARY", "GETFILECHECKSUM", "SETPERMISSION", "SETOWNER", "SETREPLICATION"} and entry is None:
            return remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
        if op == "GETCONTENTSUMMARY":
            keys = [p for p in fs if p == path or p.startswith(path.rstrip("/") + "/")]
            files = [k for k in keys if fs[k]["type"] == "FILE"]
            length = sum(len(fs[k]["content"]) for k in files)
            return {"ContentSummary": {"directoryCount": len(keys) - len(files), "fileCount": len(files), "length": length, "quota": -1, "spaceConsumed": length, "spaceQuota": -1}}
        if op == "GETFILECHECKSUM":
            if entry["type"] != "FILE":
                return remote_exception(400, "IllegalArgumentException", f"Path is not a file: {path}")
            return {"FileChecksum": {"algorithm": "MD5-of-0MD5-of-512CRC32C", "bytes": hashlib.md5(entry["content"]).hexdigest(), "length": 28}}
        if op == "SETPERMISSION":
            entry["permission"] = query.get("permission", "755")
            return Response(status_code=200)
        if op == "SETOWNER":
            if query.get("owner"):
                entry["owner"] = query["owner"]
            if query.get("group"):
                entry["group"] = query["group"]
            return Response(status_code=200)
        if op == "SETREPLICATION":
            entry["replication"] = int(query.get("replication", 1))
            return {"boolean": True}
        return webhdfs_extra(op, path, entry, query, body, user)


def fs_subtree(path):
    return {p: dict(e) for p, e in fs.items() if p == path or p.startswith(path.rstrip("/") + "/")}


def xattr_decode(value):
    """WebHDFS encodes xattr values as "text", 0x<hex> or 0s<base64>."""
    if value.startswith("0x"):
        return bytes.fromhex(value[2:])
    if value.startswith("0s"):
        return base64.b64decode(value[2:])
    return value.strip('"').encode()


def xattr_encode(value, encoding):
    return {"hex": "0x" + value.hex(), "base64": "0s" + base64.b64encode(value).decode()}.get(encoding, '"' + value.decode(errors="replace") + '"')


def webhdfs_extra(op, path, entry, query, body, user):
    """The operations the webhdfs_admin seed pack adds; called under fs_lock."""
    missing = remote_exception(404, "FileNotFoundException", f"File does not exist: {path}")
    if op == "GETHOMEDIRECTORY":
        return {"Path": f"/user/{user}"}
    if op == "GETTRASHROOT":
        return {"Path": f"/user/{user}/.Trash"}
    if op == "GETSTATUS":
        used = sum(len(e["content"]) for e in fs.values() if e["type"] == "FILE")
        return {"FsStatus": {"capacity": 10 ** 12, "used": used, "remaining": 10 ** 12 - used}}
    if op == "GETSNAPSHOTTABLEDIRECTORYLIST":
        return {"SnapshottableDirectoryList": [{"dirStatus": fs_status(fs[d], d.rsplit("/", 1)[1]), "parentFullPath": fs_parent(d),
            "snapshotNumber": len([k for k in snapshots if k[0] == d]), "snapshotQuota": 65536} for d in sorted(snapshottable) if d in fs]}
    if op == "CONCAT":
        sources = [s for s in query.get("sources", "").split(",") if s]
        if entry is None or entry["type"] != "FILE":
            return missing
        for source in sources:
            if fs.get(source, {}).get("type") != "FILE":
                return remote_exception(404, "FileNotFoundException", f"File does not exist: {source}")
            if fs_parent(source) != fs_parent(path):
                return remote_exception(403, "HadoopIllegalArgumentException", "Sources and target must be in the same directory")
        for source in sources:
            entry["content"] += fs.pop(source)["content"]
        return Response(status_code=200)
    if entry is None:
        return missing
    if op == "LISTSTATUS_BATCH":
        children = fs_children(path) if entry["type"] == "DIRECTORY" else [path]
        after = query.get("startAfter", "")
        if after:
            children = [c for c in children if c.rsplit("/", 1)[1] > after]
        page, rest = children[:2], children[2:]  # tiny pages so paging is exercised
        statuses = [fs_status(fs[c], c.rsplit("/", 1)[1] if c != path else "") for c in page]
        return {"DirectoryListing": {"partialListing": {"FileStatuses": {"FileStatus": statuses}}, "remainingEntries": len(rest)}}
    if op == "GETQUOTAUSAGE":
        keys = fs_subtree(path)
        length = sum(len(e["content"]) for e in keys.values() if e["type"] == "FILE")
        return {"QuotaUsage": {"fileAndDirectoryCount": len(keys), "quota": entry.get("quota", -1), "spaceConsumed": length, "spaceQuota": entry.get("space_quota", -1),
            "typeQuota": {}}}
    if op == "GETXATTRS":
        names = query.getlist("xattr.name") if hasattr(query, "getlist") else [n for n in [query.get("xattr.name")] if n]
        attrs = entry.setdefault("xattrs", {})
        for name in names:
            if name not in attrs:
                return remote_exception(403, "IOException", f"At least one of the attributes provided was not found: {name}")
        chosen = names or sorted(attrs)
        return {"XAttrs": [{"name": n, "value": xattr_encode(attrs[n], query.get("encoding", "text"))} for n in chosen]}
    if op == "LISTXATTRS":
        return {"XAttrNames": json.dumps(sorted(entry.get("xattrs", {})))}
    if op == "SETXATTR":
        name, flag = query.get("xattr.name", ""), query.get("flag", "CREATE")
        attrs = entry.setdefault("xattrs", {})
        if not name.split(".")[0] in {"user", "trusted", "security", "system", "raw"}:
            return remote_exception(400, "HadoopIllegalArgumentException", f"An XAttr name must be prefixed with user/trusted/security/system/raw: {name}")
        if flag == "CREATE" and name in attrs:
            return remote_exception(403, "IOException", f"XAttr: {name} already exists. The REPLACE flag must be specified.")
        if flag == "REPLACE" and name not in attrs:
            return remote_exception(403, "IOException", f"XAttr: {name} does not exist. The CREATE flag must be specified.")
        attrs[name] = xattr_decode(query.get("xattr.value", ""))
        return Response(status_code=200)
    if op == "REMOVEXATTR":
        name = query.get("xattr.name", "")
        if name not in entry.get("xattrs", {}):
            return remote_exception(403, "IOException", f"No matching attributes found for remove operation: {name}")
        del entry["xattrs"][name]
        return Response(status_code=200)
    if op == "GETACLSTATUS":
        return {"AclStatus": {"entries": entry.get("acl", []), "group": entry.get("group", "supergroup"), "owner": entry["owner"],
            "permission": entry.get("permission", "755" if entry["type"] == "DIRECTORY" else "644"), "stickyBit": False}}
    if op == "CHECKACCESS":
        wanted = query.get("fsaction", "---")
        bits = int(entry.get("permission", "755" if entry["type"] == "DIRECTORY" else "644")[-3:], 8)
        mine = bits >> 6 if entry["owner"] == user else bits & 7  # owner or "other"; the fake knows no groups
        allowed = "".join(c if mine & (4 >> i) else "-" for i, c in enumerate("rwx"))
        if any(w != "-" and a == "-" for w, a in zip(wanted, allowed)):
            return remote_exception(403, "AccessControlException", f"Permission denied: user={user}, access={wanted}, inode=\"{path}\":{entry['owner']}:supergroup")
        return Response(status_code=200)
    if op == "GETSTORAGEPOLICY":
        return {"BlockStoragePolicy": {"copyOnCreateFile": False, "creationFallbacks": [], "id": 7, "name": entry.get("storage_policy", "HOT"), "replicationFallbacks": ["ARCHIVE"], "storageTypes": ["DISK"]}}
    if op == "SETTIMES":
        mtime, atime = int(query.get("modificationtime", -1)), int(query.get("accesstime", -1))
        if mtime >= 0:
            entry["mtime"] = mtime
        if atime >= 0:
            entry["atime"] = atime
        return Response(status_code=200)
    if op == "APPEND":
        if entry["type"] != "FILE":
            return remote_exception(404, "FileNotFoundException", f"Path is not a file: {path}")
        entry["content"] += body
        return Response(status_code=200)
    if op in {"CREATESNAPSHOT", "RENAMESNAPSHOT", "DELETESNAPSHOT", "GETSNAPSHOTLIST", "GETSNAPSHOTDIFF", "ALLOWSNAPSHOT", "DISALLOWSNAPSHOT"}:
        if entry["type"] != "DIRECTORY":
            return remote_exception(403, "SnapshotException", f"Not a directory: {path}")
        if op == "ALLOWSNAPSHOT":
            snapshottable.add(path)
            return Response(status_code=200)
        if op == "DISALLOWSNAPSHOT":
            snapshottable.discard(path)
            return Response(status_code=200)
        if path not in snapshottable:
            return remote_exception(403, "SnapshotException", f"Directory is not a snapshottable directory: {path}")
        name, old = query.get("snapshotname", ""), query.get("oldsnapshotname", "")
        mine = {k[1]: v for k, v in snapshots.items() if k[0] == path}
        if op == "CREATESNAPSHOT":
            name = name or time.strftime("s%Y%m%d-%H%M%S.000")
            if name in mine:
                return remote_exception(403, "SnapshotException", f"Failed to add snapshot: there is already a snapshot with the same name \"{name}\".")
            snapshots[(path, name)] = fs_subtree(path)
            return {"Path": f"{path.rstrip('/')}/.snapshot/{name}"}
        if op == "GETSNAPSHOTLIST":
            return {"SnapshotList": [{"dirStatus": fs_status(fs[path], ""), "fullPath": f"{path.rstrip('/')}/.snapshot/{n}", "snapshotID": i, "snapshotStatus": "ACTIVE"}
                for i, n in enumerate(sorted(mine))]}
        if op == "GETSNAPSHOTDIFF" and name in {"", "."}:
            mine["."] = fs_subtree(path)  # "." compares against the current contents
            name = "."
        if name not in mine and op != "RENAMESNAPSHOT":
            return remote_exception(403, "SnapshotException", f"Cannot find snapshot {name} in {path}")
        if op == "DELETESNAPSHOT":
            del snapshots[(path, name)]
            return Response(status_code=200)
        if op == "RENAMESNAPSHOT":
            if old not in mine:
                return remote_exception(403, "SnapshotException", f"The snapshot {old} does not exist for directory {path}")
            if name in mine:
                return remote_exception(403, "SnapshotException", f"The snapshot {name} already exists for directory {path}")
            snapshots[(path, name)] = snapshots.pop((path, old))
            return Response(status_code=200)
        if op == "GETSNAPSHOTDIFF":
            if old not in mine:
                return remote_exception(403, "SnapshotException", f"Cannot find snapshot {old} in {path}")
            before, after = mine[old], mine[name]
            diffs = [{"sourcePath": p[len(path.rstrip("/")):] or "/", "targetPath": "", "type": "CREATE"} for p in after if p not in before]
            diffs += [{"sourcePath": p[len(path.rstrip("/")):] or "/", "targetPath": "", "type": "DELETE"} for p in before if p not in after]
            diffs += [{"sourcePath": p[len(path.rstrip("/")):] or "/", "targetPath": "", "type": "MODIFY"} for p in after if p in before and after[p].get("content") != before[p].get("content")]
            return {"SnapshotDiffReport": {"diffList": sorted(diffs, key=lambda d: (d["type"], d["sourcePath"])), "fromSnapshot": old, "snapshotRoot": path, "toSnapshot": name}}
    return remote_exception(400, "UnsupportedOperationException", f"Unsupported operation: {op}")


# ---- Apache Ranger fake ---------------------------------------------------------------
# The public v2 API's read side, served at the direct Ranger Admin path and at a Knox-style path,
# with Basic credentials (an Auditor service account and a limited user) or a Bearer JWT whose
# subject is the user. /ranger-1 serves the same data as a Ranger without roles and zones, so
# packs can show their version tolerance. Policies, roles and zones are small but mention users,
# groups and roles, so caller-scoped searches have something to narrow.
RANGER_ACCOUNTS = {"auditor": ("auditor-secret", "AUDITOR"), "alice": ("alice-secret", "USER"), "bob": ("bob-secret", "USER")}
RANGER_GROUPS = {"alice": ["analysts"], "bob": ["finance"], "carol": ["finance", "analysts"]}
RANGER_SERVICE_DEFS = [
    {"id": 1, "guid": "0d047247-bafe-4cf8-8e9b-d5d377284b2d", "name": "hdfs", "displayName": "HDFS", "implClass": "org.apache.ranger.services.hdfs.RangerServiceHdfs", "label": "HDFS Repository",
        "resources": [{"itemId": 1, "name": "path", "type": "path", "level": 10, "recursiveSupported": True, "excludesSupported": False, "label": "Resource Path"}],
        "accessTypes": [{"itemId": 1, "name": "read"}, {"itemId": 2, "name": "write"}, {"itemId": 3, "name": "execute"}]},
    {"id": 3, "guid": "3e1afb5a-184a-4e82-9d9c-87a5cacc243c", "name": "hive", "displayName": "Hadoop SQL", "implClass": "org.apache.ranger.services.hive.RangerServiceHive", "label": "Hive Server2",
        "resources": [{"itemId": 1, "name": "database", "type": "string", "level": 10, "recursiveSupported": False, "excludesSupported": True, "label": "Hive Database"},
            {"itemId": 2, "name": "table", "type": "string", "level": 20, "parent": "database", "label": "Hive Table"}, {"itemId": 3, "name": "column", "type": "string", "level": 30, "parent": "table", "label": "Hive Column"}],
        "accessTypes": [{"itemId": 1, "name": "select"}, {"itemId": 2, "name": "update"}, {"itemId": 3, "name": "create"}, {"itemId": 4, "name": "drop"}, {"itemId": 5, "name": "all"}]},
]
RANGER_SERVICES = [
    {"id": 1, "guid": "6b7f1e0a-1111-4f5e-9a1b-aaaaaaaaaaaa", "isEnabled": True, "createdBy": "Admin", "updatedBy": "Admin", "version": 4, "type": "hdfs", "name": "cm_hdfs", "displayName": "cm_hdfs", "description": "Cluster HDFS",
        "configs": {"username": "hdfs", "hadoop.security.authentication": "kerberos", "fs.default.name": "hdfs://nn.example.internal:8020"}, "policyVersion": 12, "tagVersion": 1},
    {"id": 2, "guid": "6b7f1e0a-2222-4f5e-9a1b-bbbbbbbbbbbb", "isEnabled": True, "createdBy": "Admin", "updatedBy": "Admin", "version": 7, "type": "hive", "name": "cm_hive", "displayName": "Hadoop SQL", "description": "Hive, Impala and Spark SQL",
        "configs": {"username": "hive", "jdbc.url": "jdbc:hive2://hs2.example.internal:10000"}, "policyVersion": 31, "tagVersion": 3},
]
RANGER_ROLES = [
    {"id": 1, "guid": "r-1", "isEnabled": True, "createdBy": "Admin", "name": "data_stewards", "description": "Curate shared datasets", "options": {},
        "users": [{"name": "alice", "isAdmin": False}, {"name": "carol", "isAdmin": True}], "groups": [{"name": "analysts", "isAdmin": False}], "roles": []},
    {"id": 2, "guid": "r-2", "isEnabled": True, "createdBy": "Admin", "name": "finance_admins", "description": "Own the finance databases", "options": {},
        "users": [{"name": "bob", "isAdmin": True}], "groups": [{"name": "finance", "isAdmin": False}], "roles": []},
]


def ranger_policy(id, service, name, resources, items, **extra):
    service_type = next(s["type"] for s in RANGER_SERVICES if s["name"] == service)
    return {"id": id, "guid": f"p-{id:04d}-{service}", "isEnabled": True, "version": 1, "service": service, "serviceType": service_type, "name": name, "policyType": extra.pop("policyType", 0),
        "policyPriority": 0, "description": extra.pop("description", ""), "isAuditEnabled": True, "resources": {k: {"values": v, "isExcludes": False, "isRecursive": k == "path"} for k, v in resources.items()},
        "policyItems": [{"accesses": [{"type": a, "isAllowed": True} for a in accesses], "users": users, "groups": groups, "roles": roles, "conditions": [], "delegateAdmin": False}
            for accesses, users, groups, roles in items], "denyPolicyItems": [], "allowExceptions": [], "denyExceptions": [], "dataMaskPolicyItems": [], "rowFilterPolicyItems": [],
        "zoneName": extra.pop("zoneName", ""), "isDenyAllElse": False, **extra}


RANGER_POLICIES = [
    ranger_policy(1, "cm_hdfs", "all - path", {"path": ["/*"]}, [(["read", "write", "execute"], ["hdfs"], ["hadoop"], [])], description="Default policy"),
    ranger_policy(2, "cm_hdfs", "shared datasets", {"path": ["/data/shared"]}, [(["read", "execute"], [], ["analysts"], []), (["read", "write", "execute"], [], [], ["data_stewards"])]),
    ranger_policy(3, "cm_hdfs", "alice home", {"path": ["/user/alice"]}, [(["read", "write", "execute"], ["alice"], [], [])]),
    ranger_policy(4, "cm_hive", "sales database", {"database": ["sales"], "table": ["*"], "column": ["*"]}, [(["select"], [], ["analysts"], []), (["all"], [], [], ["data_stewards"])]),
    ranger_policy(5, "cm_hive", "finance database", {"database": ["finance"], "table": ["*"], "column": ["*"]}, [(["all"], [], ["finance"], ["finance_admins"])], zoneName="finance-zone"),
    ranger_policy(6, "cm_hive", "mask salaries", {"database": ["finance"], "table": ["payroll"], "column": ["salary"]}, [], policyType=1, zoneName="finance-zone",
        dataMaskPolicyItems=[{"dataMaskInfo": {"dataMaskType": "MASK"}, "accesses": [{"type": "select", "isAllowed": True}], "users": [], "groups": ["analysts"], "roles": [], "conditions": []}]),
]
RANGER_ZONES = [
    {"id": 1, "guid": "z-1", "isEnabled": True, "createdBy": "Admin", "name": "finance-zone", "description": "Finance data, administered by finance", "version": 2,
        "services": {"cm_hive": {"resources": [{"database": ["finance"]}]}}, "tagServices": [], "adminUsers": ["bob"], "adminUserGroups": ["finance"], "auditUsers": ["auditor"], "auditUserGroups": []},
]
RANGER_TAGS = {"cm_hive": {"op": "add_or_update", "serviceName": "cm_hive", "tagVersion": 3, "tagUpdateTime": 1760000000000,
    "tagDefinitions": {"1": {"id": 1, "guid": "td-1", "name": "PII", "source": "Atlas", "attributeDefs": [{"name": "type", "type": "string"}]}},
    "tags": {"1": {"id": 1, "guid": "t-1", "type": "PII", "attributes": {"type": "salary"}}},
    "serviceResources": [{"id": 1, "guid": "sr-1", "serviceName": "cm_hive", "resourceElements": {"database": {"values": ["finance"]}, "table": {"values": ["payroll"]}, "column": {"values": ["salary"]}}}],
    "resourceToTagIds": {"1": [1]}}}


def ranger_user(request):
    """The authenticated user and role, or None. Basic against the accounts table; Bearer JWTs are trusted for their subject (Knox already verified them)."""
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "basic":
        try:
            user, _, password = base64.b64decode(value).decode().partition(":")
        except (ValueError, UnicodeDecodeError):
            return None
        account = RANGER_ACCOUNTS.get(user)
        return (user, account[1]) if account and account[0] == password else None
    if scheme.lower() == "bearer" and value.count(".") == 2:
        payload = value.split(".")[1]
        try:
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        except (ValueError, UnicodeDecodeError):
            return None
        subject = claims.get("sub")
        return (subject, RANGER_ACCOUNTS.get(subject, ("", "USER"))[1]) if subject else None
    return None


def ranger_error(status, message):
    return JSONResponse({"statusCode": 1, "msgDesc": message, "messageList": [{"name": "OPER_NOT_ALLOWED_FOR_ENTITY" if status == 403 else "DATA_NOT_FOUND", "rbKey": "", "message": message}]}, status_code=status)


def ranger_principals(user):
    """What a Ranger `user=` search filter matches: the user, their groups, the roles those reach, plus public."""
    groups = set(RANGER_GROUPS.get(user, [])) | {"public"}
    roles = {r["name"] for r in RANGER_ROLES if any(u["name"] == user for u in r["users"]) or groups & {g["name"] for g in r["groups"]}}
    return groups, roles


def ranger_items(policy):
    return policy["policyItems"] + policy["denyPolicyItems"] + policy["allowExceptions"] + policy["denyExceptions"] + policy["dataMaskPolicyItems"] + policy["rowFilterPolicyItems"]


def ranger_mentions(policy, user=None, group=None, role=None):
    items = ranger_items(policy)
    if user:
        groups, roles = ranger_principals(user)
        return any(user in i["users"] or groups & set(i["groups"]) or roles & set(i["roles"]) for i in items)
    if group:
        return any(group in i["groups"] for i in items)
    if role:
        return any(role in i["roles"] for i in items)
    return True


def ranger_search(policies, query):
    """The subset of Ranger's SearchFilter that the read tools use."""
    for key, value in query.items():
        if not value:
            continue
        if key == "serviceName":
            policies = [p for p in policies if p["service"] == value]
        elif key == "serviceType":
            policies = [p for p in policies if p["serviceType"] == value]
        elif key == "policyName":
            policies = [p for p in policies if p["name"] == value]
        elif key == "policyNamePartial":
            policies = [p for p in policies if value.lower() in p["name"].lower()]
        elif key == "policyId":
            policies = [p for p in policies if str(p["id"]) == value]
        elif key == "guid":
            policies = [p for p in policies if p["guid"] == value]
        elif key == "policyType":
            policies = [p for p in policies if str(p["policyType"]) == value]
        elif key == "zoneName":
            policies = [p for p in policies if p["zoneName"] == value]
        elif key == "user":
            policies = [p for p in policies if ranger_mentions(p, user=value)]
        elif key == "group":
            policies = [p for p in policies if ranger_mentions(p, group=value)]
        elif key == "role":
            policies = [p for p in policies if ranger_mentions(p, role=value)]
        elif key.startswith("resource:"):
            name = key[len("resource:"):]
            policies = [p for p in policies if name in p["resources"] and any(ranger_resource_match(v, value) for v in p["resources"][name]["values"])]
    start, size = int(query.get("startIndex", 0)), int(query.get("pageSize", 200))
    return policies[start:start + size]


def ranger_resource_match(pattern, value):
    if pattern == "*" or pattern == value:
        return True
    if pattern.endswith("*"):
        return value.startswith(pattern[:-1])
    if pattern.endswith("/*") or pattern.endswith("/"):
        return value.startswith(pattern.rstrip("*"))
    return value.startswith(pattern.rstrip("/") + "/")  # recursive path policies


def ranger_for_resource(service_def, service, query):
    policies = [p for p in RANGER_POLICIES if p["serviceType"] == service_def and (not service or p["service"] == service)]
    wanted = {k[len("resource:"):]: v for k, v in query.items() if k.startswith("resource:")}
    return [p for p in policies if all(name in p["resources"] and any(ranger_resource_match(v, value) for v in p["resources"][name]["values"]) for name, value in wanted.items())]


def ranger_zone_header(zone):
    return {"id": zone["id"], "name": zone["name"]}


def ranger_service_header(service):
    return {"id": service["id"], "name": service["name"], "displayName": service["displayName"], "type": service["type"], "isEnabled": service["isEnabled"], "isTagService": False}


def ranger_zone_resources(zone, service_name):
    entry = zone["services"].get(service_name)
    if entry is None:
        return ranger_error(404, f"Service {service_name} is not part of zone {zone['name']}")
    return [{"id": i + 1, "resource": r} for i, r in enumerate(entry["resources"])]


@app.api_route("/service/public/v2/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ranger_direct(rest: str, request: Request):
    return ranger_api(rest, request, features=True)


@app.api_route("/gateway/cdp-proxy-api/ranger/service/public/v2/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ranger_knox(rest: str, request: Request):
    return ranger_api(rest, request, features=True)


@app.api_route("/ranger-1/service/public/v2/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ranger_old(rest: str, request: Request):
    return ranger_api(rest, request, features=False)


def ranger_api(rest, request, features):
    identity = ranger_user(request)
    if identity is None:
        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Ranger"'}, content="Authentication required")
    user, role = identity
    query = dict(request.query_params)
    parts = rest.strip("/").split("/")
    if request.method != "GET":
        return ranger_error(403, f"User {user} is not authorized to perform {request.method} on {rest}") if role != "ADMIN" else ranger_error(400, "Writes are not implemented by the fixture")
    if not features and parts[0] in {"roles", "zones", "zones-v2", "zone-headers", "zone-names"}:
        return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
    # Roles a user holds are visible to that user; everything else needs the Auditor (or Admin) role.
    if parts[:2] == ["roles", "user"] and len(parts) == 3:
        if role == "USER" and parts[2] != user:
            return ranger_error(403, f"User {user} is not authorized to view roles of {parts[2]}")
        return [r["name"] for r in RANGER_ROLES if r["name"] in ranger_principals(parts[2])[1]]
    if role == "USER":
        return ranger_error(403, f"User {user} is not authorized to access {rest}; only administrators and auditors may read policies through this API")
    # Services and service definitions
    if parts == ["servicedef"]:
        return [d for d in RANGER_SERVICE_DEFS if not query.get("serviceType") or d["name"] == query["serviceType"]]
    if parts[:2] == ["servicedef", "name"] and len(parts) == 3:
        return next((d for d in RANGER_SERVICE_DEFS if d["name"] == parts[2]), None) or ranger_error(404, f"Service definition {parts[2]} not found")
    if parts[0] == "servicedef" and len(parts) == 2:
        return next((d for d in RANGER_SERVICE_DEFS if str(d["id"]) == parts[1]), None) or ranger_error(404, f"Service definition {parts[1]} not found")
    if parts == ["service"]:
        return [s for s in RANGER_SERVICES if (not query.get("serviceType") or s["type"] == query["serviceType"]) and (not query.get("serviceName") or s["name"] == query["serviceName"])
            and (not query.get("serviceNamePartial") or query["serviceNamePartial"].lower() in s["name"].lower())]
    if parts == ["service-headers"]:
        return [ranger_service_header(s) for s in RANGER_SERVICES]
    if parts[:2] == ["service", "name"] and len(parts) == 3:
        return next((s for s in RANGER_SERVICES if s["name"] == parts[2]), None) or ranger_error(404, f"Service {parts[2]} not found")
    if parts[0] == "service" and len(parts) == 2:
        return next((s for s in RANGER_SERVICES if str(s["id"]) == parts[1]), None) or ranger_error(404, f"Service {parts[1]} not found")
    if parts[0] == "service" and len(parts) == 3 and parts[2] == "tags":
        if not any(s["name"] == parts[1] for s in RANGER_SERVICES):
            return ranger_error(404, f"Service {parts[1]} not found")
        tags = RANGER_TAGS.get(parts[1]) or {"op": "add_or_update", "serviceName": parts[1], "tagVersion": 0, "tagDefinitions": {}, "tags": {}, "serviceResources": [], "resourceToTagIds": {}}
        return Response(status_code=304) if query.get("lastKnownVersion") == str(tags["tagVersion"]) else tags
    if parts[0] == "service" and len(parts) == 3 and parts[2] == "policy":
        if not any(s["name"] == parts[1] for s in RANGER_SERVICES):
            return ranger_error(404, f"Service {parts[1]} not found")
        return ranger_search(RANGER_POLICIES, {**query, "serviceName": parts[1]})
    if parts[0] == "service" and len(parts) == 4 and parts[2] == "policy":
        found = [p for p in RANGER_POLICIES if p["service"] == parts[1] and p["name"] == parts[3] and p["zoneName"] == query.get("zoneName", "")]
        return found[0] if found else ranger_error(404, f"Policy {parts[3]} not found in service {parts[1]}" + (f" zone {query['zoneName']}" if query.get("zoneName") else ""))
    # Policies
    if parts == ["policy"]:
        return ranger_search(RANGER_POLICIES, query)
    if parts[:2] == ["policy", "guid"] and len(parts) == 3:
        found = [p for p in RANGER_POLICIES if p["guid"] == parts[2] and (not query.get("serviceName") or p["service"] == query["serviceName"]) and p["zoneName"] == query.get("zoneName", "")]
        return found[0] if found else ranger_error(404, f"Policy with guid {parts[2]} not found")
    if parts[0] == "policy" and len(parts) == 2:
        return next((p for p in RANGER_POLICIES if str(p["id"]) == parts[1]), None) or ranger_error(404, f"Policy {parts[1]} not found")
    if parts[0] == "policies" and len(parts) == 3 and parts[2] == "for-resource":
        if not any(d["name"] == parts[1] for d in RANGER_SERVICE_DEFS):
            return ranger_error(404, f"Service definition {parts[1]} not found")
        return ranger_for_resource(parts[1], query.get("serviceName", ""), query)
    # Roles
    if parts == ["roles"]:
        roles = RANGER_ROLES
        if query.get("roleName"):
            roles = [r for r in roles if r["name"] == query["roleName"]]
        if query.get("roleNamePartial"):
            roles = [r for r in roles if query["roleNamePartial"].lower() in r["name"].lower()]
        if query.get("userName"):
            roles = [r for r in roles if r["name"] in ranger_principals(query["userName"])[1]]
        if query.get("groupName"):
            roles = [r for r in roles if any(g["name"] == query["groupName"] for g in r["groups"])]
        return roles
    if parts == ["roles", "names"]:
        return [r["name"] for r in RANGER_ROLES]
    if parts[:2] == ["roles", "name"] and len(parts) == 3:
        return next((r for r in RANGER_ROLES if r["name"] == parts[2]), None) or ranger_error(404, f"Role {parts[2]} not found")
    if parts[0] == "roles" and len(parts) == 2:
        return next((r for r in RANGER_ROLES if str(r["id"]) == parts[1]), None) or ranger_error(404, f"Role {parts[1]} not found")
    # Security zones
    if parts == ["zone-headers"]:
        return [ranger_zone_header(z) for z in RANGER_ZONES]
    if parts[0] == "zone-names" and len(parts) == 3 and parts[2] == "resource":
        wanted = {k[len("resource:"):]: v for k, v in query.items() if k.startswith("resource:")}
        return [z["name"] for z in RANGER_ZONES if parts[1] in z["services"] and any(all(name in r and any(ranger_resource_match(p, value) for p in r[name]) for name, value in wanted.items()) for r in z["services"][parts[1]]["resources"])]
    if parts in (["zones"], ["zones-v2"]):
        return RANGER_ZONES
    if parts[0] in {"zones", "zones-v2"} and len(parts) == 3 and parts[1] == "name":
        return next((z for z in RANGER_ZONES if z["name"] == parts[2]), None) or ranger_error(404, f"Security zone {parts[2]} not found")
    if parts[0] == "zones-v2" and len(parts) == 5 and parts[1] == "name" and parts[3] == "resources":
        zone = next((z for z in RANGER_ZONES if z["name"] == parts[2]), None)
        return ranger_zone_resources(zone, parts[4]) if zone else ranger_error(404, f"Security zone {parts[2]} not found")
    if parts[0] == "zones-v2" and len(parts) == 4 and parts[2] == "resources":
        zone = next((z for z in RANGER_ZONES if str(z["id"]) == parts[1]), None)
        return ranger_zone_resources(zone, parts[3]) if zone else ranger_error(404, f"Security zone {parts[1]} not found")
    if parts[:3] == ["zones", "zone-headers", "for-service"] and len(parts) == 4:
        service = next((s for s in RANGER_SERVICES if str(s["id"]) == parts[3]), None)
        return [ranger_zone_header(z) for z in RANGER_ZONES if service and service["name"] in z["services"]]
    if parts[0] == "zones" and len(parts) == 3 and parts[2] == "service-headers":
        zone = next((z for z in RANGER_ZONES if str(z["id"]) == parts[1]), None)
        return [ranger_service_header(s) for s in RANGER_SERVICES if zone and s["name"] in zone["services"]] if zone else ranger_error(404, f"Security zone {parts[1]} not found")
    if parts[0] in {"zones", "zones-v2"} and len(parts) == 2:
        return next((z for z in RANGER_ZONES if str(z["id"]) == parts[1]), None) or ranger_error(404, f"Security zone {parts[1]} not found")
    return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
