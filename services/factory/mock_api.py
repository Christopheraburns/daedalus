"""Two unrelated, deterministic development fixtures. No customer data."""
import threading

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(title="Daedalus fixtures")
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


@app.get("/fixture/counters")
def counters():
    return dict(calls)


# ---- WebHDFS fake -------------------------------------------------------------
# In-memory HDFS for tests and the playground. /webhdfs/v1 behaves like HttpFS (data
# flows directly); /webhdfs-nn/v1 behaves like a NameNode (OPEN and CREATE answer with a
# 307 redirect to the HttpFS path, as a real NameNode redirects to a DataNode).
import time
from fastapi import Response
from fastapi.responses import JSONResponse

fs_lock = threading.Lock()


def fs_entry(kind, content=b"", owner="hdfs"):
    return {"type": kind, "content": content, "owner": owner, "mtime": int(time.time() * 1000)}


fs = {"/": fs_entry("DIRECTORY"), "/data": fs_entry("DIRECTORY"), "/data/readme.txt": fs_entry("FILE", b"Hello from the HDFS fixture.\n")}


def fs_status(entry, suffix):
    directory = entry["type"] == "DIRECTORY"
    return {"pathSuffix": suffix, "type": entry["type"], "length": 0 if directory else len(entry["content"]), "modificationTime": entry["mtime"], "accessTime": entry["mtime"],
        "owner": entry["owner"], "group": "supergroup", "permission": "755" if directory else "644", "replication": 0 if directory else 1, "blockSize": 0 if directory else 134217728}


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
    body = await request.body() if request.method == "PUT" else b""
    if redirects and op in {"OPEN", "CREATE"} and query.get("data") != "true":
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
        return remote_exception(400, "UnsupportedOperationException", f"Unsupported operation: {op}")
