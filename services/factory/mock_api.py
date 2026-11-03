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
    return {"authorization": request.headers.get("authorization"), "query": dict(request.query_params), "altus_auth": request.headers.get("x-altus-auth")}


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


# ---- Apache Atlas fake --------------------------------------------------------------------
# The discovery side of the v2 API (search, saved searches, suggestions) at the direct Atlas path, a
# Knox-style path, and /atlas-1 for an Atlas without quick search, relationship search or
# suggestions. Atlas itself filters results by the authenticated identity (the Ranger Atlas plugin),
# so the fake does too: admin and auditor see everything, alice sees the sales mart, bob finance.
import re as _re

ATLAS_ACCOUNTS = {"admin": "admin-secret", "auditor": "auditor-secret", "alice": "alice-secret", "bob": "bob-secret"}
ATLAS_VISIBLE = {"admin": None, "auditor": None, "alice": ("sales", "/data", "Customer"), "bob": ("finance", "/data")}


def atlas_entity(guid, type_name, qualified_name, name, owner, status="ACTIVE", classifications=(), terms=(), **attributes):
    return {"guid": guid, "typeName": type_name, "status": status, "displayText": name, "isIncomplete": False, "labels": [],
        "classificationNames": list(classifications), "meaningNames": list(terms), "meanings": [{"displayText": t, "termGuid": f"term-{t.lower()}"} for t in terms],
        "attributes": {"qualifiedName": qualified_name, "name": name, "owner": owner, **attributes}}


ATLAS_ENTITIES = [
    atlas_entity("db-sales", "hive_db", "sales@cm", "sales", "alice", description="Sales mart", clusterName="cm"),
    atlas_entity("db-finance", "hive_db", "finance@cm", "finance", "bob", description="Finance ledger", clusterName="cm"),
    atlas_entity("tbl-orders", "hive_table", "sales.orders@cm", "orders", "alice", classifications=["Curated"], description="Customer orders", tableType="MANAGED_TABLE", createTime=1760000000000),
    atlas_entity("tbl-customers", "hive_table", "sales.customers@cm", "customers", "alice", classifications=["PII"], terms=["Customer"], description="Customer master data", tableType="MANAGED_TABLE"),
    atlas_entity("tbl-orders-2019", "hive_table", "sales.orders_2019@cm", "orders_2019", "alice", status="DELETED", description="Archived orders"),
    atlas_entity("tbl-payroll", "hive_table", "finance.payroll@cm", "payroll", "bob", classifications=["PII", "Confidential"], description="Monthly payroll", tableType="MANAGED_TABLE"),
    atlas_entity("col-email", "hive_column", "sales.customers.email@cm", "email", "alice", classifications=["PII"], type="string"),
    atlas_entity("col-salary", "hive_column", "finance.payroll.salary@cm", "salary", "bob", classifications=["PII"], type="decimal(12,2)"),
    atlas_entity("path-shared", "hdfs_path", "/data/shared@cm", "shared", "hdfs", path="/data/shared"),
    atlas_entity("term-customer", "AtlasGlossaryTerm", "Customer@Business", "Customer", "steward", shortDescription="A person or organisation that buys from us"),
    atlas_entity("tbl-order-summary", "hive_table", "sales.order_summary@cm", "order_summary", "alice", description="Daily order totals", tableType="MANAGED_TABLE"),
    atlas_entity("proc-load-orders", "hive_process", "sales.etl.load_orders@cm", "load_orders", "etl", description="Loads /data/shared files into sales.orders", queryText="LOAD DATA INPATH '/data/shared' INTO TABLE sales.orders"),
    atlas_entity("proc-summarise", "hive_process", "sales.etl.summarise_orders@cm", "summarise_orders", "etl", description="Aggregates orders per day", queryText="INSERT OVERWRITE TABLE sales.order_summary SELECT ..."),
]
ATLAS_LINEAGE = [("path-shared", "proc-load-orders"), ("proc-load-orders", "tbl-orders"), ("tbl-orders", "proc-summarise"), ("proc-summarise", "tbl-order-summary")]  # (input, output) edges
ATLAS_AUDIT = {
    "tbl-customers": [
        {"eventKey": "tbl-customers:1760000000000", "timestamp": 1760000000000, "user": "atlas-sync", "action": "ENTITY_CREATE", "details": "Created: hive_table sales.customers@cm"},
        {"eventKey": "tbl-customers:1760003600000", "timestamp": 1760003600000, "user": "steward", "action": "CLASSIFICATION_ADD", "details": "Added classification: PII"},
        {"eventKey": "tbl-customers:1760007200000", "timestamp": 1760007200000, "user": "steward", "action": "TERM_ADD", "details": "Added term: Customer"},
    ],
    "tbl-payroll": [{"eventKey": "tbl-payroll:1760000000000", "timestamp": 1760000000000, "user": "atlas-sync", "action": "ENTITY_CREATE", "details": "Created: hive_table finance.payroll@cm"}],
}
ATLAS_CLASSIFICATION_ATTRIBUTES = {("tbl-payroll", "Confidential"): {"level": "high"}, ("col-salary", "PII"): {"type": "salary"}}
ATLAS_RELATIONSHIPS = [
    {"guid": "rel-1", "typeName": "hive_table_db", "status": "ACTIVE", "end1": "tbl-orders", "end2": "db-sales", "end1Attr": "db", "end2Attr": "tables"},
    {"guid": "rel-2", "typeName": "hive_table_db", "status": "ACTIVE", "end1": "tbl-customers", "end2": "db-sales", "end1Attr": "db", "end2Attr": "tables"},
    {"guid": "rel-3", "typeName": "hive_table_db", "status": "ACTIVE", "end1": "tbl-payroll", "end2": "db-finance", "end1Attr": "db", "end2Attr": "tables"},
    {"guid": "rel-4", "typeName": "hive_table_columns", "status": "ACTIVE", "end1": "tbl-customers", "end2": "col-email", "end1Attr": "columns", "end2Attr": "table"},
    {"guid": "rel-5", "typeName": "hive_table_columns", "status": "ACTIVE", "end1": "tbl-payroll", "end2": "col-salary", "end1Attr": "columns", "end2Attr": "table"},
    {"guid": "rel-6", "typeName": "AtlasGlossarySemanticAssignment", "status": "ACTIVE", "end1": "term-customer", "end2": "tbl-customers", "end1Attr": "assignedEntities", "end2Attr": "meanings"},
    {"guid": "rel-7", "typeName": "hive_table_db", "status": "ACTIVE", "end1": "tbl-order-summary", "end2": "db-sales", "end1Attr": "db", "end2Attr": "tables"},
    {"guid": "rel-8", "typeName": "dataset_process_inputs", "status": "ACTIVE", "end1": "proc-load-orders", "end2": "path-shared", "end1Attr": "inputs", "end2Attr": "inputToProcesses"},
    {"guid": "rel-9", "typeName": "process_dataset_outputs", "status": "ACTIVE", "end1": "proc-load-orders", "end2": "tbl-orders", "end1Attr": "outputs", "end2Attr": "outputFromProcesses"},
    {"guid": "rel-10", "typeName": "dataset_process_inputs", "status": "ACTIVE", "end1": "proc-summarise", "end2": "tbl-orders", "end1Attr": "inputs", "end2Attr": "inputToProcesses"},
    {"guid": "rel-11", "typeName": "process_dataset_outputs", "status": "ACTIVE", "end1": "proc-summarise", "end2": "tbl-order-summary", "end1Attr": "outputs", "end2Attr": "outputFromProcesses"},
]
ATLAS_SAVED = [
    {"guid": "ss-1", "name": "PII tables", "ownerName": "admin", "searchType": "BASIC", "searchParameters": {"typeName": "hive_table", "classification": "PII", "excludeDeletedEntities": True, "limit": 25, "offset": 0}, "uiParameters": ""},
    {"guid": "ss-2", "name": "my sales tables", "ownerName": "alice", "searchType": "ADVANCED", "searchParameters": {"query": "hive_table where owner = 'alice'", "limit": 25, "offset": 0}, "uiParameters": ""},
]


