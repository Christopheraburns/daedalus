"""Ownership, permissions, replication, checksums and space usage on HDFS or Ozone over WebHDFS.
Extends the built-in hdfs pack with the administrative operations a file-management agent needs."""
import re
from urllib.parse import quote

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "webhdfs"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix       WebHDFS path prefix on the connection, default "/webhdfs/v1" (Knox: "/gateway/cdp-proxy-api/webhdfs/v1")
#   pseudo_auth  true to send user.name=<caller> for clusters without Kerberos
DEFAULTS = {"prefix": "/webhdfs/v1", "pseudo_auth": False}
PATH = re.compile(r"^/(?:[^\x00-\x1f\x7f]*)$")
OCTAL = re.compile(r"^[0-7]{3,4}$")
NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.@-]{0,63}$")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_path(path):
    if not PATH.match(path or "") or any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("Paths must be absolute HDFS paths without . or .. segments")
    return path.rstrip("/") or "/"


def call(ctx, method, path, op, **params):
    query = {"op": op, **{k: v for k, v in params.items() if v is not None and v != ""}}
    if setting(ctx, "pseudo_auth"):
        query["user.name"] = ctx.caller.username
    url = setting(ctx, "prefix").rstrip("/") + quote(check_path(path), safe="/")
    with ctx.client(timeout=30.0) as client:
        response = client.request(method, url, params=query)
    if response.status_code >= 400:
        try:
            detail = response.json()["RemoteException"]
            raise ValueError(f"{detail.get('exception', 'Error')}: {detail.get('message', '')}"[:400])
        except (ValueError, KeyError, TypeError) as exc:
            if isinstance(exc, ValueError) and str(exc) and not str(exc).startswith("Expecting"):
                raise
            raise ValueError(f"HTTP {response.status_code} from the HDFS endpoint")
    return response.json() if response.content else {}


@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the endpoint speaks WebHDFS by reading the root directory's status."""
    status = call(ctx, "GET", "/", "GETFILESTATUS")["FileStatus"]
    return {"message": f"WebHDFS answered; / is owned by {status.get('owner', '?')}"}


@pack_tool(effect="read", requires_connection=True)
def get_content_summary(ctx: ToolContext, path: str) -> dict:
    """Report how much a directory holds: file and directory counts, total bytes, and quota usage if quotas are set."""
    summary = call(ctx, "GET", path, "GETCONTENTSUMMARY")["ContentSummary"]
    return {"path": check_path(path), "files": summary.get("fileCount", 0), "directories": summary.get("directoryCount", 0),
        "bytes": summary.get("length", 0), "space_consumed": summary.get("spaceConsumed", 0),
        "quota": summary.get("quota", -1), "space_quota": summary.get("spaceQuota", -1)}


@pack_tool(effect="read", requires_connection=True)
def get_checksum(ctx: ToolContext, path: str) -> dict:
    """Return the file's checksum (algorithm and hex value), for comparing copies or verifying an upload."""
    checksum = call(ctx, "GET", path, "GETFILECHECKSUM")["FileChecksum"]
    return {"path": check_path(path), "algorithm": checksum.get("algorithm", ""), "checksum": checksum.get("bytes", ""), "length": checksum.get("length", 0)}


@pack_tool(effect="write", requires_connection=True)
def set_permission(ctx: ToolContext, path: str, permission: str) -> dict:
    """Change a file's or directory's permission bits, given in octal such as 750 or 644."""
    if not OCTAL.match(permission or ""):
        raise ValueError("permission must be three or four octal digits, for example 750")
    call(ctx, "PUT", path, "SETPERMISSION", permission=permission)
    return {"path": check_path(path), "permission": permission}


@pack_tool(effect="write", requires_connection=True)
def set_owner(ctx: ToolContext, path: str, owner: str = "", group: str = "") -> dict:
    """Change a file's or directory's owner and/or group. Give at least one of them."""
    if not owner and not group:
        raise ValueError("Give an owner, a group, or both")
    for value in (owner, group):
        if value and not NAME.match(value):
            raise ValueError(f"{value!r} is not a valid owner or group name")
    call(ctx, "PUT", path, "SETOWNER", owner=owner or None, group=group or None)
    return {"path": check_path(path), "owner": owner or None, "group": group or None}


@pack_tool(effect="write", requires_connection=True)
def set_replication(ctx: ToolContext, path: str, replication: int) -> dict:
    """Set the replication factor of a file (1 to 10). Directories are not affected."""
    if not 1 <= replication <= 10:
        raise ValueError("replication must be between 1 and 10")
    result = call(ctx, "PUT", path, "SETREPLICATION", replication=replication)
    return {"path": check_path(path), "replication": replication, "changed": bool(result.get("boolean", True))}
