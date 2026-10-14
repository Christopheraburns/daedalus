"""File management on HDFS (and Ozone via HttpFS) through the WebHDFS REST API: list, inspect, read, write, copy, move and delete."""
import base64
import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from . import ToolContext, pack_tool

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix            WebHDFS path prefix on the connection, default "/webhdfs/v1"
#                     (Knox: "/gateway/cdp-proxy-api/webhdfs/v1")
#   follow_redirects  true to follow NameNode 307 redirects to DataNodes for OPEN/CREATE.
#                     HttpFS needs no redirects and is the recommended front door; a
#                     followed redirect leaves the connection's approved origin.
#   pseudo_auth       true to send user.name=<caller> for clusters without Kerberos
#   allow_recursive_delete  true to permit deleting non-empty directories
#   max_download_bytes      default 262144; results stay well under the 1 MiB cap
#   max_upload_bytes        default 1048576 (decoded)
#   max_copy_bytes          default 67108864; copies stream through the executor
DEFAULTS = {"prefix": "/webhdfs/v1", "follow_redirects": False, "pseudo_auth": False, "allow_recursive_delete": False,
    "max_download_bytes": 256 * 1024, "max_upload_bytes": 1024 * 1024, "max_copy_bytes": 64 * 1024 * 1024}
PATH = re.compile(r"^/(?:[^\x00-\x1f\x7f]*)$")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_path(path):
    if not PATH.match(path or "") or any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("Paths must be absolute HDFS paths without . or .. segments")
    return path.rstrip("/") or "/"


def remote_error(response):
    try:
        detail = response.json()["RemoteException"]
        return f"{detail.get('exception', 'Error')}: {detail.get('message', '')}"[:400]
    except (ValueError, KeyError, TypeError):
        return f"HTTP {response.status_code} from the HDFS endpoint"


def call(ctx, method, path, op, params=None, content=None, stream=False):
    """One WebHDFS operation. Redirects (NameNode → DataNode) are followed only when configured,
    reusing the connection's credentials, because the target host is outside the approved origin."""
    query = {"op": op, **{k: v for k, v in (params or {}).items() if v is not None}}
    if setting(ctx, "pseudo_auth"):
        query["user.name"] = ctx.caller.username
    url = setting(ctx, "prefix").rstrip("/") + quote(check_path(path), safe="/")
    headers = {"Content-Type": "application/octet-stream"} if content is not None else {}
    with ctx.client(timeout=30.0) as client:
        response = client.request(method, url, params=query, content=content, headers=headers)
        if response.status_code in (301, 302, 307) and "location" in response.headers:
            if not setting(ctx, "follow_redirects"):
                raise ValueError("The endpoint redirected (NameNode-style WebHDFS); use HttpFS or set follow_redirects in the tool configuration")
            response = httpx.request(method, response.headers["location"], content=content, headers={**dict(client.headers), **headers}, timeout=30.0, trust_env=False)
    if response.status_code >= 400:
        raise ValueError(remote_error(response))
    return response


def status_entry(status):
    return {"name": status.get("pathSuffix", ""), "type": status.get("type", "").lower(), "length": status.get("length", 0),
        "modified": datetime.fromtimestamp(status.get("modificationTime", 0) / 1000, timezone.utc).isoformat(timespec="seconds"),
        "owner": status.get("owner", ""), "group": status.get("group", ""), "permission": status.get("permission", "")}


@pack_tool(effect="read", requires_connection=True)
def list_directory(ctx: ToolContext, path: str, limit: int = 200) -> dict:
    """List the files and subdirectories directly under an HDFS directory, with size, owner and modification time."""
    entries = call(ctx, "GET", path, "LISTSTATUS").json()["FileStatuses"]["FileStatus"]
    limit = max(1, min(limit, 1000))
    return {"path": check_path(path), "entries": [status_entry(s) for s in entries[:limit]], "total": len(entries), "truncated": len(entries) > limit}


@pack_tool(effect="read", requires_connection=True)
def get_file_status(ctx: ToolContext, path: str) -> dict:
    """Describe one HDFS file or directory: type, size, owner, group, permission and modification time."""
    status = call(ctx, "GET", path, "GETFILESTATUS").json()["FileStatus"]
    return {"path": check_path(path), **status_entry(status)}


