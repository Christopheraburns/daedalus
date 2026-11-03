"""Inventory and capacity of an Apache Ozone cluster through Recon, Ozone's reporting service: volumes, buckets and
keys, what a path holds and how much space it uses, quotas, file size distributions, open and pending-deletion
keys, and the cluster's datanodes, containers and storage. Read-only. Answers "what is in Ozone and how big is it"
without touching the data; the s3 and s3_extras packs read and write the objects themselves."""
import re
from datetime import datetime, timezone

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix       path of the Recon API on the connection, default "/api/v1";
#                through Knox for example "/gateway/cdp-proxy/ozone-recon/api/v1"
#   page_size    default 100, the most items one listing returns
#   simple_user  for a Recon with Hadoop "simple" authentication that refuses anonymous callers: "caller" sends the
#                calling user's name as user.name, any other value is sent as a fixed name, "" (default) sends nothing
# Authentication is otherwise the connection's: none (simple, anonymous), basic or forward-token (Knox), static.
# Recon reports the whole cluster; it does not narrow answers to what the caller may read.
DEFAULTS = {"prefix": "/api/v1", "page_size": 100, "simple_user": ""}
SEGMENT = re.compile(r"^[^\x00-\x1f\x7f]{1,1024}$")
UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_path(value, what="path"):
    value = (value or "").strip()
    if not value.startswith("/") or not SEGMENT.match(value) or "//" in value:
        raise ValueError(f"{what} must be absolute, like /volume/bucket/dir, without empty segments")
    return value if value == "/" else value.rstrip("/")


def check_name(value, what):
    value = (value or "").strip()
    if not value or "/" in value or not SEGMENT.match(value):
        raise ValueError(f"{what} must be a name without slashes")
    return value


def call(ctx, path, params=None, feature=None):
    query = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    user = setting(ctx, "simple_user")
    if user:
        query["user.name"] = ctx.caller.username if user == "caller" else user
    url = setting(ctx, "prefix").rstrip("/") + "/" + path.lstrip("/")
    with ctx.client(timeout=60.0) as client:
        response = client.get(url, params=query)
    is_json = response.headers.get("content-type", "").startswith("application/json")
    body = None
    if is_json and response.content:
        try:
            body = response.json()
        except ValueError:
            body = None
    if response.status_code == 204:
        return None
    if response.status_code < 400:
        if response.content and body is None:
            raise ValueError("Recon returned a response that is not JSON; check the prefix in the tool configuration")
        return body
    if response.status_code == 401:
        raise ValueError("Recon rejected the connection's credentials (HTTP 401); for simple authentication set simple_user in the tool configuration")
    if response.status_code == 403:
        raise ValueError("Recon refused the request: " + (body.get("message") if isinstance(body, dict) and body.get("message") else "the identity may not read this"))
    if response.status_code == 503 and isinstance(body, dict) and body.get("status") == "INITIALIZING":
        raise ValueError("Recon is still loading the Ozone Manager database; try again in a few minutes")
    if response.status_code in (404, 405) and not (isinstance(body, dict) and body.get("message")):
        raise ValueError(feature or f"Recon has no endpoint at {url}; check the prefix in the tool configuration")
    if isinstance(body, dict) and body.get("message"):
        raise ValueError(f"Recon error {response.status_code}: {body['message']}")
    raise ValueError(f"Recon error {response.status_code}: {response.text[:200] or 'no detail'}")


def checked(result, path):
    """Raise for the statuses Recon reports inside a 200 answer; return whether the type applies to this path."""
    status = (result or {}).get("status", "OK")
    if status == "PATH_NOT_FOUND":
        raise ValueError(f"Nothing in Ozone at {path}: no volume, bucket, directory or key has that path")
    if status == "INITIALIZING":
        raise ValueError("Recon is still loading the Ozone Manager database; try again in a few minutes")
    return status != "TYPE_NOT_APPLICABLE"


def page(ctx, limit, offset=0):
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    return max(1, min(limit, int(setting(ctx, "page_size"))))


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def when(millis):
    return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if millis else None


def quota(value):
    return None if value in (None, -1) else value


def human(size):
    value, unit = float(size), 0
    while value >= 1024 and unit < len(UNITS) - 1:
        value, unit = value / 1024, unit + 1
    return f"{value:g} {UNITS[unit]}"


