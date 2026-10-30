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
