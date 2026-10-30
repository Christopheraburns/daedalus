"""More object storage operations over the S3 API (Ozone S3 Gateway, MinIO, AWS S3): bucket checks, deleting many
objects in one call, and object tags. Extends the built-in s3 pack, which covers listing, reading, writing, copying,
moving and deleting single objects."""
import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from factory.packs import ToolContext, pack_probe, pack_tool
from factory.packs.s3 import check_bucket, check_key, object_url, parse, raise_for, request, text

PROTOCOL = "s3"

# Tool configuration (inspector → Configuration JSON), all optional:
#   region           SigV4 signing region, default "us-east-1" (Ozone accepts any)
#   max_delete_keys  default 1000 (the S3 limit per request) for delete_objects
# The connection uses auth_mode s3-sigv4 with FACTORY_SECRET_<NAME>="ACCESS_KEY:SECRET_KEY".
DEFAULTS = {"region": "us-east-1", "max_delete_keys": 1000}
TAG_KEY = re.compile(r"^[\w .:/=+@-]{1,128}$")
TAG_VALUE = re.compile(r"^[\w .:/=+@-]{0,256}$")
MAX_TAGS = 10


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def parse_list(value, what):
    """A JSON array of strings, or one item per line or comma. Items containing commas need the JSON form."""
    value = (value or "").strip()
    if value.startswith("["):
        try:
            items = json.loads(value)
        except ValueError as exc:
            raise ValueError(f"{what} is not a valid JSON array") from exc
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise ValueError(f"{what} must be a JSON array of strings")
    else:
        items = [i for line in value.splitlines() for i in line.split(",")]
    items = [i.strip() for i in items if i.strip()]
    if not items:
        raise ValueError(f"Give at least one {what.rstrip('s')}")
    return items


def parse_tags(value):
    """A JSON object, or key=value pairs separated by commas or newlines."""
    value = (value or "").strip()
    if value.startswith("{"):
        try:
            tags = json.loads(value)
        except ValueError as exc:
            raise ValueError("tags is not a valid JSON object") from exc
        if not isinstance(tags, dict) or not all(isinstance(v, str) for v in tags.values()):
            raise ValueError("tags must be a JSON object of string values")
    else:
        tags = {}
        for pair in parse_list(value, "tags"):
            key, separator, item = pair.partition("=")
            if not separator:
                raise ValueError(f"{pair!r} is not a key=value pair")
            tags[key.strip()] = item.strip()
    for key, item in tags.items():
        if not TAG_KEY.match(key):
            raise ValueError(f"Tag key {key!r} must be 1 to 128 letters, digits, spaces or . : / = + - @ _")
        if not TAG_VALUE.match(item):
            raise ValueError(f"Tag value for {key!r} must be at most 256 letters, digits, spaces or . : / = + - @ _")
    return tags


def tagging_xml(tags):
    body = "".join(f"<Tag><Key>{escape(k)}</Key><Value>{escape(v)}</Value></Tag>" for k, v in sorted(tags.items()))
    return f"<Tagging><TagSet>{body}</TagSet></Tagging>".encode()


def read_tags(ctx, bucket, key):
    root = parse(request(ctx, "GET", object_url(bucket, key), params={"tagging": ""}))
    return {text(tag, "Key"): text(tag, "Value") for tag in root.iter("Tag")}


def write_tags(ctx, bucket, key, tags):
    if len(tags) > MAX_TAGS:
        raise ValueError(f"An object can carry at most {MAX_TAGS} tags; it would have {len(tags)}")
    if tags:
        request(ctx, "PUT", object_url(bucket, key), params={"tagging": ""}, content=tagging_xml(tags), headers={"Content-Type": "application/xml"})
    else:
        request(ctx, "DELETE", object_url(bucket, key), params={"tagging": ""})
    return {"bucket": bucket, "key": key, "tags": dict(sorted(tags.items()))}