@pack_tool(effect="write", requires_connection=True)
def make_directory(ctx: ToolContext, path: str, permission: str = "") -> dict:
    """Create an HDFS directory, including missing parents. Permission is octal such as 750."""
    if permission and not re.fullmatch(r"[0-7]{3,4}", permission):
        raise ValueError("Permission must be octal, for example 750")
    created = call(ctx, "PUT", path, "MKDIRS", {"permission": permission or None}).json().get("boolean", False)
    return {"path": check_path(path), "created": bool(created)}


@pack_tool(effect="write", requires_connection=True)
def move(ctx: ToolContext, source: str, destination: str) -> dict:
    """Move or rename an HDFS file or directory. The destination must not already exist."""
    moved = call(ctx, "PUT", source, "RENAME", {"destination": check_path(destination)}).json().get("boolean", False)
    if not moved:
        raise ValueError("HDFS refused the move; the destination may exist or the source may be missing")
    return {"source": check_path(source), "destination": check_path(destination), "moved": True}


@pack_tool(effect="write", requires_connection=True)
def delete(ctx: ToolContext, path: str, recursive: bool = False) -> dict:
    """Delete an HDFS file or an empty directory. Deleting a directory with contents requires recursive=true and must be enabled for this tool."""
    if recursive and not setting(ctx, "allow_recursive_delete"):
        raise ValueError("Recursive delete is disabled for this tool; an administrator can enable allow_recursive_delete in its configuration")
    deleted = call(ctx, "DELETE", path, "DELETE", {"recursive": "true" if recursive else "false"}).json().get("boolean", False)
    return {"path": check_path(path), "deleted": bool(deleted)}


@pack_tool(effect="read", requires_connection=True)
def download_file(ctx: ToolContext, path: str, offset: int = 0, max_bytes: int = 65536) -> dict:
    """Read the contents of an HDFS file. Text is returned as UTF-8, other data as base64; large files are read in slices with offset and max_bytes."""
    limit = max(1, min(max_bytes, setting(ctx, "max_download_bytes")))
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    response = call(ctx, "GET", path, "OPEN", {"offset": offset, "length": limit + 1})
    data = response.content
    truncated = len(data) > limit
    data = data[:limit]
    try:
        content, encoding = data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        content, encoding = base64.b64encode(data).decode(), "base64"
    return {"path": check_path(path), "offset": offset, "length": len(data), "truncated": truncated, "encoding": encoding, "content": content}


def decode_upload(ctx, content, encoding):
    if encoding not in {"utf-8", "base64"}:
        raise ValueError("encoding must be utf-8 or base64")
    try:
        data = base64.b64decode(content, validate=True) if encoding == "base64" else content.encode("utf-8")
    except ValueError as exc:
        raise ValueError("content is not valid base64") from exc
    if len(data) > setting(ctx, "max_upload_bytes"):
        raise ValueError(f"Uploads are limited to {setting(ctx, 'max_upload_bytes')} bytes for this tool")
    return data


@pack_tool(effect="write", requires_connection=True)
def upload_file(ctx: ToolContext, path: str, content: str, overwrite: bool = False, encoding: str = "utf-8") -> dict:
    """Write a file to HDFS from inline content (UTF-8 text, or base64 for binary data). Fails if the file exists unless overwrite=true."""
    data = decode_upload(ctx, content, encoding)
    call(ctx, "PUT", path, "CREATE", {"overwrite": "true" if overwrite else "false", "data": "true"}, content=data)
    return {"path": check_path(path), "length": len(data), "overwritten": overwrite}


@pack_tool(effect="write", requires_connection=True)
def copy(ctx: ToolContext, source: str, destination: str, overwrite: bool = False) -> dict:
    """Copy an HDFS file to a new path by streaming it through the server. Fails if the destination exists unless overwrite=true."""
    size = get_file_status(ctx, source)
    if size["type"] != "file":
        raise ValueError("Only files can be copied; copy directory contents one file at a time")
    if size["length"] > setting(ctx, "max_copy_bytes"):
        raise ValueError(f"Copies are limited to {setting(ctx, 'max_copy_bytes')} bytes for this tool")
    data = call(ctx, "GET", source, "OPEN").content
    call(ctx, "PUT", destination, "CREATE", {"overwrite": "true" if overwrite else "false", "data": "true"}, content=data)
    return {"source": check_path(source), "destination": check_path(destination), "length": len(data)}