def acls(items):
    return [f"{a.get('type', '?')} {a.get('name', '?')}: {', '.join(a.get('aclList', []))}" + (f" ({a['scope'].lower()})" if a.get("scope") and a["scope"] != "ACCESS" else "") for a in items or []]


def replication(info):
    if not info:
        return None
    if info.get("replicationType") == "EC":
        return f"EC {info.get('codec', 'RS')}-{info.get('data', '?')}-{info.get('parity', '?')}-{int(info.get('ecChunkSize', 0)) // 1024}k"
    return f"{info.get('replicationType', '?')}/{info.get('replicationFactor') or info.get('requiredNodes', '?')}"


def volume(item):
    return dropped({"name": item.get("volume") or item.get("name"), "owner": item.get("owner"), "admin": item.get("admin"), "quota_bytes": quota(item.get("quotaInBytes")), "quota_namespace": quota(item.get("quotaInNamespace")),
        "used_namespace": item.get("usedNamespace"), "created": when(item.get("creationTime")), "modified": when(item.get("modificationTime")), "acls": acls(item.get("acls"))})


def bucket(item):
    source = f"{item['sourceVolume']}/{item['sourceBucket']}" if item.get("sourceVolume") and item.get("sourceBucket") else None
    return dropped({"volume": item.get("volumeName"), "name": item.get("name"), "layout": item.get("bucketLayout"), "storage_type": item.get("storageType"), "versioning": item.get("versioning"), "owner": item.get("owner"),
        "used_bytes": item.get("usedBytes"), "used_namespace": item.get("usedNamespace"), "quota_bytes": quota(item.get("quotaInBytes")), "quota_namespace": quota(item.get("quotaInNamespace")),
        "created": when(item.get("creationTime")), "modified": when(item.get("modificationTime")), "linked_to": source, "encrypted": True if item.get("encryptionInfo") else None,
        "replication": replication(item.get("replicationConfigInfo")), "acls": acls(item.get("acls"))})


def key(item):
    return dropped({"path": item.get("path") or item.get("key"), "size_bytes": item.get("size"), "replicated_bytes": item.get("replicatedSize"), "replication": replication(item.get("replicationInfo")),
        "created": when(item.get("creationTime")), "modified": when(item.get("modificationTime"))})


def counts(result):
    stats = result.get("countStats") or result  # Recon before the countStats block reported the counts at the top level
    return dropped({k: v for k, v in (("volumes", stats.get("numVolume")), ("buckets", stats.get("numBucket")), ("directories", stats.get("numDir")), ("keys", stats.get("numKey"))) if v is not None and v >= 0})