@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Check that the connection accepts signed S3 requests by listing buckets."""
    count = len(list(parse(request(ctx, "GET", "/")).iter("Bucket")))
    return {"ok": True, "message": f"S3 endpoint accepted the signature; {count} bucket(s) visible"}


@pack_tool(effect="read", requires_connection=True)
def check_bucket_access(ctx: ToolContext, bucket: str) -> dict:
    """Check whether a bucket exists and this connection may use it, without listing it. Say so before working in a bucket a user names."""
    with ctx.client(timeout=30.0) as client:
        response = client.head(object_url(bucket))
    if response.status_code == 404:
        return {"bucket": bucket, "accessible": False, "reason": "NoSuchBucket"}
    if response.status_code == 403:
        return {"bucket": bucket, "accessible": False, "reason": "AccessDenied"}
    raise_for(response)
    return {"bucket": bucket, "accessible": True, "region": response.headers.get("x-amz-bucket-region", "")}


@pack_tool(effect="write", requires_connection=True)
def delete_objects(ctx: ToolContext, bucket: str, keys: str) -> dict:
    """Delete many objects from one bucket in a single request. keys is a JSON array of object keys, or one key per line or comma. Keys that do not exist count as deleted."""
    wanted = [check_key(k) for k in parse_list(keys, "keys")]
    limit = int(setting(ctx, "max_delete_keys"))
    if len(wanted) > limit:
        raise ValueError(f"delete_objects accepts at most {limit} keys per call; split the list")
    body = ("<Delete>" + "".join(f"<Object><Key>{escape(k)}</Key></Object>" for k in wanted) + "</Delete>").encode()
    md5 = base64.b64encode(hashlib.md5(body).digest()).decode()  # S3 requires Content-MD5 on this request
    root = parse(request(ctx, "POST", object_url(bucket), params={"delete": ""}, content=body, headers={"Content-Type": "application/xml", "Content-MD5": md5}))
    deleted = [text(d, "Key") for d in root.iter("Deleted")]
    errors = [{"key": text(e, "Key"), "code": text(e, "Code"), "message": text(e, "Message")} for e in root.iter("Error")]
    return {"bucket": bucket, "deleted": deleted, "errors": errors, "requested": len(wanted)}


@pack_tool(effect="read", requires_connection=True)
def get_object_tags(ctx: ToolContext, bucket: str, key: str) -> dict:
    """Read the tags on an object (up to 10 key=value pairs), for example owner_team=finance or pii=yes."""
    return {"bucket": bucket, "key": key, "tags": dict(sorted(read_tags(ctx, bucket, key).items()))}


@pack_tool(effect="write", requires_connection=True)
def set_object_tags(ctx: ToolContext, bucket: str, key: str, tags: str, replace: bool = False) -> dict:
    """Add or change tags on an object. tags is a JSON object or key=value pairs separated by commas. Existing tags are kept unless replace=true, which makes these the only tags."""
    wanted = parse_tags(tags)
    if not wanted:
        raise ValueError("Give at least one tag")
    merged = wanted if replace else {**read_tags(ctx, bucket, key), **wanted}
    return {**write_tags(ctx, bucket, key, merged), "replaced": replace}


@pack_tool(effect="write", requires_connection=True)
def delete_object_tags(ctx: ToolContext, bucket: str, key: str, names: str = "") -> dict:
    """Remove tags from an object: the named ones (comma-separated) or, with names empty, all of them. The object itself is untouched."""
    if not names.strip():
        request(ctx, "DELETE", object_url(bucket, key), params={"tagging": ""})
        return {"bucket": bucket, "key": key, "tags": {}, "removed": "all"}
    remove = set(parse_list(names, "names"))
    current = read_tags(ctx, bucket, key)
    kept = {k: v for k, v in current.items() if k not in remove}
    return {**write_tags(ctx, bucket, key, kept), "removed": sorted(remove & set(current))}