def atlas_user(request):
    header = request.headers.get("authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "basic":
        try:
            user, _, password = base64.b64decode(value).decode().partition(":")
        except (ValueError, UnicodeDecodeError):
            return None
        return user if ATLAS_ACCOUNTS.get(user) == password else None
    if scheme.lower() == "bearer" and value.count(".") == 2:
        payload = value.split(".")[1]
        try:
            return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("sub")
        except (ValueError, UnicodeDecodeError):
            return None
    return None


def atlas_error(status, code, message):
    return JSONResponse({"errorCode": code, "errorMessage": message}, status_code=status)


def atlas_visible(user):
    prefixes = ATLAS_VISIBLE.get(user, ())
    return [e for e in ATLAS_ENTITIES if prefixes is None or any(e["attributes"]["qualifiedName"].startswith(p) for p in prefixes)]


def atlas_by_guid(guid):
    return next((e for e in ATLAS_ENTITIES if e["guid"] == guid), None)


def atlas_text(entity):
    return " ".join(str(v) for v in entity["attributes"].values()) + " " + " ".join(entity["classificationNames"] + entity["meaningNames"])


def atlas_like(pattern, value):
    return _re.fullmatch(_re.escape(pattern).replace(r"\*", ".*").replace(r"\?", "."), str(value), _re.I) is not None


def atlas_filter(entities, criterion):
    """SearchParameters.entityFilters: one {attributeName, operator, attributeValue} or {condition, criterion: [...]}."""
    if "criterion" in criterion:
        parts = [atlas_filter(entities, c) for c in criterion["criterion"]]
        if criterion.get("condition", "AND").upper() == "OR":
            seen = {e["guid"] for part in parts for e in part}
            return [e for e in entities if e["guid"] in seen]
        keep = set.intersection(*[{e["guid"] for e in part} for part in parts]) if parts else set()
        return [e for e in entities if e["guid"] in keep]
    name, op, wanted = criterion.get("attributeName", ""), criterion.get("operator", "=").lower(), str(criterion.get("attributeValue", ""))

    def matches(entity):
        value = entity["attributes"].get(name)
        if op in ("isnull", "is_null"):
            return value is None
        if op in ("notnull", "not_null"):
            return value is not None
        if value is None:
            return False
        text = str(value)
        return {"=": text == wanted, "eq": text == wanted, "!=": text != wanted, "neq": text != wanted, "like": atlas_like(wanted, text), "contains": wanted.lower() in text.lower(),
            "startswith": text.lower().startswith(wanted.lower()), "endswith": text.lower().endswith(wanted.lower()),
            "<": text < wanted, "lt": text < wanted, ">": text > wanted, "gt": text > wanted, "<=": text <= wanted, "lte": text <= wanted, ">=": text >= wanted, "gte": text >= wanted}.get(op, False)
    return [e for e in entities if matches(e)]


def atlas_basic(entities, params):
    """Basic search over visible entities: type, classification, term, free-text query, deleted filter, entityFilters."""
    if params.get("typeName"):
        entities = [e for e in entities if e["typeName"] == params["typeName"]]
    if params.get("classification"):
        entities = [e for e in entities if params["classification"] in e["classificationNames"]]
    if params.get("termName"):
        entities = [e for e in entities if params["termName"] in e["meaningNames"]]
    if params.get("query") and params["query"] != "*":
        q = params["query"].rstrip("*").lower()
        entities = [e for e in entities if q in atlas_text(e).lower()]
    if str(params.get("excludeDeletedEntities", "true")).lower() == "true":
        entities = [e for e in entities if e["status"] != "DELETED"]
    if params.get("entityFilters"):
        entities = atlas_filter(entities, params["entityFilters"])
    return entities


def atlas_page(entities, params, extra=None, attributes=None):
    limit, offset = int(params.get("limit", 100) or 100), int(params.get("offset", 0) or 0)
    page = entities[offset:offset + limit]
    result = {"queryType": params.get("_queryType", "BASIC"), "searchParameters": {k: v for k, v in params.items() if not k.startswith("_")}, "approximateCount": len(entities), "entities": []}
    for e in page:
        header = {k: v for k, v in e.items() if k != "attributes"}
        header["attributes"] = {k: v for k, v in e["attributes"].items() if k in {"qualifiedName", "name", "owner", "description", "createTime"} or (attributes and k in attributes)}
        result["entities"].append(header)
    return {**result, **(extra or {})}


def atlas_dsl(entities, query):
    """A small subset of the Atlas DSL: [from] <type> [where <attr> (=|!=|like) '<v>' [and ...] | isa <classification>] [select a, b] [limit n] [offset n]."""
    text = query.strip()
    match = _re.fullmatch(r"(?:from\s+)?(\w+)(?:\s+isa\s+(\w+))?(?:\s+where\s+(.+?))?(?:\s+select\s+([\w\s,]+?))?(?:\s+limit\s+(\d+))?(?:\s+offset\s+(\d+))?", text, _re.I | _re.S)
    if not match:
        return None
    type_name, isa, where, select, limit, offset = match.groups()
    entities = [e for e in entities if e["typeName"] == type_name and e["status"] != "DELETED"]
    if isa:
        entities = [e for e in entities if isa in e["classificationNames"]]
    if where:
        for clause in _re.split(r"\s+and\s+", where, flags=_re.I):
            m = _re.fullmatch(r"(\w+)\s*(=|!=|like)\s*'([^']*)'", clause.strip(), _re.I)
            if not m:
                return None
            attr, op, value = m.groups()
            entities = atlas_filter(entities, {"attributeName": attr, "operator": op.lower(), "attributeValue": value})
    columns = [c.strip() for c in select.split(",")] if select else None
    return entities, columns, int(limit or 100), int(offset or 0)


def atlas_relationship_view(rel):
    e1, e2 = atlas_by_guid(rel["end1"]), atlas_by_guid(rel["end2"])
    end = lambda e: {"guid": e["guid"], "typeName": e["typeName"], "uniqueAttributes": {"qualifiedName": e["attributes"]["qualifiedName"]}}
    return {"guid": rel["guid"], "typeName": rel["typeName"], "status": rel["status"], "end1": end(e1), "end2": end(e2)}


@app.api_route("/api/atlas/v2/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def atlas_direct(rest: str, request: Request):
    return await atlas_api(rest, request, features=True)


@app.api_route("/gateway/cdp-proxy-api/atlas/api/atlas/v2/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def atlas_knox(rest: str, request: Request):
    return await atlas_api(rest, request, features=True)


@app.api_route("/atlas-1/api/atlas/v2/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def atlas_old(rest: str, request: Request):
    return await atlas_api(rest, request, features=False)


async def atlas_api(rest, request, features):
    user = atlas_user(request)
    if user is None:
        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Atlas"'}, content="Authentication required")
    query = dict(request.query_params)
    parts = rest.strip("/").split("/")
    visible = atlas_visible(user)
    if parts[0] in {"entity", "lineage", "relationship"}:
        return atlas_entity_api(parts, query, user, visible, features, request.query_params.getlist("guid"))
    if parts[0] == "glossary":
        return atlas_glossary_api(parts, query, visible)
    if parts[0] == "types":
        return atlas_types_api(parts, query, features)
    if parts[0] != "search":
        return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
    if not features and len(parts) > 1 and parts[1] in {"quick", "relations", "relationship", "suggestions"}:
        return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
    if parts == ["search", "basic"] and request.method == "GET":
        return atlas_page(atlas_basic(visible, query), query)
    if parts == ["search", "basic"] and request.method == "POST":
        body = await request.json()
        if not isinstance(body, dict):
            return atlas_error(400, "ATLAS-400-00-001", "Invalid search parameters")
        return atlas_page(atlas_basic(visible, body), {**body, "_queryType": "BASIC"}, attributes=set(body.get("attributes") or []))
    if parts == ["search", "attribute"]:
        name, prefix = query.get("attrName", ""), query.get("attrValuePrefix", "")
        if not name:
            return atlas_error(400, "ATLAS-400-00-00C", "attrName is required")
        entities = [e for e in visible if e["status"] != "DELETED" and str(e["attributes"].get(name, "")).lower().startswith(prefix.lower()) and (not query.get("typeName") or e["typeName"] == query["typeName"])]
        return atlas_page(entities, {**query, "_queryType": "ATTRIBUTE"})
    if parts == ["search", "dsl"]:
        if not query.get("query") and not query.get("typeName"):
            return atlas_error(400, "ATLAS-400-00-059", "Invalid DSL query: query or typeName is required")
        text = query.get("query") or ""
        if query.get("typeName") and not text.lower().startswith(("from", query["typeName"].lower())):
            text = f"{query['typeName']} {text}".strip()
        parsed = atlas_dsl(visible, text)
        if parsed is None:
            return atlas_error(400, "ATLAS-400-00-059", f"Invalid DSL query: [{text}] | Reason: expected <type> [where ...] [select ...]")
        entities, columns, limit, offset = parsed
        if query.get("classification"):
            entities = [e for e in entities if query["classification"] in e["classificationNames"]]
        limit, offset = int(query.get("limit") or limit), int(query.get("offset") or offset)
        if columns:
            rows = [[e["attributes"].get(c) if c not in ("typeName", "guid") else e[c] for c in columns] for e in entities[offset:offset + limit]]
            return {"queryType": "DSL", "queryText": text, "attributes": {"name": columns, "values": rows}, "approximateCount": len(entities)}
        return {**atlas_page(entities, {"limit": limit, "offset": offset, "_queryType": "DSL"}), "queryText": text}
    if parts == ["search", "fulltext"]:
        q = (query.get("query") or "").lower()
        entities = [e for e in visible if q and q in atlas_text(e).lower()]
        if str(query.get("excludeDeletedEntities", "true")).lower() == "true":
            entities = [e for e in entities if e["status"] != "DELETED"]
        return atlas_page(entities, {**query, "_queryType": "FULL_TEXT"}, {"fullTextResult": [{"entity": {"guid": e["guid"], "typeName": e["typeName"]}, "score": 1.0} for e in entities]})
    if parts == ["search", "quick"]:
        entities = atlas_basic(visible, query)
        counts = {}
        for e in entities:
            counts[e["typeName"]] = counts.get(e["typeName"], 0) + 1
        return {"searchResults": atlas_page(entities, {**query, "_queryType": "BASIC"}), "aggregationMetrics": {"__typeName": counts}}
    if parts == ["search", "relations"]:
        rels = [r for r in ATLAS_RELATIONSHIPS if (not query.get("relationshipName") or r["typeName"] == query["relationshipName"]) and atlas_by_guid(r["end1"]) in visible and atlas_by_guid(r["end2"]) in visible]
        limit, offset = int(query.get("limit") or 100), int(query.get("offset") or 0)
        return {"queryType": "RELATIONSHIP", "searchParameters": query, "approximateCount": len(rels), "relations": [atlas_relationship_view(r) for r in rels[offset:offset + limit]]}
    if parts == ["search", "relationship"]:
        guid, relation = query.get("guid", ""), query.get("relation", "")
        entity = atlas_by_guid(guid)
        if entity is None or entity not in visible:
            return atlas_error(404, "ATLAS-404-00-005", f"Given instance guid {guid} is invalid/not found")
        if not relation:
            return atlas_error(400, "ATLAS-400-00-00C", "relation is required")
        related = []
        for r in ATLAS_RELATIONSHIPS:
            if r["end1"] == guid and r["end1Attr"] == relation:
                related.append(atlas_by_guid(r["end2"]))
            if r["end2"] == guid and r["end2Attr"] == relation:
                related.append(atlas_by_guid(r["end1"]))
        related = [e for e in related if e in visible]
        return atlas_page(related, {**query, "_queryType": "RELATIONSHIP"})
    if parts == ["search", "saved"] and request.method == "GET":
        owner = query.get("user") or user
        if owner != user and user not in ("admin",):
            return atlas_error(403, "ATLAS-403-00-001", f"{user} is not authorized to read saved searches of {owner}")
        saved = [s for s in ATLAS_SAVED if s["ownerName"] == owner and (not query.get("searchType") or s["searchType"] == query["searchType"])]
        return saved
    if parts[:2] == ["search", "saved"] and len(parts) == 3 and request.method == "GET":
        owner = query.get("user") or user
        if owner != user and user != "admin":
            return atlas_error(403, "ATLAS-403-00-001", f"{user} is not authorized to read saved searches of {owner}")
        saved = next((s for s in ATLAS_SAVED if s["ownerName"] == owner and s["name"] == parts[2]), None)
        return saved or atlas_error(404, "ATLAS-404-00-00E", f"Saved search '{parts[2]}' not found for user {owner}")
    if parts[:3] == ["search", "saved", "execute"]:
        if parts[3] == "guid":
            saved = next((s for s in ATLAS_SAVED if s["guid"] == parts[4]), None)
        else:
            owner = query.get("user") or user
            saved = next((s for s in ATLAS_SAVED if s["ownerName"] == owner and s["name"] == parts[3]), None)
        if saved is None:
            return atlas_error(404, "ATLAS-404-00-00E", f"Saved search {parts[-1]} not found")
        if saved["ownerName"] != user and user != "admin":
            return atlas_error(403, "ATLAS-403-00-001", f"{user} is not authorized to execute saved searches of {saved['ownerName']}")
        if saved["searchType"] == "BASIC":
            return atlas_page(atlas_basic(visible, saved["searchParameters"]), {**saved["searchParameters"], "_queryType": "BASIC"})
        entities, columns, limit, offset = atlas_dsl(visible, saved["searchParameters"]["query"])
        return {**atlas_page(entities, {"limit": limit, "offset": offset, "_queryType": "DSL"}), "queryText": saved["searchParameters"]["query"]}
    if parts == ["search", "suggestions"]:
        prefix, field = (query.get("prefixString") or "").lower(), query.get("fieldName") or "name"
        values = sorted({str(e["attributes"].get(field, "")) for e in visible if e["status"] != "DELETED" and str(e["attributes"].get(field, "")).lower().startswith(prefix) and prefix})
        return {"prefixString": query.get("prefixString", ""), "fieldName": field, "suggestions": values}
    return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")


def atlas_header(entity):
    return {k: v for k, v in entity.items() if k != "attributes"} | {"attributes": {k: v for k, v in entity["attributes"].items() if k in {"qualifiedName", "name", "owner", "description", "createTime"}}}


def atlas_classifications(entity):
    own = [{"typeName": c, "entityGuid": entity["guid"], "entityStatus": "ACTIVE", "propagate": True, "removePropagationsOnEntityDelete": False, "validityPeriods": [],
        "attributes": ATLAS_CLASSIFICATION_ATTRIBUTES.get((entity["guid"], c), {})} for c in entity["classificationNames"]]
    # A column inherits its table's classifications by propagation.
    if entity["typeName"] == "hive_column":
        table = next((atlas_by_guid(r["end1"]) for r in ATLAS_RELATIONSHIPS if r["end2"] == entity["guid"] and r["typeName"] == "hive_table_columns"), None)
        own += [{"typeName": c, "entityGuid": table["guid"], "entityStatus": "ACTIVE", "propagate": True, "removePropagationsOnEntityDelete": False, "validityPeriods": [], "attributes": {}}
            for c in (table["classificationNames"] if table else []) if c not in entity["classificationNames"]]
    return own


def atlas_full(entity):
    related = {}
    for r in ATLAS_RELATIONSHIPS:
        for me, other, attr in ((r["end1"], r["end2"], r["end1Attr"]), (r["end2"], r["end1"], r["end2Attr"])):
            if me == entity["guid"]:
                target = atlas_by_guid(other)
                related.setdefault(attr, []).append({"guid": target["guid"], "typeName": target["typeName"], "displayText": target["attributes"]["name"], "relationshipGuid": r["guid"], "relationshipStatus": "ACTIVE", "entityStatus": target["status"]})
    singular = {"db", "table"}
    relationship_attributes = {k: (v[0] if k in singular else v) for k, v in related.items()}
    full = {**entity, "attributes": {**entity["attributes"], "description": entity["attributes"].get("description")}, "relationshipAttributes": relationship_attributes,
        "classifications": atlas_classifications(entity), "createdBy": "atlas-sync", "updatedBy": "steward" if entity["classificationNames"] else "atlas-sync",
        "createTime": 1760000000000, "updateTime": 1760007200000, "version": 2 if entity["classificationNames"] else 0, "proxy": False, "isIncomplete": False}
    referred = {g: atlas_header(atlas_by_guid(g)) for v in related.values() for g in [x["guid"] for x in v]}
    return {"referredEntities": referred, "entity": full}


def atlas_lineage(entity, direction, depth):
    nodes, edges, frontier = {entity["guid"]: entity}, set(), {entity["guid"]}
    for _ in range(max(1, depth) * 2):  # each hop crosses a process and a dataset
        step = set()
        for guid in frontier:
            for source, target in ATLAS_LINEAGE:
                if direction in ("INPUT", "BOTH") and target == guid:
                    edges.add((source, target)); step.add(source)
                if direction in ("OUTPUT", "BOTH") and source == guid:
                    edges.add((source, target)); step.add(target)
        step -= set(nodes)
        for guid in step:
            nodes[guid] = atlas_by_guid(guid)
        frontier = step
        if not frontier:
            break
    return {"baseEntityGuid": entity["guid"], "lineageDirection": direction, "lineageDepth": depth, "guidEntityMap": {g: atlas_header(e) for g, e in nodes.items()},
        "relations": [{"fromEntityId": a, "toEntityId": b, "relationshipId": f"lin-{a}-{b}"} for a, b in sorted(edges)]}


def atlas_entity_api(parts, query, user, visible, features, guids=()):
    missing = lambda guid: atlas_error(404, "ATLAS-404-00-005", f"Given instance guid {guid} is invalid/not found")
    forbidden = lambda what: atlas_error(403, "ATLAS-403-00-001", f"{user} is not authorized to perform read entity : {what}")

    def lookup(guid):
        entity = atlas_by_guid(guid)
        if entity is None:
            return None, missing(guid)
        if entity not in visible:
            return None, forbidden(entity["attributes"]["qualifiedName"])
        return entity, None

    def by_unique(type_name, index=None):
        prefix = f"attr_{index}:" if index is not None else "attr:"
        attrs = {k[len(prefix):]: v for k, v in query.items() if k.startswith(prefix)}
        if not attrs:
            return None, atlas_error(400, "ATLAS-400-00-00C", "attr:<name>=<value> is required") if index is None else (None, None)
        entity = next((e for e in ATLAS_ENTITIES if e["typeName"] == type_name and all(str(e["attributes"].get(k)) == v for k, v in attrs.items())), None)
        if entity is None:
            return None, atlas_error(404, "ATLAS-404-00-007", f"Instance {type_name} with unique attribute {attrs} does not exist")
        if entity not in visible:
            return None, forbidden(entity["attributes"]["qualifiedName"])
        return entity, None

    if parts[0] == "entity":
        if parts[1:] == ["bulk"]:
            guids = [g for g in guids if g]
            found, referred = [], {}
            for guid in guids:
                entity, err = lookup(guid)
                if err is not None and err.status_code == 404:
                    return err
                if entity is not None:
                    full = atlas_full(entity)
                    found.append(full["entity"]); referred.update(full["referredEntities"])
            if not found:
                return atlas_error(404, "ATLAS-404-00-005", "Given instance guid is invalid/not found") if not guids else forbidden(",".join(guids))
            return {"entities": found, "referredEntities": referred}
        if parts[1:] == ["bulk", "headers"]:
            if not features:
                return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
            since = int(query.get("tagUpdateStartTime", 0) or 0)
            changed = [e for e in visible if e["classificationNames"] and 1760007200000 >= since]
            return {"guidHeaderMap": {e["guid"]: atlas_header(e) for e in changed}}
        if parts[1:3] == ["bulk", "uniqueAttribute"] and len(parts) == 5:
            found, referred, i = [], {}, 0
            while any(k.startswith(f"attr_{i}:") for k in query):
                entity, err = by_unique(parts[4], i)
                if err is not None:
                    return err
                full = atlas_full(entity); found.append(full["entity"]); referred.update(full["referredEntities"]); i += 1
            if not found:
                return atlas_error(400, "ATLAS-400-00-00C", "attr_<n>:<name>=<value> is required")
            return {"entities": found, "referredEntities": referred}
        if parts[1] == "guid" and len(parts) >= 3:
            entity, err = lookup(parts[2])
            if err is not None:
                return err
            if len(parts) == 3:
                return atlas_full(entity)
            if parts[3] == "header":
                return atlas_header(entity)
            if parts[3] == "classifications":
                return {"list": atlas_classifications(entity), "startIndex": 0, "pageSize": 100, "totalCount": len(atlas_classifications(entity)), "sortType": "NONE"}
            if parts[3] == "classification" and len(parts) == 5:
                found = next((c for c in atlas_classifications(entity) if c["typeName"] == parts[4]), None)
                return found or atlas_error(404, "ATLAS-404-00-013", f"Classification {parts[4]} is not associated with entity {parts[2]}")
        if parts[1] == "uniqueAttribute" and parts[2] == "type" and len(parts) in (4, 5):
            entity, err = by_unique(parts[3])
            if err is not None:
                return err
            return atlas_header(entity) if len(parts) == 5 and parts[4] == "header" else atlas_full(entity)
        if len(parts) == 3 and parts[2] == "audit":
            entity, err = lookup(parts[1])
            if err is not None:
                return err
            events = sorted(ATLAS_AUDIT.get(parts[1], []), key=lambda e: -e["timestamp"])
            if query.get("auditAction"):
                events = [e for e in events if e["action"] == query["auditAction"]]
            if query.get("startKey"):
                events = [e for e in events if e["eventKey"] < query["startKey"]]
            count = int(query.get("count", 100) or 100)
            return [{**e, "entityId": parts[1], "type": "ENTITY_AUDIT_V2"} for e in events[:count]]
    if parts[0] == "lineage":
        direction, depth = query.get("direction", "BOTH").upper(), int(query.get("depth", 3) or 3)
        if direction not in ("INPUT", "OUTPUT", "BOTH"):
            return atlas_error(400, "ATLAS-400-00-00C", "direction must be INPUT, OUTPUT or BOTH")
        if parts[1:3] == ["uniqueAttribute", "type"] and len(parts) == 4:
            entity, err = by_unique(parts[3])
        else:
            entity, err = lookup(parts[1])
        if err is not None:
            return err
        info = atlas_lineage(entity, direction, depth)
        info["guidEntityMap"] = {g: h for g, h in info["guidEntityMap"].items() if atlas_by_guid(g) in visible}
        info["relations"] = [r for r in info["relations"] if r["fromEntityId"] in info["guidEntityMap"] and r["toEntityId"] in info["guidEntityMap"]]
        return info
    if parts[0] == "relationship" and parts[1] == "guid" and len(parts) == 3:
        rel = next((r for r in ATLAS_RELATIONSHIPS if r["guid"] == parts[2]), None)
        if rel is None:
            return atlas_error(404, "ATLAS-404-00-00C", f"Given relationship guid {parts[2]} is invalid/not found")
        e1, e2 = atlas_by_guid(rel["end1"]), atlas_by_guid(rel["end2"])
        if e1 not in visible or e2 not in visible:
            return forbidden(parts[2])
        view = atlas_relationship_view(rel)
        full = {**view, "label": f"__{rel['typeName']}", "propagateTags": "NONE", "createdBy": "atlas-sync", "updatedBy": "atlas-sync", "createTime": 1760000000000, "updateTime": 1760000000000, "version": 0}
        result = {"relationship": full}
        if str(query.get("extendedInfo", "false")).lower() == "true":
            result["referredEntities"] = {e1["guid"]: atlas_header(e1), e2["guid"]: atlas_header(e2)}
        return result
    return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")


# Glossaries: Business (categories Sales > Customer Management, Finance; terms Customer, Order, Invoice, Payroll) and
# Regulatory (term PII, assigned to every PII-classified entity). Glossary objects are visible to every authenticated
# user; the entities a term is assigned to are filtered by identity like everything else.
ATLAS_GLOSSARIES = {
    "gl-business": {"guid": "gl-business", "qualifiedName": "Business", "name": "Business", "shortDescription": "Business vocabulary", "longDescription": "Terms the business uses for its data, owned by the data stewards.", "language": "en", "usage": "Tag tables and columns with the term they hold"},
    "gl-regulatory": {"guid": "gl-regulatory", "qualifiedName": "Regulatory", "name": "Regulatory", "shortDescription": "Regulatory vocabulary", "longDescription": "", "language": "en", "usage": ""},
}
ATLAS_CATEGORIES = {
    "cat-sales": {"guid": "cat-sales", "qualifiedName": "Sales@Business", "name": "Sales", "shortDescription": "Selling and customers", "longDescription": "", "glossary": "gl-business", "parent": None},
    "cat-customer-mgmt": {"guid": "cat-customer-mgmt", "qualifiedName": "Sales.Customer Management@Business", "name": "Customer Management", "shortDescription": "Knowing our customers", "longDescription": "", "glossary": "gl-business", "parent": "cat-sales"},
    "cat-finance": {"guid": "cat-finance", "qualifiedName": "Finance@Business", "name": "Finance", "shortDescription": "Money in and out", "longDescription": "", "glossary": "gl-business", "parent": None},
}
ATLAS_TERMS = {
    "term-customer": {"guid": "term-customer", "qualifiedName": "Customer@Business", "name": "Customer", "shortDescription": "A person or organisation that buys from us", "longDescription": "Identified by a customer id; may hold personal data.", "abbreviation": "", "usage": "Tables and columns describing customers", "examples": ["customers table", "customer_id column"],
        "glossary": "gl-business", "categories": ["cat-customer-mgmt"], "assigned": ["tbl-customers"], "related": {"seeAlso": ["term-order"]}, "classifications": []},
    "term-order": {"guid": "term-order", "qualifiedName": "Order@Business", "name": "Order", "shortDescription": "A customer's request to buy", "longDescription": "", "abbreviation": "", "usage": "", "examples": [],
        "glossary": "gl-business", "categories": ["cat-sales"], "assigned": [], "related": {"seeAlso": ["term-customer", "term-invoice"]}, "classifications": []},
    "term-invoice": {"guid": "term-invoice", "qualifiedName": "Invoice@Business", "name": "Invoice", "shortDescription": "A bill sent for an order", "longDescription": "", "abbreviation": "INV", "usage": "", "examples": [],
        "glossary": "gl-business", "categories": ["cat-finance"], "assigned": [], "related": {"seeAlso": ["term-order"], "synonyms": ["term-bill"]}, "classifications": []},
    "term-bill": {"guid": "term-bill", "qualifiedName": "Bill@Business", "name": "Bill", "shortDescription": "Synonym of Invoice", "longDescription": "", "abbreviation": "", "usage": "", "examples": [],
        "glossary": "gl-business", "categories": ["cat-finance"], "assigned": [], "related": {"synonyms": ["term-invoice"]}, "classifications": []},
    "term-payroll": {"guid": "term-payroll", "qualifiedName": "Payroll@Business", "name": "Payroll", "shortDescription": "Salaries paid to staff", "longDescription": "", "abbreviation": "", "usage": "", "examples": [],
        "glossary": "gl-business", "categories": ["cat-finance"], "assigned": ["tbl-payroll"], "related": {}, "classifications": [{"typeName": "Confidential", "attributes": {}}]},
    "term-pii": {"guid": "term-pii", "qualifiedName": "PII@Regulatory", "name": "PII", "shortDescription": "Personally identifiable information", "longDescription": "Data that identifies a natural person; handling is regulated.", "abbreviation": "PII", "usage": "", "examples": ["email", "salary"],
        "glossary": "gl-regulatory", "categories": [], "assigned": ["tbl-customers", "col-email", "tbl-payroll", "col-salary"], "related": {}, "classifications": []},
}


def atlas_term_header(guid):
    term = ATLAS_TERMS[guid]
    return {"termGuid": guid, "relationGuid": f"rel-{guid}", "displayText": term["name"], "status": "ACTIVE"}


def atlas_category_header(guid):
    category = ATLAS_CATEGORIES[guid]
    return {"categoryGuid": guid, "relationGuid": f"rel-{guid}", "displayText": category["name"], **({"parentCategoryGuid": category["parent"]} if category["parent"] else {})}


def atlas_glossary_view(guid):
    g = ATLAS_GLOSSARIES[guid]
    return {**g, "terms": [atlas_term_header(t) for t in ATLAS_TERMS if ATLAS_TERMS[t]["glossary"] == guid], "categories": [atlas_category_header(c) for c in ATLAS_CATEGORIES if ATLAS_CATEGORIES[c]["glossary"] == guid]}


def atlas_category_view(guid):
    c = ATLAS_CATEGORIES[guid]
    view = {k: v for k, v in c.items() if k not in {"glossary", "parent"}}
    view["anchor"] = {"glossaryGuid": c["glossary"], "relationGuid": f"anchor-{guid}"}
    if c["parent"]:
        view["parentCategory"] = atlas_category_header(c["parent"])
    children = [atlas_category_header(x) for x in ATLAS_CATEGORIES if ATLAS_CATEGORIES[x]["parent"] == guid]
    if children:
        view["childrenCategories"] = children
    terms = [atlas_term_header(t) for t in ATLAS_TERMS if guid in ATLAS_TERMS[t]["categories"]]
    if terms:
        view["terms"] = terms
    return view


def atlas_term_view(guid, visible):
    t = ATLAS_TERMS[guid]
    view = {k: v for k, v in t.items() if k not in {"glossary", "categories", "assigned", "related"}}
    view["anchor"] = {"glossaryGuid": t["glossary"], "relationGuid": f"anchor-{guid}"}
    if t["categories"]:
        view["categories"] = [atlas_category_header(c) for c in t["categories"]]
    assigned = [atlas_by_guid(g) for g in t["assigned"] if atlas_by_guid(g) in visible]
    if assigned:
        view["assignedEntities"] = [{"guid": e["guid"], "typeName": e["typeName"], "displayText": e["attributes"]["name"], "relationshipGuid": f"assign-{guid}-{e['guid']}", "relationshipStatus": "ACTIVE", "entityStatus": e["status"],
            "uniqueAttributes": {"qualifiedName": e["attributes"]["qualifiedName"]}} for e in assigned]
    for relation, others in t["related"].items():
        view[relation] = [atlas_term_header(o) for o in others]
    return view


def atlas_glossary_api(parts, query, visible):
    not_found = lambda guid: atlas_error(404, "ATLAS-404-00-005", f"Given instance guid {guid} is invalid/not found")
    limit, offset = int(query.get("limit", -1) or -1), int(query.get("offset", 0) or 0)
    page = lambda items: items[offset:] if limit < 0 else items[offset:offset + limit]
    if parts == ["glossary"]:
        return page([atlas_glossary_view(g) for g in ATLAS_GLOSSARIES])
    if parts[1] == "category" and len(parts) >= 3:
        if parts[2] not in ATLAS_CATEGORIES:
            return not_found(parts[2])
        if len(parts) == 3:
            return atlas_category_view(parts[2])
        if parts[3] == "related":
            c = ATLAS_CATEGORIES[parts[2]]
            related = {}
            if c["parent"]:
                related["parent"] = [atlas_category_header(c["parent"])]
            children = [atlas_category_header(x) for x in ATLAS_CATEGORIES if ATLAS_CATEGORIES[x]["parent"] == parts[2]]
            if children:
                related["children"] = children
            return related
        if parts[3] == "terms":
            return page([atlas_term_header(t) for t in ATLAS_TERMS if parts[2] in ATLAS_TERMS[t]["categories"]])
    if parts[1] in ("term", "terms") and len(parts) >= 3:
        if parts[2] not in ATLAS_TERMS:
            return not_found(parts[2])
        if len(parts) == 3:
            return atlas_term_view(parts[2], visible)
        if parts[3] == "assignedEntities":
            return page(atlas_term_view(parts[2], visible).get("assignedEntities", []))
        if parts[3] == "related":
            return {relation: [atlas_term_header(o) for o in others] for relation, others in ATLAS_TERMS[parts[2]]["related"].items()}
    if len(parts) >= 2 and parts[1] in ATLAS_GLOSSARIES:
        guid = parts[1]
        if len(parts) == 2:
            return atlas_glossary_view(guid)
        if parts[2] == "detailed":
            view = atlas_glossary_view(guid)
            return {**view, "termInfo": {t: atlas_term_view(t, visible) for t in ATLAS_TERMS if ATLAS_TERMS[t]["glossary"] == guid}, "categoryInfo": {c: atlas_category_view(c) for c in ATLAS_CATEGORIES if ATLAS_CATEGORIES[c]["glossary"] == guid}}
        if parts[2:] == ["categories"]:
            return page([atlas_category_view(c) for c in ATLAS_CATEGORIES if ATLAS_CATEGORIES[c]["glossary"] == guid])
        if parts[2:] == ["categories", "headers"]:
            return page([atlas_category_header(c) for c in ATLAS_CATEGORIES if ATLAS_CATEGORIES[c]["glossary"] == guid])
        if parts[2:] == ["terms"]:
            return page([atlas_term_view(t, visible) for t in ATLAS_TERMS if ATLAS_TERMS[t]["glossary"] == guid])
        if parts[2:] == ["terms", "headers"]:
            return page([atlas_term_header(t) for t in ATLAS_TERMS if ATLAS_TERMS[t]["glossary"] == guid])
    if len(parts) >= 2 and parts[1] not in ATLAS_GLOSSARIES and parts[1] not in ("category", "term", "terms"):
        return not_found(parts[1])
    return Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")


# Type system: entity types with inheritance, classifications with applicability, an enum, a struct, relationships and
# (on Atlas 2.1+ only, so not on the /atlas-1 prefix) business metadata. Types are not filtered by identity.
def atlas_attr(name, type_name, optional=True, cardinality="SINGLE", unique=False, indexable=False, description=None, default=None, **options):
    attr = {"name": name, "typeName": type_name, "isOptional": optional, "cardinality": cardinality, "valuesMinCount": 0 if optional else 1, "valuesMaxCount": 1 if cardinality == "SINGLE" else 2147483647,
        "isUnique": unique, "isIndexable": indexable, "includeInNotification": False, "searchWeight": -1}
    if description:
        attr["description"] = description
    if default is not None:
        attr["defaultValue"] = default
    if options:
        attr["options"] = options
    return attr


def atlas_type(name, category, guid, description, attributes=(), service_type=None, **extra):
    item = {"category": category, "guid": guid, "createdBy": "admin", "updatedBy": "admin", "createTime": 1750000000000, "updateTime": 1750000000000, "version": 1, "name": name, "description": description,
        "typeVersion": "1.0", "attributeDefs": list(attributes), **extra}
    if service_type:
        item["serviceType"] = service_type
    return item


def atlas_end(type_name, name, cardinality="SINGLE", container=False):
    return {"type": type_name, "name": name, "isContainer": container, "cardinality": cardinality, "isLegacyAttribute": False}


ATLAS_TYPES = [
    atlas_type("Referenceable", "ENTITY", "type-referenceable", "Any entity that can be referenced by a unique name", [atlas_attr("qualifiedName", "string", optional=False, unique=True, indexable=True)], "atlas_core", superTypes=[]),
    atlas_type("Asset", "ENTITY", "type-asset", "A named asset with an owner", [atlas_attr("name", "string", optional=False, indexable=True), atlas_attr("description", "string"), atlas_attr("owner", "string", indexable=True), atlas_attr("userDescription", "string")],
        "atlas_core", superTypes=["Referenceable"]),
    atlas_type("DataSet", "ENTITY", "type-dataset", "A set of data: a table, a file, a topic", [], "atlas_core", superTypes=["Asset"],
        relationshipAttributeDefs=[{"name": "inputToProcesses", "typeName": "array<Process>", "isOptional": True, "cardinality": "SET", "relationshipTypeName": "dataset_process_inputs"},
            {"name": "outputFromProcesses", "typeName": "array<Process>", "isOptional": True, "cardinality": "SET", "relationshipTypeName": "process_dataset_outputs"}]),
    atlas_type("Process", "ENTITY", "type-process", "Something that reads inputs and writes outputs", [atlas_attr("inputs", "array<DataSet>", cardinality="SET"), atlas_attr("outputs", "array<DataSet>", cardinality="SET")], "atlas_core", superTypes=["Asset"]),
    atlas_type("hive_db", "ENTITY", "type-hive-db", "A Hive database", [atlas_attr("clusterName", "string", optional=False, indexable=True), atlas_attr("location", "string"), atlas_attr("parameters", "map<string,string>"), atlas_attr("ownerType", "hive_principal_type")],
        "hive", superTypes=["Asset"]),
    atlas_type("hive_table", "ENTITY", "type-hive-table", "A Hive table", [atlas_attr("createTime", "date"), atlas_attr("lastAccessTime", "date"), atlas_attr("comment", "string"), atlas_attr("retention", "int"), atlas_attr("tableType", "string", indexable=True),
        atlas_attr("temporary", "boolean", default="false"), atlas_attr("parameters", "map<string,string>")], "hive", superTypes=["DataSet"],
        relationshipAttributeDefs=[{"name": "db", "typeName": "hive_db", "isOptional": False, "cardinality": "SINGLE", "relationshipTypeName": "hive_table_db"},
            {"name": "columns", "typeName": "array<hive_column>", "isOptional": True, "cardinality": "SET", "relationshipTypeName": "hive_table_columns"}]),
    atlas_type("hive_column", "ENTITY", "type-hive-column", "A column of a Hive table", [atlas_attr("type", "string", optional=False, indexable=True), atlas_attr("comment", "string"), atlas_attr("position", "int")], "hive", superTypes=["DataSet"],
        relationshipAttributeDefs=[{"name": "table", "typeName": "hive_table", "isOptional": False, "cardinality": "SINGLE", "relationshipTypeName": "hive_table_columns"}]),
    atlas_type("hive_process", "ENTITY", "type-hive-process", "A Hive query that produced data", [atlas_attr("startTime", "date", optional=False), atlas_attr("endTime", "date", optional=False), atlas_attr("userName", "string"), atlas_attr("queryText", "string", optional=False), atlas_attr("queryPlan", "string")],
        "hive", superTypes=["Process"]),
    atlas_type("hdfs_path", "ENTITY", "type-hdfs-path", "A path in HDFS or Ozone", [atlas_attr("path", "string", optional=False, indexable=True), atlas_attr("clusterName", "string"), atlas_attr("numberOfReplicas", "int"), atlas_attr("fileSize", "long"), atlas_attr("isFile", "boolean", default="false")],
        "hdfs", superTypes=["DataSet"]),
    atlas_type("PII", "CLASSIFICATION", "type-pii", "Personally identifiable information", [atlas_attr("type", "string", description="What kind of personal data")], superTypes=[], entityTypes=[]),
    atlas_type("Confidential", "CLASSIFICATION", "type-confidential", "Restricted to named staff", [atlas_attr("level", "string", default="medium")], superTypes=[], entityTypes=["hive_table", "hdfs_path"]),
    atlas_type("Curated", "CLASSIFICATION", "type-curated", "Reviewed and fit for reporting", [], superTypes=[], entityTypes=["hive_table"]),
    atlas_type("hive_principal_type", "ENUM", "type-hive-principal-type", "Who owns a Hive object", [], "hive", elementDefs=[{"ordinal": 1, "value": "USER"}, {"ordinal": 2, "value": "ROLE"}, {"ordinal": 3, "value": "GROUP"}], defaultValue="USER"),
    atlas_type("hive_order", "STRUCT", "type-hive-order", "A sort order on a column", [atlas_attr("col", "string", optional=False), atlas_attr("order", "int", optional=False)], "hive"),
    atlas_type("hive_table_db", "RELATIONSHIP", "type-hive-table-db", "The database a table belongs to", [], "hive", relationshipCategory="AGGREGATION", propagateTags="NONE",
        endDef1=atlas_end("hive_table", "db"), endDef2=atlas_end("hive_db", "tables", "SET", True)),
    atlas_type("hive_table_columns", "RELATIONSHIP", "type-hive-table-columns", "The columns of a table", [], "hive", relationshipCategory="COMPOSITION", propagateTags="ONE_TO_TWO",
        endDef1=atlas_end("hive_table", "columns", "SET", True), endDef2=atlas_end("hive_column", "table")),
    atlas_type("dataset_process_inputs", "RELATIONSHIP", "type-dataset-process-inputs", "Data sets read by a process", [], "atlas_core", relationshipCategory="AGGREGATION", propagateTags="NONE",
        endDef1=atlas_end("Process", "inputs", "SET"), endDef2=atlas_end("DataSet", "inputToProcesses", "SET")),
    atlas_type("process_dataset_outputs", "RELATIONSHIP", "type-process-dataset-outputs", "Data sets written by a process", [], "atlas_core", relationshipCategory="AGGREGATION", propagateTags="NONE",
        endDef1=atlas_end("Process", "outputs", "SET"), endDef2=atlas_end("DataSet", "outputFromProcesses", "SET")),
    atlas_type("Governance", "BUSINESS_METADATA", "type-governance", "Stewardship facts kept per asset", [atlas_attr("steward", "string", applicableEntityTypes='["hive_table","hdfs_path"]', maxStrLength="50"),
        atlas_attr("retention_days", "int", applicableEntityTypes='["hive_table"]')]),
]
ATLAS_TYPE_KEYS = {"ENTITY": "entityDefs", "CLASSIFICATION": "classificationDefs", "ENUM": "enumDefs", "STRUCT": "structDefs", "RELATIONSHIP": "relationshipDefs", "BUSINESS_METADATA": "businessMetadataDefs"}
ATLAS_TYPE_PATHS = {"entitydef": "ENTITY", "classificationdef": "CLASSIFICATION", "enumdef": "ENUM", "structdef": "STRUCT", "relationshipdef": "RELATIONSHIP", "businessmetadatadef": "BUSINESS_METADATA"}


def atlas_type_view(item):
    view = dict(item)
    if item["category"] in ("ENTITY", "CLASSIFICATION"):
        view["subTypes"] = sorted(t["name"] for t in ATLAS_TYPES if t["category"] == item["category"] and item["name"] in t.get("superTypes", []))
    return view


def atlas_super_types(item):
    names, pending = set(), list(item.get("superTypes", []))
    while pending:
        name = pending.pop()
        if name not in names:
            names.add(name)
            parent = next((t for t in ATLAS_TYPES if t["name"] == name), None)
            pending.extend(parent.get("superTypes", []) if parent else [])
    return names


def atlas_types_api(parts, query, features):
    html_404 = Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
    types = [t for t in ATLAS_TYPES if features or t["category"] != "BUSINESS_METADATA"]
    if parts[1:2] == ["typedefs"]:
        if query.get("type"):
            if query["type"].upper() not in ATLAS_TYPE_KEYS:
                return atlas_error(400, "ATLAS-400-00-00D", f"Invalid type category {query['type']}")
            types = [t for t in types if t["category"] == query["type"].upper()]
        if query.get("supertype"):
            types = [t for t in types if query["supertype"] in atlas_super_types(t)]
        if query.get("serviceType"):
            types = [t for t in types if t.get("serviceType") == query["serviceType"]]
        if query.get("name"):
            types = [t for t in types if t["name"] == query["name"]]
        if parts[2:] == ["headers"]:
            return [{"guid": t["guid"], "name": t["name"], "category": t["category"], **({"serviceType": t["serviceType"]} if t.get("serviceType") else {})} for t in types]
        if len(parts) == 2:
            return {key: [atlas_type_view(t) for t in types if t["category"] == category] for category, key in ATLAS_TYPE_KEYS.items() if features or category != "BUSINESS_METADATA"}
        return html_404
    if len(parts) == 4 and parts[2] == "name" and (parts[1] == "typedef" or parts[1] in ATLAS_TYPE_PATHS):
        if parts[1] == "businessmetadatadef" and not features:
            return html_404
        item = next((t for t in types if t["name"] == parts[3]), None)
        if item is None:
            return atlas_error(404, "ATLAS-404-00-001", f"Given typename {parts[3]} was invalid")
        if parts[1] != "typedef" and ATLAS_TYPE_PATHS[parts[1]] != item["category"]:
            return atlas_error(400, "ATLAS-400-00-00B", f"Given type {parts[3]} doesn't match {ATLAS_TYPE_PATHS[parts[1]]}")
        return atlas_type_view(item)
    return html_404


# ---- Ozone Recon fake -------------------------------------------------------------------------------------------------
# Three prefixes: /api/v1 is a Recon with Hadoop simple authentication that allows anonymous callers;
# /gateway/cdp-proxy/ozone-recon/api/v1 is Recon through Knox (Basic against the Ranger accounts or a Bearer JWT);
# /recon-1/api/v1 is an older Recon whose simple authentication requires user.name, without key listing, the storage
# distribution or the deleted-directory summary, and with the flat namespace summary shape. Recon does not filter by identity.
RECON_RATIS = {"replicationType": "RATIS", "replicationFactor": "THREE", "requiredNodes": 3}
RECON_EC = {"replicationType": "EC", "data": 6, "parity": 3, "ecChunkSize": 1048576, "codec": "RS", "requiredNodes": 9}
RECON_VOLUMES = [
    {"volume": "s3v", "owner": "hadoop", "admin": "hadoop", "quotaInBytes": -1, "quotaInNamespace": -1, "usedNamespace": 1, "creationTime": 1772000000000, "modificationTime": 1772000000000,
        "acls": [{"type": "USER", "name": "hadoop", "scope": "ACCESS", "aclList": ["ALL"]}], "metadata": {}},
    {"volume": "sales", "owner": "alice", "admin": "hadoop", "quotaInBytes": -1, "quotaInNamespace": -1, "usedNamespace": 2, "creationTime": 1772000000000, "modificationTime": 1780000000000,
        "acls": [{"type": "USER", "name": "alice", "scope": "ACCESS", "aclList": ["ALL"]}, {"type": "GROUP", "name": "analysts", "scope": "ACCESS", "aclList": ["READ", "LIST"]}], "metadata": {}},
    {"volume": "finance", "owner": "bob", "admin": "hadoop", "quotaInBytes": 10737418240, "quotaInNamespace": 1000, "usedNamespace": 1, "creationTime": 1772000000000, "modificationTime": 1772000000000,
        "acls": [{"type": "USER", "name": "bob", "scope": "ACCESS", "aclList": ["ALL"]}], "metadata": {"department": "finance"}},
]
RECON_BUCKETS = [
    {"volumeName": "s3v", "name": "landing", "bucketLayout": "OBJECT_STORE", "storageType": "DISK", "versioning": False, "owner": "hadoop", "quotaInBytes": -1, "quotaInNamespace": -1, "creationTime": 1772000000000, "modificationTime": 1793000000000,
        "acls": [{"type": "USER", "name": "hadoop", "scope": "ACCESS", "aclList": ["ALL"]}]},
    {"volumeName": "sales", "name": "orders", "bucketLayout": "FILE_SYSTEM_OPTIMIZED", "storageType": "DISK", "versioning": False, "owner": "alice", "quotaInBytes": -1, "quotaInNamespace": -1, "creationTime": 1772000000000, "modificationTime": 1793000000000,
        "acls": [{"type": "USER", "name": "alice", "scope": "ACCESS", "aclList": ["ALL"]}]},
    {"volumeName": "sales", "name": "archive", "bucketLayout": "FILE_SYSTEM_OPTIMIZED", "storageType": "ARCHIVE", "versioning": True, "owner": "alice", "quotaInBytes": -1, "quotaInNamespace": -1, "creationTime": 1772000000000, "modificationTime": 1772500000000,
        "replicationConfigInfo": RECON_EC, "acls": [{"type": "USER", "name": "alice", "scope": "ACCESS", "aclList": ["ALL"]}]},
    {"volumeName": "finance", "name": "ledger", "bucketLayout": "FILE_SYSTEM_OPTIMIZED", "storageType": "DISK", "versioning": False, "owner": "bob", "quotaInBytes": 5368709120, "quotaInNamespace": 500, "creationTime": 1772000000000, "modificationTime": 1792000000000,
        "acls": [{"type": "USER", "name": "bob", "scope": "ACCESS", "aclList": ["ALL"]}]},
]
RECON_KEYS = [  # path, size, replication, created
    ("/s3v/landing/upload.bin", 900, RECON_RATIS, 1793000000000),
    ("/sales/orders/README.md", 2048, RECON_RATIS, 1780000000000),
    ("/sales/orders/2026/01/orders.parquet", 52428800, RECON_RATIS, 1780100000000),
    ("/sales/orders/2026/02/orders.parquet", 61865984, RECON_RATIS, 1793000000000),
    ("/sales/archive/2019.tar", 1610612736, RECON_EC, 1772500000000),
    ("/finance/ledger/gl.csv", 3145728, RECON_RATIS, 1792000000000),
]
RECON_CLUSTER_STATE = {"pipelines": 4, "totalDatanodes": 3, "healthyDatanodes": 3, "containers": 120, "missingContainers": 0, "openContainers": 8, "deletedContainers": 2, "volumes": 3, "buckets": 4, "keys": 6,
    "keysPendingDeletion": 2, "deletedDirs": 1, "scmServiceId": "scm1", "omServiceId": "om1",
    "storageReport": {"capacity": 3298534883328, "used": 5184168588, "remaining": 3200000000000, "committed": 8589934592, "minimumFreeSpace": 32985348833, "reserved": 60000000000, "filesystemCapacity": 3400000000000, "filesystemUsed": 100000000000, "filesystemAvailable": 3300000000000}}
RECON_DATANODES = [{"datanodeUuid": f"dn-{i}", "hostName": f"dn{i}.example.com", "capacity": 1099511627776, "used": 1728056196, "remaining": 1066666666666, "committed": 2863311530, "minimumFreeSpace": 10995116277, "reserved": 20000000000,
    "filesystemCapacity": 1133333333333, "filesystemUsed": 33333333333, "filesystemAvailable": 1100000000000} for i in (1, 2, 3)]
RECON_OPEN = {"totalOpenKeys": 3, "totalReplicatedDataSize": 94371840, "totalUnreplicatedDataSize": 31457280}
RECON_DELETED = {"totalDeletedKeys": 2, "totalReplicatedDataSize": 6291456, "totalUnreplicatedDataSize": 2097152}
RECON_DELETED_DIRS = {"totalDeletedDirectories": 1}


def recon_replicated(size, config):
    return size * config["requiredNodes"] // (config.get("data") or 1) if config["replicationType"] == "EC" else size * config["requiredNodes"]


def recon_key_record(path, size, config, created):
    return {"key": path, "path": path, "size": size, "replicatedSize": recon_replicated(size, config), "replicationInfo": config, "creationTime": created, "modificationTime": created, "isKey": True}


def recon_dirs():
    found = set()
    for path, *_ in RECON_KEYS:
        parts = path.split("/")[1:]
        for depth in range(3, len(parts)):
            found.add("/" + "/".join(parts[:depth]))
    return sorted(found)


def recon_under(path):
    prefix = "" if path == "/" else path
    return [k for k in RECON_KEYS if k[0].startswith(prefix + "/")]


def recon_parent(path):
    return path.rsplit("/", 1)[0] or "/"


def recon_kind(path):
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "ROOT"
    if len(parts) == 1:
        return "VOLUME" if any(v["volume"] == parts[0] for v in RECON_VOLUMES) else "UNKNOWN"
    if len(parts) == 2:
        return "BUCKET" if any(b["volumeName"] == parts[0] and b["name"] == parts[1] for b in RECON_BUCKETS) else "UNKNOWN"
    if any(k[0] == path for k in RECON_KEYS):
        return "KEY"
    return "DIRECTORY" if path in recon_dirs() else "UNKNOWN"


def recon_bucket_record(b):
    under = recon_under(f"/{b['volumeName']}/{b['name']}")
    return {**b, "usedBytes": sum(k[1] for k in under), "usedNamespace": len(under) + len([d for d in recon_dirs() if d.startswith(f"/{b['volumeName']}/{b['name']}/")]), "snapshotUsedBytes": 0, "sourceVolume": None, "sourceBucket": None}


def recon_summary(path, flat):
    kind = recon_kind(path)
    if kind == "UNKNOWN":
        return {"status": "PATH_NOT_FOUND", "type": "UNKNOWN"} if flat else {"status": "PATH_NOT_FOUND", "path": path, "type": "UNKNOWN"}
    parts = [p for p in path.split("/") if p]
    under, dirs = recon_under(path), [d for d in recon_dirs() if path == "/" or d.startswith(path + "/")]
    if kind == "ROOT":
        stats, info = (len(RECON_VOLUMES), len(RECON_BUCKETS), len(dirs), len(under)), {}
    elif kind == "VOLUME":
        v = next(v for v in RECON_VOLUMES if v["volume"] == parts[0])
        stats, info = (-1, len([b for b in RECON_BUCKETS if b["volumeName"] == parts[0]]), len(dirs), len(under)), {**v, "name": v["volume"]}
    elif kind == "BUCKET":
        b = recon_bucket_record(next(b for b in RECON_BUCKETS if b["volumeName"] == parts[0] and b["name"] == parts[1]))
        stats, info = (-1, -1, len(dirs), len(under)), {**b, "metadata": {}}
    elif kind == "DIRECTORY":
        stats, info = (-1, -1, len(dirs), len(under)), {"name": parts[-1], "creationTime": min(k[3] for k in under), "modificationTime": max(k[3] for k in under), "metadata": {}}
    else:
        k = next(k for k in RECON_KEYS if k[0] == path)
        stats, info = (-1, -1, -1, 0), {"name": parts[-1], "dataSize": k[1], "replicationConfig": k[2], "creationTime": k[3], "modificationTime": k[3], "metadata": {}}
    if flat:
        return {"status": "OK", "type": kind, "numVolume": stats[0], "numBucket": stats[1], "numDir": stats[2], "numKey": stats[3]}
    return {"status": "OK", "path": path, "type": kind, "countStats": {"numVolume": stats[0], "numBucket": stats[1], "numDir": stats[2], "numKey": stats[3]}, "objectInfo": info}


def recon_sizes(keys, replica):
    return sum(k[1] for k in keys), (sum(recon_replicated(k[1], k[2]) for k in keys) if replica else -1)


def recon_du(path, files, replica):
    kind = recon_kind(path)
    if kind == "UNKNOWN":
        return {"status": "PATH_NOT_FOUND", "path": path, "size": 0, "sizeWithReplica": -1, "subPathCount": 0, "subPaths": [], "sizeDirectKey": 0}
    if kind == "KEY":
        k = next(k for k in RECON_KEYS if k[0] == path)
        return {"status": "OK", "path": path, "size": k[1], "sizeWithReplica": recon_replicated(k[1], k[2]) if replica else -1, "subPathCount": 0, "subPaths": [], "sizeDirectKey": 0}
    if kind == "ROOT":
        children = [(f"/{v['volume']}", False) for v in RECON_VOLUMES]
    elif kind == "VOLUME":
        children = [(f"/{b['volumeName']}/{b['name']}", False) for b in RECON_BUCKETS if f"/{b['volumeName']}" == path]
    else:
        children = [(d, False) for d in recon_dirs() if recon_parent(d) == path] + ([(k[0], True) for k in RECON_KEYS if recon_parent(k[0]) == path] if files else [])
    sub = []
    for child, is_key in children:
        keys = [k for k in RECON_KEYS if k[0] == child] if is_key else recon_under(child)
        size, replicated = recon_sizes(keys, replica)
        sub.append({"path": child, "size": size, "sizeWithReplica": replicated, "isKey": is_key})
    sub.sort(key=lambda s: -s["size"])
    size, replicated = recon_sizes(recon_under(path), replica)
    direct = sum(k[1] for k in RECON_KEYS if recon_parent(k[0]) == path) if kind in ("BUCKET", "DIRECTORY") else 0
    return {"status": "OK", "path": path, "size": size, "sizeWithReplica": replicated, "subPathCount": len(sub), "subPaths": sub, "sizeDirectKey": direct}


def recon_quota(path):
    kind = recon_kind(path)
    parts = [p for p in path.split("/") if p]
    if kind == "UNKNOWN":
        return {"status": "PATH_NOT_FOUND", "allowed": 0, "used": 0}
    if kind in ("DIRECTORY", "KEY"):
        return {"status": "TYPE_NOT_APPLICABLE", "allowed": 0, "used": 0}
    if kind == "ROOT":
        allowed = sum(v["quotaInBytes"] for v in RECON_VOLUMES if v["quotaInBytes"] > 0) or -1
    elif kind == "VOLUME":
        allowed = next(v["quotaInBytes"] for v in RECON_VOLUMES if v["volume"] == parts[0])
    else:
        allowed = next(b["quotaInBytes"] for b in RECON_BUCKETS if b["volumeName"] == parts[0] and b["name"] == parts[1])
    return {"status": "OK", "allowed": allowed, "used": sum(k[1] for k in recon_under(path))}


def recon_bin(size):
    return 0 if size <= 1024 else min(41, (size - 1).bit_length() - 10)


def recon_dist(path):
    kind = recon_kind(path)
    if kind == "UNKNOWN":
        return {"status": "PATH_NOT_FOUND", "dist": []}
    if kind == "KEY":
        return {"status": "TYPE_NOT_APPLICABLE", "dist": []}
    dist = [0] * 42
    for k in recon_under(path):
        dist[recon_bin(k[1])] += 1
    return {"status": "OK", "dist": dist}


def recon_file_counts(volume, bucket, file_size):
    rows = {}
    for path, size, *_ in RECON_KEYS:
        parts = path.split("/")[1:]
        rows[(parts[0], parts[1], 1 << (10 + recon_bin(size)))] = rows.get((parts[0], parts[1], 1 << (10 + recon_bin(size))), 0) + 1
    out = [{"volume": v, "bucket": b, "fileSize": s, "count": n} for (v, b, s), n in rows.items()
        if (not volume or v == volume) and (not bucket or b == bucket) and (not file_size or s == 1 << (10 + recon_bin(file_size)))]
    return out


def recon_after(items, key, prev):
    if not prev:
        return items
    names = [key(i) for i in items]
    return items[names.index(prev) + 1:] if prev in names else [i for i in items if key(i) > prev]


@app.api_route("/api/v1/{rest:path}", methods=["GET"])
async def recon_direct(rest: str, request: Request):
    return recon_api(rest, request, features=True)


@app.api_route("/gateway/cdp-proxy/ozone-recon/api/v1/{rest:path}", methods=["GET"])
async def recon_knox(rest: str, request: Request):
    if ranger_user(request) is None:
        return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Knox"'}, content="Authentication required")
    return recon_api(rest, request, features=True)


@app.api_route("/recon-1/api/v1/{rest:path}", methods=["GET"])
async def recon_old(rest: str, request: Request):
    if not request.query_params.get("user.name"):
        return Response(status_code=401, content="<html><body><h1>HTTP Status 401 - Authentication required</h1></body></html>", media_type="text/html")
    return recon_api(rest, request, features=False)


def recon_api(rest, request, features):
    from datetime import datetime as _datetime, timezone as _timezone
    query = dict(request.query_params)
    html_404 = Response(status_code=404, content="<html><body><h1>HTTP Status 404 - Not Found</h1></body></html>", media_type="text/html")
    limit = int(query.get("limit", 1000) or 1000)
    prev = query.get("prevKey", "")
    rest = rest.strip("/")
    if rest == "volumes":
        items = recon_after(sorted(RECON_VOLUMES, key=lambda v: v["volume"]), lambda v: v["volume"], prev)
        return {"totalCount": len(RECON_VOLUMES), "volumes": items[:limit]}
    if rest == "buckets":
        items = sorted([recon_bucket_record(b) for b in RECON_BUCKETS if not query.get("volume") or b["volumeName"] == query["volume"]], key=lambda b: (b["volumeName"], b["name"]))
        items = recon_after(items, lambda b: b["name"], prev)
        return {"totalCount": len(items), "buckets": items[:limit]}
    if rest == "keys/open/summary":
        return RECON_OPEN
    if rest == "keys/deletePending/summary":
        return RECON_DELETED
    if rest == "keys/deletePending/dirs/summary" and features:
        return RECON_DELETED_DIRS
    if rest == "keys/listKeys" and features:
        prefix = query.get("startPrefix", "/")
        if len([p for p in prefix.split("/") if p]) < 2:
            return Response(status_code=400)
        keys = sorted(k for k in RECON_KEYS if k[0].startswith(prefix))
        if query.get("replicationType"):
            keys = [k for k in keys if k[2]["replicationType"] == query["replicationType"]]
        if query.get("keySize"):
            keys = [k for k in keys if k[1] >= int(query["keySize"])]
        if query.get("creationDate"):
            since = _datetime.strptime(query["creationDate"], "%m-%d-%Y %H:%M:%S").replace(tzinfo=_timezone.utc).timestamp() * 1000
            keys = [k for k in keys if k[3] >= since]
        records = recon_after([recon_key_record(*k) for k in keys], lambda k: k["key"], prev)[:limit]
        if not records:
            return Response(status_code=204)
        return {"status": "OK", "path": prefix, "replicatedDataSize": sum(r["replicatedSize"] for r in records), "unReplicatedDataSize": sum(r["size"] for r in records), "lastKey": records[-1]["key"], "keys": records}
    if rest.startswith("namespace/"):
        path = query.get("path", "")
        if not path:
            return Response(status_code=400)
        path = path if path == "/" else path.rstrip("/")
        if rest == "namespace/summary":
            return recon_summary(path, flat=not features)
        if rest == "namespace/usage":
            return recon_du(path, query.get("files") == "true", query.get("replica") == "true")
        if rest == "namespace/quota":
            return recon_quota(path)
        if rest == "namespace/dist":
            return recon_dist(path)
    if rest == "clusterState":
        return RECON_CLUSTER_STATE
    if rest == "utilization/fileCount":
        return recon_file_counts(query.get("volume"), query.get("bucket"), int(query.get("fileSize", 0) or 0))
    if rest == "storageDistribution" and features:
        total = sum(k[1] for k in RECON_KEYS)
        return {"globalStorage": {"totalFileSystemCapacity": 3400000000000, "totalReservedSpace": 60000000000, "totalOzoneCapacity": 3298534883328, "totalOzoneUsedSpace": 5184168588, "totalOzoneFreeSpace": 3200000000000, "totalOzoneCommittedSpace": 8589934592, "totalMinimumFreeSpace": 32985348833},
            "globalNamespace": {"totalUsedSpace": total, "totalKeys": len(RECON_KEYS)},
            "usedSpaceBreakdown": {"openKeyBytes": {"openKeyAndFileBytes": 31457280, "multipartOpenKeyBytes": 0, "totalOpenKeyBytes": 31457280}, "finalizedKeyBytes": total},
            "dataNodeUsage": RECON_DATANODES}
    return html_404


# ---- CDP control plane fake: Cloudera Lakehouse Optimizer ----------------------------------------------------------
# Signed POSTs as the cdp CLI sends them: x-altus-auth carries base64url(JSON{access_key_id, auth_method}) "." base64url(
# signature) over "METHOD\ncontent-type\nx-altus-date\npath\nauth_method". One Ed25519 API key is accepted; its seed is
# fixed so tests can hold the matching private key. Errors follow the control plane's {"code", "message"} shape.
CDP_ACCESS_KEY_ID = "e6a3f9c1-daedalus-test-key"
CDP_SEED = bytes(range(32))
CDP_ENVIRONMENTS = [
    {"environmentName": "prod-env", "environmentCrn": "crn:cdp:environments:us-west-1:tenant:environment:prod", "isCloEnabled": True, "datahubName": "prod-clo", "datahubCrn": "crn:cdp:datahub:us-west-1:tenant:cluster:clo-prod", "cloudPlatform": "AWS", "status": "AVAILABLE"},
    {"environmentName": "dev-env", "environmentCrn": "crn:cdp:environments:us-west-1:tenant:environment:dev", "isCloEnabled": False, "datahubName": None, "datahubCrn": None, "cloudPlatform": "AWS", "status": None},
    {"environmentName": "eu-env", "environmentCrn": "crn:cdp:environments:eu-1:tenant:environment:eu", "isCloEnabled": True, "datahubName": "eu-clo", "datahubCrn": "crn:cdp:datahub:eu-1:tenant:cluster:clo-eu", "cloudPlatform": "AZURE", "status": "AVAILABLE"},
]
CDP_PROD = "crn:cdp:datahub:us-west-1:tenant:cluster:clo-prod"
CDP_EU = "crn:cdp:datahub:eu-1:tenant:cluster:clo-eu"
CDP_TABLES = {  # datahub → namespace → table → (policies, status, last execution)
    CDP_PROD: {
        "sales": {"orders": (["daily-compaction"], "SUCCESS", 1793005000000), "customers": (["daily-compaction", "weekly-expire-snapshots"], "WARNING", 1792900000000)},
        "finance": {"ledger": (["weekly-expire-snapshots"], "USER_PAUSED", 1790000000000)},
    },
    CDP_EU: {"marketing": {}},
}
CDP_POLICIES = {  # name → (default, scope, created, arguments)
    "daily-compaction": (False, "Namespace", 1772000000000, {"actions": ["rewrite_data_files"], "schedule": "0 2 * * *", "timezone": "UTC", "targetFileSizeBytes": 536870912}),
    "weekly-expire-snapshots": (True, "Catalog", 1770000000000, {"actions": ["expire_snapshots", "remove_orphan_files"], "schedule": "0 3 * * 0", "timezone": "UTC", "retainLast": 5}),
    "monthly-orphan-cleanup": (False, "Namespace", 1785000000000, {"actions": ["remove_orphan_files"], "schedule": "0 4 1 * *", "timezone": "UTC"}),
}
CDP_TASKS = {
    "sales": [
        {"status": "COMPLETED", "taskId": "6b1a0e2c-0000-4000-8000-000000000001", "policy": "daily-compaction", "catalog": "spark_catalog", "namespace": "sales", "table": "orders", "createdAt": 1793005000000, "details": {"action": "rewrite_data_files", "rewrittenFiles": 42, "addedFiles": 3, "durationSeconds": 184}},
        {"status": "COMPLETED", "taskId": "6b1a0e2c-0000-4000-8000-000000000002", "policy": "daily-compaction", "catalog": "spark_catalog", "namespace": "sales", "table": "customers", "createdAt": 1792900000000, "details": {"action": "rewrite_data_files", "rewrittenFiles": 7, "addedFiles": 1, "durationSeconds": 51}},
        {"status": "FAILED", "taskId": "6b1a0e2c-0000-4000-8000-000000000003", "policy": "weekly-expire-snapshots", "catalog": "spark_catalog", "namespace": "sales", "table": "customers", "createdAt": 1792850000000, "details": {"action": "expire_snapshots", "error": "Snapshot 8812 is referenced by a branch"}},
        {"status": "SUBMITTED", "taskId": "6b1a0e2c-0000-4000-8000-000000000004", "policy": "daily-compaction", "catalog": "spark_catalog", "namespace": "sales", "table": "orders", "createdAt": 1793090000000, "details": {"action": "rewrite_data_files"}},
    ],
    "finance": [],
}


def cdp_public_key():
    from cryptography.hazmat.primitives.asymmetric import ed25519
    return ed25519.Ed25519PrivateKey.from_private_bytes(CDP_SEED).public_key()


def cdp_error(status, code, message):
    return JSONResponse({"code": code, "message": message}, status_code=status)


def cdp_authenticated(request):
    header, date = request.headers.get("x-altus-auth", ""), request.headers.get("x-altus-date", "")
    metadata, _, signature = header.partition(".")
    try:
        claims = json.loads(base64.urlsafe_b64decode(metadata + "=" * (-len(metadata) % 4)))
        if claims.get("access_key_id") != CDP_ACCESS_KEY_ID or claims.get("auth_method") != "ed25519v1" or not date:
            return False
        to_sign = "\n".join([request.method.upper(), request.headers.get("content-type", ""), date, request.url.path, "ed25519v1"])
        cdp_public_key().verify(base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)), to_sign.encode("utf-8"))
        return True
    except Exception:
        return False


def cdp_b64(value):
    return base64.b64encode(json.dumps(value).encode()).decode()


def cdp_table_status(policies, status, last):
    return {"status": status, "policies": policies, "lastExecutionEpoch": last}


@app.post("/api/v1/lakehouseopt/{operation}")
async def cdp_lakehouseopt(operation: str, request: Request):
    if not cdp_authenticated(request):
        return cdp_error(401, "UNAUTHENTICATED", "The request signature is invalid or the API key is unknown")
    try:
        body = await request.json()
    except ValueError:
        return cdp_error(400, "INVALID_ARGUMENT", "Request body must be JSON")
    body = body or {}
    if operation == "listEnvironments":
        size = int(body.get("pageSize") or 100)
        start = 0 if body.get("pageToken") in (None, "", "ALL") else int(body["pageToken"])
        page = CDP_ENVIRONMENTS[start:start + size]
        out = {"environments": page, "totalEnvironments": len(CDP_ENVIRONMENTS)}
        if start + size < len(CDP_ENVIRONMENTS):
            out["nextPageToken"] = str(start + size)
        return out
    crn = body.get("datahubCrn")
    if not crn:
        return cdp_error(400, "INVALID_ARGUMENT", "datahubCrn is required")
    if crn not in CDP_TABLES:
        return cdp_error(404, "NOT_FOUND", f"Data Hub {crn} was not found or is not a Lakehouse Optimizer Data Hub")
    namespaces = CDP_TABLES[crn]

    def need_namespace():
        ns = body.get("namespace")
        if ns not in namespaces:
            return None, cdp_error(404, "NOT_FOUND", f"Namespace {ns} does not exist in catalog")
        return ns, None

    def need_policy():
        name = body.get("policyName")
        if name not in CDP_POLICIES:
            return None, cdp_error(404, "NOT_FOUND", f"Policy {name} does not exist")
        return name, None

    def tables_with(policy):
        return [(ns, t) for ns, tables in namespaces.items() for t, (policies, *_rest) in tables.items() if policy in policies]

    if operation == "getNamespaces":
        return {"namespaces": sorted(namespaces)}
    if operation == "getTableNames":
        ns, err = need_namespace()
        return err or {"tables": sorted(namespaces[ns])}
    if operation == "listTables":
        ns, err = need_namespace()
        return err or {"tables": [{"status": st, "namespace": ns, "tableName": t, "policies": pol, "lastExecutionTime": last} for t, (pol, st, last) in sorted(namespaces[ns].items())]}
    if operation == "listPolicies":
        ns = body.get("namespace")
        if ns and ns not in namespaces:
            return cdp_error(404, "NOT_FOUND", f"Namespace {ns} does not exist in catalog")
        out = []
        for name, (default, scope, created, _args) in CDP_POLICIES.items():
            tables = [(n, t) for n, t in tables_with(name) if not ns or n == ns]
            if ns and not tables:
                continue
            runs = [k for k in CDP_TASKS.get(ns, []) or sum(CDP_TASKS.values(), []) if k["policy"] == name]
            out.append({"status": "UNAVAILABLE" if not tables else "ERROR" if any(k["status"] == "FAILED" for k in runs) else "SUCCESS", "policyName": name, "taskCount": len(runs), "tableCount": len(tables),
                "creationTime": created, "lastExecutionTime": max((k["createdAt"] for k in runs), default=0), "isDefault": default})
        return {"policies": out}
    if operation == "getPolicyNames":
        ns = body.get("namespace")
        if ns != "*" and ns not in namespaces:
            return cdp_error(404, "NOT_FOUND", f"Namespace {ns} does not exist in catalog")
        return {"policyNames": sorted({p for n, tables in namespaces.items() if ns == "*" or n == ns for pol, *_ in tables.values() for p in pol})}
    if operation == "getPolicy":
        name, err = need_policy()
        if err:
            return err
        default, scope, created, args = CDP_POLICIES[name]
        tables = tables_with(name)
        associations = []
        for ns in sorted({n for n, _ in tables}):
            rows = [{"name": t, "namespace": ns, "taskCount": len([k for k in CDP_TASKS.get(ns, []) if k["policy"] == name and k["table"] == t]), "lastExecutionTime": namespaces[ns][t][2], "version": "v1-" + name, "status": "PAUSED" if "PAUSED" in namespaces[ns][t][1] else "SUCCESS"} for n, t in sorted(tables) if n == ns]
            associations.append({"namespace": ns, "status": "SUCCESS" if all(r["status"] == "SUCCESS" for r in rows) else "USER_PAUSED", "tableAssociations": rows})
        runs = [k for k in sum(CDP_TASKS.values(), []) if k["policy"] == name]
        return {"versions": ["v1-" + name], "policyDetail": {"version": "v1-" + name, "arguments": cdp_b64(args), "scope": scope, "associations": associations, "tableCount": len(tables), "creationTime": created, "lastExecutionTime": max((k["createdAt"] for k in runs), default=0)}}
    if operation == "getTablePolicies":
        ns, err = need_namespace()
        if err:
            return err
        table = body.get("tableName")
        if table not in namespaces[ns]:
            return cdp_error(404, "NOT_FOUND", f"Table {ns}.{table} does not exist")
        policies, status, last = namespaces[ns][table]
        return {"policies": [{"status": status, "policyName": p, "taskCount": len([k for k in CDP_TASKS.get(ns, []) if k["policy"] == p and k["table"] == table]), "lastExecutionTime": last} for p in policies]}
    if operation == "getTableStatusDetails":
        ns, err = need_namespace()
        if err:
            return err
        table, policy = body.get("tableName"), body.get("policyName")
        if table not in namespaces[ns]:
            return cdp_error(404, "NOT_FOUND", f"Table {ns}.{table} does not exist")
        if body.get("status") not in ("UNAVAILABLE", "SUCCESS", "ERROR", "PAUSED"):
            return cdp_error(400, "INVALID_ARGUMENT", "status must be one of UNAVAILABLE, SUCCESS, ERROR, PAUSED")
        policies, status, last = namespaces[ns][table]
        if "PAUSED" in status:
            return {"pausedTable": {"message": "Table paused by user bob", "details": {"pausedSince": "2026-09-21T00:00:00Z", "reasons": ["Quarter-end close in progress"]}}}
        runs = [k for k in CDP_TASKS.get(ns, []) if k["table"] == table and k["policy"] == policy and k["status"] in ("COMPLETED", "FAILED")]
        if not runs:
            return {}
        recent = max(runs, key=lambda k: k["createdAt"])
        return {"recentTask": {"actions": [{"action": recent["details"]["action"], "status": recent["status"]}], "policyName": policy, "tableName": table, "lastExecutionTime": recent["createdAt"]}}
    if operation == "getAssociations":
        name, err = need_policy()
        return err or {"associations": [{"namespace": ns, "tables": sorted(t for n, t in tables_with(name) if n == ns)} for ns in sorted({n for n, _ in tables_with(name)})]}
    if operation == "getAssociatedNamespaces":
        name, err = need_policy()
        return err or {"associatedNamespaces": [{"namespace": ns, "isAssociated": any(n == ns for n, _ in tables_with(name))} for ns in sorted(namespaces)]}
    if operation == "getAssociatedTables":
        name, err = need_policy()
        return err or {"associatedTables": [{"namespace": ns, "tables": [{"tableName": t, "isAssociated": (ns, t) in tables_with(name)} for t in sorted(tables)]} for ns, tables in sorted(namespaces.items())]}
    if operation == "getAssociationDetails":
        direct = [{"namespace": ns, "status": "SUCCESS" if all(st == "SUCCESS" for _, st, _ in tables.values()) else "WARNING",
            "tables": [{"tableName": t, "policies": pol, "lastExecutionEpoch": last, "status": st} for t, (pol, st, last) in sorted(tables.items())]} for ns, tables in sorted(namespaces.items()) if tables]
        star = [{"catalog": "spark_catalog", "status": "SUCCESS", "namespaces": [{"namespace": ns, "status": "SUCCESS", "policies": ["weekly-expire-snapshots"]} for ns in sorted(namespaces)]}]
        return {"directAssociation": direct, "starAssociation": star}
    if operation == "listTasks":
        ns, err = need_namespace()
        if err:
            return err
        tasks = sorted(CDP_TASKS.get(ns, []), key=lambda k: -k["createdAt"])
        size = int(body.get("pageSize") or 100)
        start = int(body.get("pageToken") or 0)
        page = [{**k, "details": cdp_b64(k["details"])} for k in tasks[start:start + size]]
        out = {"tasks": page}
        if start + size < len(tasks):
            out["nextPageToken"] = str(start + size)
        return out
    return cdp_error(404, "NOT_FOUND", f"Unknown operation {operation}")
