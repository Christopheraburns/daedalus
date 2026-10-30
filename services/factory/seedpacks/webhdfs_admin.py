"""Advanced file management on HDFS or Ozone over WebHDFS: ownership, permissions and ACLs, extended attributes,
snapshots, quotas and space usage, appends and concatenation. Extends the built-in hdfs pack, which covers
listing, reading, writing, copying, moving and deleting."""
import base64
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "webhdfs"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix            WebHDFS path prefix on the connection, default "/webhdfs/v1" (Knox: "/gateway/cdp-proxy-api/webhdfs/v1")
#   follow_redirects  true to follow NameNode 307 redirects to DataNodes for APPEND; HttpFS needs none
#   pseudo_auth       true to send user.name=<caller> for clusters without Kerberos
#   max_upload_bytes  default 1048576 (decoded) for append
DEFAULTS = {"prefix": "/webhdfs/v1", "follow_redirects": False, "pseudo_auth": False, "max_upload_bytes": 1024 * 1024}
PATH = re.compile(r"^/(?:[^\x00-\x1f\x7f]*)$")
OCTAL = re.compile(r"^[0-7]{3,4}$")
NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.@-]{0,63}$")
SNAPSHOT = re.compile(r"^[^/\x00-\x1f\x7f]{1,255}$")
XATTR = re.compile(r"^(user|trusted|security|system|raw)\.[^\x00-\x1f\x7f=]{1,200}$")
FSACTION = re.compile(r"^[r-][w-][x-]$")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_path(path):
    if not PATH.match(path or "") or any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("Paths must be absolute HDFS paths without . or .. segments")
    return path.rstrip("/") or "/"


def check_snapshot(name):
    if not SNAPSHOT.match(name or ""):
        raise ValueError("A snapshot name is 1 to 255 characters without slashes")
    return name


def check_xattr(name):
    if not XATTR.match(name or ""):
        raise ValueError("An extended attribute name is a namespace (user, trusted, security, system or raw), a dot, and a name, for example user.owner_team")
    return name


def remote_error(response):
    try:
        detail = response.json()["RemoteException"]
        return f"{detail.get('exception', 'Error')}: {detail.get('message', '')}"[:400]
    except (ValueError, KeyError, TypeError):
        return f"HTTP {response.status_code} from the HDFS endpoint"


def call(ctx, method, path, op, params=None, content=None):
    """One WebHDFS operation. Repeated parameters are given as lists. NameNode-style redirects are followed
    only when configured, because the DataNode is outside the connection's approved origin."""
    query = [("op", op)]
    for key, value in (params or {}).items():
        for item in value if isinstance(value, list) else [value]:
            if item is not None and item != "":
                query.append((key, item))
    if setting(ctx, "pseudo_auth"):
        query.append(("user.name", ctx.caller.username))
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
    return response.json() if response.content else {}


def status_entry(status):
    return {"name": status.get("pathSuffix", ""), "type": status.get("type", "").lower(), "length": status.get("length", 0),
        "modified": iso(status.get("modificationTime", 0)), "owner": status.get("owner", ""), "group": status.get("group", ""), "permission": status.get("permission", "")}


def iso(millis):
    return datetime.fromtimestamp(millis / 1000, timezone.utc).isoformat(timespec="seconds")