def size_bin(index):
    return 1 << (10 + index)


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm Recon answers by reading the cluster state."""
    state = call(ctx, "clusterState") or {}
    return {"ok": True, "message": f"Recon answered: {state.get('volumes', '?')} volumes, {state.get('buckets', '?')} buckets, {state.get('keys', '?')} keys on "
        f"{state.get('totalDatanodes', '?')} datanodes ({state.get('healthyDatanodes', '?')} healthy)"}


# ---- Inventory ------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_volumes(ctx: ToolContext, limit: int = 100, start_after: str = "") -> dict:
    """List the volumes in Ozone with owner, admin, quotas and ACLs. Pass start_after (the last name of the previous page) to continue a long list."""
    size = page(ctx, limit)
    result = call(ctx, "volumes", {"limit": size + 1, "prevKey": start_after.strip()}) or {}
    items = [volume(v) for v in result.get("volumes", [])]
    return {"volumes": items[:size], **dropped({"count": min(len(items), size), "total": result.get("totalCount"), "truncated": len(items) > size, "next_start_after": items[size - 1]["name"] if len(items) > size else None})}


@pack_tool(effect="read", requires_connection=True)
def list_buckets(ctx: ToolContext, volume: str = "", limit: int = 100, start_after: str = "") -> dict:
    """List buckets, in one volume or across all volumes, with layout (FILE_SYSTEM_OPTIMIZED, OBJECT_STORE, LEGACY), owner, space and object counts used, quotas, versioning and replication."""
    size = page(ctx, limit)
    result = call(ctx, "buckets", {"volume": check_name(volume, "volume") if volume.strip() else "", "limit": size + 1, "prevKey": start_after.strip()}) or {}
    items = [bucket(b) for b in result.get("buckets", [])]
    return {"buckets": items[:size], **dropped({"count": min(len(items), size), "total": result.get("totalCount"), "truncated": len(items) > size, "next_start_after": items[size - 1]["name"] if len(items) > size else None})}


@pack_tool(effect="read", requires_connection=True)
def list_keys(ctx: ToolContext, prefix: str, limit: int = 100, start_after: str = "", replication_type: str = "", min_size_bytes: int = 0, created_after: str = "") -> dict:
    """List the keys (files) under a prefix such as /volume/bucket or /volume/bucket/dir, with size, replication and dates. Filter by replication type (RATIS or EC), minimum size in bytes, or creation time (MM-dd-yyyy HH:mm:ss, UTC). Pass start_after (the previous page's last_key) to continue."""
    prefix = check_path(prefix, "prefix")
    if prefix.count("/") < 2:
        raise ValueError("prefix must name at least a volume and a bucket, like /volume/bucket")
    replication_type = replication_type.strip().upper()
    if replication_type and replication_type not in ("RATIS", "EC"):
        raise ValueError("replication_type must be RATIS or EC")
    if min_size_bytes < 0:
        raise ValueError("min_size_bytes must be zero or positive")
    if created_after.strip() and not re.fullmatch(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}", created_after.strip()):
        raise ValueError("created_after must look like MM-dd-yyyy HH:mm:ss")
    size = page(ctx, limit)
    params = {"startPrefix": prefix, "limit": size + 1, "prevKey": start_after.strip(), "replicationType": replication_type, "keySize": min_size_bytes or None, "creationDate": created_after.strip()}
    result = call(ctx, "keys/listKeys", params, feature="This Recon does not offer key listing (Ozone 2.0 and later); use the s3 pack to list objects") or {}
    checked(result, prefix)
    items = [key(k) for k in result.get("keys", [])]
    shown = items[:size]
    return {"prefix": prefix, "keys": shown, **dropped({"count": len(shown), "truncated": len(items) > size, "last_key": (result.get("keys") or [{}])[len(shown) - 1].get("key") if shown and len(items) > size else None,
        "total_bytes": sum(k.get("size_bytes", 0) for k in shown), "total_replicated_bytes": sum(k.get("replicated_bytes", 0) for k in shown)})}


# ---- Namespace --------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def describe_path(ctx: ToolContext, path: str) -> dict:
    """Say what a path is in Ozone (the root, a volume, a bucket, a directory or a key) and count what it holds: volumes, buckets, directories and keys, plus the object's own owner, quotas, dates and ACLs."""
    path = check_path(path)
    result = call(ctx, "namespace/summary", {"path": path}) or {}
    checked(result, path)
    kind = (result.get("type") or "UNKNOWN").lower()
    info = result.get("objectInfo") or {}
    return dropped({"path": path, "type": kind, "counts": counts(result), "name": info.get("name"), "owner": info.get("owner"), "admin": info.get("admin"), "layout": info.get("bucketLayout"),
        "size_bytes": info.get("dataSize"), "replication": replication(info.get("replicationConfig")), "quota_bytes": quota(info.get("quotaInBytes")), "quota_namespace": quota(info.get("quotaInNamespace")),
        "used_namespace": info.get("usedNamespace"), "created": when(info.get("creationTime")), "modified": when(info.get("modificationTime")), "metadata": info.get("metadata"), "acls": acls(info.get("acls"))})


@pack_tool(effect="read", requires_connection=True)
def disk_usage(ctx: ToolContext, path: str, include_files: bool = False, with_replication: bool = False, limit: int = 100, offset: int = 0) -> dict:
    """Show how much data sits under a path and how it splits across the children (volumes under /, buckets under a volume, directories under a bucket or directory), largest first. include_files lists the keys directly under the path too; with_replication adds the on-disk size after replication."""
    path = check_path(path)
    size = page(ctx, limit, offset)
    result = call(ctx, "namespace/usage", {"path": path, "files": "true" if include_files else "false", "replica": "true" if with_replication else "false", "sortSubPaths": "true"}) or {}
    checked(result, path)
    children = [dropped({"path": c.get("path"), "size_bytes": c.get("size"), "size": human(c.get("size", 0)), "replicated_bytes": c.get("sizeWithReplica") if with_replication else None, "is_key": True if c.get("isKey") else None}) for c in result.get("subPaths") or []]
    shown = children[offset:offset + size]
    return {"children": shown, **dropped({"path": path, "size_bytes": result.get("size"), "size": human(result.get("size", 0)), "replicated_bytes": result.get("sizeWithReplica") if with_replication else None,
        "direct_keys_bytes": result.get("sizeDirectKey"), "count": len(shown), "offset": offset, "truncated": len(children) > offset + size, "total_children": result.get("subPathCount")})}


@pack_tool(effect="read", requires_connection=True)
def quota_usage(ctx: ToolContext, path: str) -> dict:
    """Show the space quota set on a volume or bucket and how much of it is used. Directories and keys carry no quota of their own."""
    path = check_path(path)
    result = call(ctx, "namespace/quota", {"path": path}) or {}
    if not checked(result, path):
        return {"path": path, "note": "Only volumes and buckets carry a quota; ask for the enclosing bucket or volume"}
    allowed = quota(result.get("allowed"))
    used = result.get("used", 0)
    return dropped({"path": path, "quota_bytes": allowed, "quota": human(allowed) if allowed else "unlimited", "used_bytes": used, "used": human(used), "percent_used": round(100 * used / allowed, 1) if allowed else None})


@pack_tool(effect="read", requires_connection=True)
def file_size_distribution(ctx: ToolContext, path: str) -> dict:
    """Show how the files under a volume, bucket or directory spread across size bands (up to 1 KB, 2 KB, ... 1 PB), to spot small-file problems or large archives. Empty bands are omitted."""
    path = check_path(path)
    result = call(ctx, "namespace/dist", {"path": path}) or {}
    if not checked(result, path):
        return {"path": path, "note": "A file size distribution applies to volumes, buckets and directories, not to a single key"}
    dist = result.get("dist") or []
    bins = [{"up_to": human(size_bin(i)), "upper_bound_bytes": size_bin(i), "count": n} for i, n in enumerate(dist) if n]
    return {"path": path, "total_files": sum(dist), "bins": bins}


# ---- Cluster ----------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def cluster_state(ctx: ToolContext) -> dict:
    """Summarise the Ozone cluster: datanodes and how many are healthy, pipelines, containers (open, missing, deleted), raw storage capacity and use, and the namespace totals (volumes, buckets, keys, keys and directories pending deletion)."""
    state = call(ctx, "clusterState") or {}
    report = state.get("storageReport") or {}
    return dropped({"datanodes": dropped({"total": state.get("totalDatanodes"), "healthy": state.get("healthyDatanodes")}), "pipelines": state.get("pipelines"),
        "containers": dropped({"total": state.get("containers"), "open": state.get("openContainers"), "missing": state.get("missingContainers"), "deleted": state.get("deletedContainers")}),
        "storage": dropped({"capacity_bytes": report.get("capacity"), "capacity": human(report["capacity"]) if report.get("capacity") is not None else None, "used_bytes": report.get("used"), "used": human(report["used"]) if report.get("used") is not None else None,
            "remaining_bytes": report.get("remaining"), "committed_bytes": report.get("committed"), "reserved_bytes": report.get("reserved"), "minimum_free_bytes": report.get("minimumFreeSpace"),
            "filesystem_capacity_bytes": report.get("filesystemCapacity"), "filesystem_used_bytes": report.get("filesystemUsed"), "filesystem_available_bytes": report.get("filesystemAvailable")}),
        "namespace": dropped({"volumes": state.get("volumes"), "buckets": state.get("buckets"), "keys": state.get("keys"), "keys_pending_deletion": state.get("keysPendingDeletion"), "directories_pending_deletion": state.get("deletedDirs")}),
        "om_service_id": state.get("omServiceId"), "scm_service_id": state.get("scmServiceId")})


@pack_tool(effect="read", requires_connection=True)
def storage_distribution(ctx: ToolContext) -> dict:
    """Break the cluster's storage down: Ozone capacity, used, free, committed and reserved space overall, what the namespace holds, how much belongs to finalized keys versus keys still open for writing, and each datanode's capacity and use."""
    result = call(ctx, "storageDistribution", feature="This Recon does not offer the storage distribution report (Ozone 2.0 and later); cluster_state gives the capacity totals") or {}
    g, ns, breakdown = result.get("globalStorage") or {}, result.get("globalNamespace") or {}, result.get("usedSpaceBreakdown") or {}
    open_bytes = breakdown.get("openKeyBytes") or {}
    return dropped({"global": dropped({"capacity_bytes": g.get("totalOzoneCapacity"), "capacity": human(g["totalOzoneCapacity"]) if g.get("totalOzoneCapacity") is not None else None, "used_bytes": g.get("totalOzoneUsedSpace"),
            "used": human(g["totalOzoneUsedSpace"]) if g.get("totalOzoneUsedSpace") is not None else None, "free_bytes": g.get("totalOzoneFreeSpace"), "committed_bytes": g.get("totalOzoneCommittedSpace"),
            "reserved_bytes": g.get("totalReservedSpace"), "minimum_free_bytes": g.get("totalMinimumFreeSpace"), "filesystem_capacity_bytes": g.get("totalFileSystemCapacity")}),
        "namespace": dropped({"used_bytes": ns.get("totalUsedSpace"), "keys": ns.get("totalKeys")}),
        "used_space": dropped({"finalized_key_bytes": breakdown.get("finalizedKeyBytes"), "open_key_bytes": open_bytes.get("totalOpenKeyBytes"), "open_key_and_file_bytes": open_bytes.get("openKeyAndFileBytes"), "multipart_open_bytes": open_bytes.get("multipartOpenKeyBytes")}),
        "datanodes": [dropped({"host": d.get("hostName"), "uuid": d.get("datanodeUuid"), "capacity_bytes": d.get("capacity"), "used_bytes": d.get("used"), "used": human(d.get("used", 0)), "remaining_bytes": d.get("remaining"), "committed_bytes": d.get("committed")}) for d in result.get("dataNodeUsage") or []]})


@pack_tool(effect="read", requires_connection=True)
def file_counts(ctx: ToolContext, volume: str = "", bucket: str = "", limit: int = 200, offset: int = 0) -> dict:
    """Count files per bucket and size band across the cluster (or one volume or bucket): the cluster-wide view of small and large files. Each row is a volume, bucket and the band's upper bound with the number of files in it."""
    size = page(ctx, limit, offset)
    params = {"volume": check_name(volume, "volume") if volume.strip() else "", "bucket": check_name(bucket, "bucket") if bucket.strip() else ""}
    if params["bucket"] and not params["volume"]:
        raise ValueError("Name the volume when filtering by bucket")
    rows = sorted(call(ctx, "utilization/fileCount", params) or [], key=lambda r: (r.get("volume", ""), r.get("bucket", ""), r.get("fileSize", 0)))
    items = [{"volume": r.get("volume"), "bucket": r.get("bucket"), "up_to": human(r.get("fileSize", 0)), "upper_bound_bytes": r.get("fileSize"), "count": r.get("count")} for r in rows]
    shown = items[offset:offset + size]
    return {"rows": shown, "count": len(shown), "offset": offset, "truncated": len(items) > offset + size, "total_files": sum(r.get("count", 0) for r in rows)}


# ---- Keys in flight ---------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def open_keys_summary(ctx: ToolContext) -> dict:
    """Count the keys currently open for writing and the data they hold, before and after replication."""
    s = call(ctx, "keys/open/summary") or {}
    return dropped({"open_keys": s.get("totalOpenKeys"), "data_bytes": s.get("totalUnreplicatedDataSize"), "data": human(s.get("totalUnreplicatedDataSize", 0)), "replicated_bytes": s.get("totalReplicatedDataSize")})


@pack_tool(effect="read", requires_connection=True)
def pending_deletion_summary(ctx: ToolContext) -> dict:
    """Count the deleted keys whose blocks are still waiting to be reclaimed, and the space they occupy, before and after replication."""
    s = call(ctx, "keys/deletePending/summary") or {}
    return dropped({"keys_pending_deletion": s.get("totalDeletedKeys"), "data_bytes": s.get("totalUnreplicatedDataSize"), "data": human(s.get("totalUnreplicatedDataSize", 0)), "replicated_bytes": s.get("totalReplicatedDataSize")})


@pack_tool(effect="read", requires_connection=True)
def deleted_directories_summary(ctx: ToolContext) -> dict:
    """Count the deleted directories whose contents are still being purged in the background."""
    s = call(ctx, "keys/deletePending/dirs/summary", feature="This Recon does not offer the deleted directory summary (Ozone 1.4 and later)") or {}
    return dropped({"directories_pending_deletion": s.get("totalDeletedDirectories")})