def millis(text):
    """An ISO 8601 timestamp (or epoch milliseconds) as WebHDFS epoch milliseconds; empty means leave unchanged."""
    if not text:
        return -1
    if text.isdigit():
        return int(text)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{text!r} is not an ISO 8601 timestamp such as 2026-01-31T09:00:00Z") from exc
    return int((parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp() * 1000)


def decode_value(encoded):
    """WebHDFS encodes attribute values as "text", 0x<hex> or 0s<base64>; return text when it is UTF-8, else base64."""
    if encoded.startswith("0x"):
        raw = bytes.fromhex(encoded[2:])
    elif encoded.startswith("0s"):
        raw = base64.b64decode(encoded[2:])
    else:
        raw = encoded.strip('"').encode()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return base64.b64encode(raw).decode(), "base64"


@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the endpoint speaks WebHDFS by reading the root directory's status."""
    status = call(ctx, "GET", "/", "GETFILESTATUS")["FileStatus"]
    return {"message": f"WebHDFS answered; / is owned by {status.get('owner', '?')}"}


# ---- Space, quotas and summaries ------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_content_summary(ctx: ToolContext, path: str) -> dict:
    """Report how much a directory holds: file and directory counts, total bytes, and quota usage if quotas are set."""
    summary = call(ctx, "GET", path, "GETCONTENTSUMMARY")["ContentSummary"]
    return {"path": check_path(path), "files": summary.get("fileCount", 0), "directories": summary.get("directoryCount", 0),
        "bytes": summary.get("length", 0), "space_consumed": summary.get("spaceConsumed", 0),
        "quota": summary.get("quota", -1), "space_quota": summary.get("spaceQuota", -1)}


@pack_tool(effect="read", requires_connection=True)
def get_quota_usage(ctx: ToolContext, path: str) -> dict:
    """Report a directory's name and space quotas and how much of each is used; -1 means no quota. Cheaper than a content summary on large trees."""
    usage = call(ctx, "GET", path, "GETQUOTAUSAGE")["QuotaUsage"]
    return {"path": check_path(path), "files_and_directories": usage.get("fileAndDirectoryCount", 0), "quota": usage.get("quota", -1),
        "space_consumed": usage.get("spaceConsumed", 0), "space_quota": usage.get("spaceQuota", -1), "type_quota": usage.get("typeQuota", {})}


@pack_tool(effect="read", requires_connection=True)
def get_filesystem_status(ctx: ToolContext) -> dict:
    """Report the whole filesystem's capacity, used and remaining bytes. Needs Hadoop 3.4 or later; older clusters answer that the operation is unsupported."""
    status = call(ctx, "GET", "/", "GETSTATUS")["FsStatus"]
    return {"capacity": status.get("capacity", 0), "used": status.get("used", 0), "remaining": status.get("remaining", 0)}


@pack_tool(effect="read", requires_connection=True)
def get_checksum(ctx: ToolContext, path: str) -> dict:
    """Return the file's checksum (algorithm and hex value), for comparing copies or verifying an upload."""
    checksum = call(ctx, "GET", path, "GETFILECHECKSUM")["FileChecksum"]
    return {"path": check_path(path), "algorithm": checksum.get("algorithm", ""), "checksum": checksum.get("bytes", ""), "length": checksum.get("length", 0)}


# ---- Listing and locations ------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_directory_page(ctx: ToolContext, path: str, start_after: str = "") -> dict:
    """List one page of a large directory. Pass the last name of the previous page as start_after to get the next page; remaining says how many entries follow."""
    listing = call(ctx, "GET", path, "LISTSTATUS_BATCH", {"startAfter": start_after or None})["DirectoryListing"]
    entries = [status_entry(s) for s in listing.get("partialListing", {}).get("FileStatuses", {}).get("FileStatus", [])]
    remaining = listing.get("remainingEntries", 0)
    return {"path": check_path(path), "entries": entries, "remaining": remaining, "next_start_after": entries[-1]["name"] if entries and remaining else None}


@pack_tool(effect="read", requires_connection=True)
def get_home_directory(ctx: ToolContext) -> dict:
    """Return the calling user's home directory, usually /user/<name>; use it to resolve relative paths the user mentions."""
    return {"path": call(ctx, "GET", "/", "GETHOMEDIRECTORY").get("Path", ""), "user": ctx.caller.username}


@pack_tool(effect="read", requires_connection=True)
def get_trash_root(ctx: ToolContext, path: str = "/") -> dict:
    """Return the trash directory that deleted files from a path move to (when trash is enabled), so recently deleted files can be found."""
    return {"path": check_path(path), "trash": call(ctx, "GET", path, "GETTRASHROOT").get("Path", "")}


# ---- Permissions, ACLs and access checks ------------------------------------------------------------------------------

@pack_tool(effect="write", requires_connection=True)
def set_permission(ctx: ToolContext, path: str, permission: str) -> dict:
    """Change a file's or directory's permission bits, given in octal such as 750 or 644."""
    if not OCTAL.match(permission or ""):
        raise ValueError("permission must be three or four octal digits, for example 750")
    call(ctx, "PUT", path, "SETPERMISSION", {"permission": permission})
    return {"path": check_path(path), "permission": permission}


@pack_tool(effect="write", requires_connection=True)
def set_owner(ctx: ToolContext, path: str, owner: str = "", group: str = "") -> dict:
    """Change a file's or directory's owner and/or group. Give at least one of them."""
    if not owner and not group:
        raise ValueError("Give an owner, a group, or both")
    for value in (owner, group):
        if value and not NAME.match(value):
            raise ValueError(f"{value!r} is not a valid owner or group name")
    call(ctx, "PUT", path, "SETOWNER", {"owner": owner or None, "group": group or None})
    return {"path": check_path(path), "owner": owner or None, "group": group or None}


@pack_tool(effect="read", requires_connection=True)
def get_acl_status(ctx: ToolContext, path: str) -> dict:
    """Show who may access a path: owner, group, permission bits, the sticky bit and any extended ACL entries such as user:alice:rwx."""
    acl = call(ctx, "GET", path, "GETACLSTATUS")["AclStatus"]
    return {"path": check_path(path), "owner": acl.get("owner", ""), "group": acl.get("group", ""), "permission": acl.get("permission", ""),
        "sticky_bit": bool(acl.get("stickyBit", False)), "entries": acl.get("entries", [])}


@pack_tool(effect="read", requires_connection=True)
def check_access(ctx: ToolContext, path: str, action: str = "r--") -> dict:
    """Check whether the calling user may read, write or execute a path. action is three characters like r--, -w- or rwx; the answer says allowed or why not."""
    if not FSACTION.match(action or ""):
        raise ValueError("action must be three characters from r, w, x or -, for example r-- or rw-")
    try:
        call(ctx, "GET", path, "CHECKACCESS", {"fsaction": action})
    except ValueError as exc:
        if "AccessControlException" not in str(exc):
            raise
        return {"path": check_path(path), "action": action, "allowed": False, "reason": str(exc)}
    return {"path": check_path(path), "action": action, "allowed": True}


# ---- Replication, storage and times --------------------------------------------------------------------------------

@pack_tool(effect="write", requires_connection=True)
def set_replication(ctx: ToolContext, path: str, replication: int) -> dict:
    """Set the replication factor of a file (1 to 10). Directories are not affected."""
    if not 1 <= replication <= 10:
        raise ValueError("replication must be between 1 and 10")
    result = call(ctx, "PUT", path, "SETREPLICATION", {"replication": replication})
    return {"path": check_path(path), "replication": replication, "changed": bool(result.get("boolean", True))}


@pack_tool(effect="read", requires_connection=True)
def get_storage_policy(ctx: ToolContext, path: str) -> dict:
    """Show the block storage policy a path uses (such as HOT, WARM, COLD or ALL_SSD) and the storage types it places replicas on."""
    policy = call(ctx, "GET", path, "GETSTORAGEPOLICY")["BlockStoragePolicy"]
    return {"path": check_path(path), "name": policy.get("name", ""), "id": policy.get("id"), "storage_types": policy.get("storageTypes", []),
        "creation_fallbacks": policy.get("creationFallbacks", []), "replication_fallbacks": policy.get("replicationFallbacks", [])}


@pack_tool(effect="write", requires_connection=True)
def set_times(ctx: ToolContext, path: str, modified: str = "", accessed: str = "") -> dict:
    """Set a file's modification and/or access time, as ISO 8601 timestamps (2026-01-31T09:00:00Z) or epoch milliseconds. Leave one empty to keep it."""
    mtime, atime = millis(modified), millis(accessed)
    if mtime < 0 and atime < 0:
        raise ValueError("Give a modification time, an access time, or both")
    call(ctx, "PUT", path, "SETTIMES", {"modificationtime": mtime if mtime >= 0 else None, "accesstime": atime if atime >= 0 else None})
    return {"path": check_path(path), "modified": iso(mtime) if mtime >= 0 else None, "accessed": iso(atime) if atime >= 0 else None}


# ---- Extended attributes ------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_xattrs(ctx: ToolContext, path: str) -> dict:
    """List the names of the extended attributes set on a file or directory, such as user.owner_team."""
    names = call(ctx, "GET", path, "LISTXATTRS").get("XAttrNames", "[]")
    return {"path": check_path(path), "names": json.loads(names) if isinstance(names, str) else list(names)}


@pack_tool(effect="read", requires_connection=True)
def get_xattrs(ctx: ToolContext, path: str, names: str = "") -> dict:
    """Read extended attributes of a file or directory. names is a comma-separated list such as user.owner_team,user.retention; empty reads them all. Values are text, or base64 when binary."""
    wanted = [check_xattr(n.strip()) for n in names.split(",") if n.strip()]
    attrs = call(ctx, "GET", path, "GETXATTRS", {"xattr.name": wanted, "encoding": "hex"}).get("XAttrs", [])
    values = []
    for attr in attrs:
        value, encoding = decode_value(attr.get("value") or "")
        values.append({"name": attr.get("name", ""), "value": value, "encoding": encoding})
    return {"path": check_path(path), "attributes": values}


@pack_tool(effect="write", requires_connection=True)
def set_xattr(ctx: ToolContext, path: str, name: str, value: str, replace: bool = False) -> dict:
    """Set an extended attribute (a small text value) on a file or directory, for example user.owner_team = finance. Set replace=true to change an attribute that already exists."""
    check_xattr(name)
    if len(value.encode("utf-8")) > 16 * 1024:
        raise ValueError("Extended attribute values are limited to 16 KiB")
    call(ctx, "PUT", path, "SETXATTR", {"xattr.name": name, "xattr.value": "0x" + value.encode("utf-8").hex(), "flag": "REPLACE" if replace else "CREATE"})
    return {"path": check_path(path), "name": name, "value": value, "replaced": replace}


@pack_tool(effect="write", requires_connection=True)
def remove_xattr(ctx: ToolContext, path: str, name: str) -> dict:
    """Remove one extended attribute from a file or directory."""
    check_xattr(name)
    call(ctx, "PUT", path, "REMOVEXATTR", {"xattr.name": name})
    return {"path": check_path(path), "name": name, "removed": True}


# ---- Snapshots --------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_snapshottable_directories(ctx: ToolContext) -> dict:
    """List the directories an administrator has allowed snapshots on, with how many snapshots each holds. Snapshots can only be taken under these."""
    listed = call(ctx, "GET", "/", "GETSNAPSHOTTABLEDIRECTORYLIST").get("SnapshottableDirectoryList", [])
    return {"directories": [{"path": (d.get("parentFullPath", "").rstrip("/") + "/" + d.get("dirStatus", {}).get("pathSuffix", "")), "snapshots": d.get("snapshotNumber", 0),
        "snapshot_quota": d.get("snapshotQuota", 0), **{k: v for k, v in status_entry(d.get("dirStatus", {})).items() if k != "name"}} for d in listed]}


@pack_tool(effect="read", requires_connection=True)
def list_snapshots(ctx: ToolContext, path: str) -> dict:
    """List the snapshots of a snapshottable directory with their full .snapshot paths. Needs Hadoop 3.3 or later."""
    listed = call(ctx, "GET", path, "GETSNAPSHOTLIST").get("SnapshotList", [])
    return {"path": check_path(path), "snapshots": [{"name": s.get("fullPath", "").rsplit("/", 1)[-1], "path": s.get("fullPath", ""), "id": s.get("snapshotID"),
        "status": s.get("snapshotStatus", "").lower(), "taken": iso(s.get("dirStatus", {}).get("modificationTime", 0))} for s in listed]}


@pack_tool(effect="read", requires_connection=True)
def get_snapshot_diff(ctx: ToolContext, path: str, from_snapshot: str, to_snapshot: str = ".") -> dict:
    """Show what changed in a directory between two snapshots: created, deleted, modified and renamed paths. to_snapshot "." means the current state."""
    check_snapshot(from_snapshot)
    if to_snapshot != ".":
        check_snapshot(to_snapshot)
    report = call(ctx, "GET", path, "GETSNAPSHOTDIFF", {"oldsnapshotname": from_snapshot, "snapshotname": to_snapshot})["SnapshotDiffReport"]
    changes = [{"type": d.get("type", "").lower(), "path": d.get("sourcePath", ""), **({"renamed_to": d["targetPath"]} if d.get("targetPath") else {})} for d in report.get("diffList", [])]
    return {"path": check_path(path), "from_snapshot": report.get("fromSnapshot", from_snapshot), "to_snapshot": report.get("toSnapshot", to_snapshot), "changes": changes}


@pack_tool(effect="write", requires_connection=True)
def create_snapshot(ctx: ToolContext, path: str, name: str = "") -> dict:
    """Take a snapshot of a snapshottable directory, a read-only point-in-time copy under <path>/.snapshot/<name>. Without a name HDFS picks a timestamp."""
    if name:
        check_snapshot(name)
    created = call(ctx, "PUT", path, "CREATESNAPSHOT", {"snapshotname": name or None}).get("Path", "")
    return {"path": check_path(path), "name": created.rsplit("/", 1)[-1] if created else name, "snapshot_path": created}


@pack_tool(effect="write", requires_connection=True)
def rename_snapshot(ctx: ToolContext, path: str, name: str, new_name: str) -> dict:
    """Rename a snapshot of a directory."""
    check_snapshot(name)
    check_snapshot(new_name)
    call(ctx, "PUT", path, "RENAMESNAPSHOT", {"oldsnapshotname": name, "snapshotname": new_name})
    return {"path": check_path(path), "name": new_name, "previous_name": name}


@pack_tool(effect="write", requires_connection=True)
def delete_snapshot(ctx: ToolContext, path: str, name: str) -> dict:
    """Delete one snapshot of a directory. The directory's current contents are not affected."""
    check_snapshot(name)
    call(ctx, "DELETE", path, "DELETESNAPSHOT", {"snapshotname": name})
    return {"path": check_path(path), "name": name, "deleted": True}


# ---- Appending and joining files -----------------------------------------------------------------------------------

@pack_tool(effect="write", requires_connection=True)
def append(ctx: ToolContext, path: str, content: str, encoding: str = "utf-8") -> dict:
    """Append inline content (UTF-8 text, or base64 for binary data) to the end of an existing file, for example a new line in a log or CSV."""
    if encoding not in {"utf-8", "base64"}:
        raise ValueError("encoding must be utf-8 or base64")
    try:
        data = base64.b64decode(content, validate=True) if encoding == "base64" else content.encode("utf-8")
    except ValueError as exc:
        raise ValueError("content is not valid base64") from exc
    if len(data) > setting(ctx, "max_upload_bytes"):
        raise ValueError(f"Appends are limited to {setting(ctx, 'max_upload_bytes')} bytes for this tool")
    call(ctx, "POST", path, "APPEND", {"data": "true"}, content=data)
    return {"path": check_path(path), "appended": len(data)}


@pack_tool(effect="write", requires_connection=True)
def concat(ctx: ToolContext, target: str, sources: str) -> dict:
    """Join files onto the end of target in order, server-side without copying data. sources is a comma-separated list of files in the same directory; they are removed afterwards."""
    parts = [check_path(s.strip()) for s in sources.split(",") if s.strip()]
    if not parts:
        raise ValueError("Give at least one source file")
    call(ctx, "POST", target, "CONCAT", {"sources": ",".join(parts)})
    return {"target": check_path(target), "sources": parts, "concatenated": len(parts)}
