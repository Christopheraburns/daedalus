"""Object storage through the S3 API (Ozone S3 Gateway, MinIO, AWS S3): list buckets and objects, inspect, read, write, copy, move and delete."""
import base64
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from . import ToolContext, pack_probe, pack_tool

PROTOCOL = "s3"

# Tool configuration (inspector → Configuration JSON), all optional:
#   region               SigV4 signing region, default "us-east-1" (Ozone accepts any)
#   max_download_bytes   default 262144; downloads are sliced with offset and max_bytes
#   max_upload_bytes     default 1048576 (decoded inline content)
#   multipart_threshold  default 67108864; larger copies use multipart UploadPartCopy
#   part_size            default 67108864 (minimum 5 MiB) for multipart copies
#   max_copy_bytes       default 5368709120 (5 GiB)
# The connection uses auth_mode s3-sigv4 with FACTORY_SECRET_<NAME>="ACCESS_KEY:SECRET_KEY".
DEFAULTS = {"region": "us-east-1", "max_download_bytes": 256 * 1024, "max_upload_bytes": 1024 * 1024, "multipart_threshold": 64 * 1024 * 1024,
    "part_size": 64 * 1024 * 1024, "max_copy_bytes": 5 * 1024 * 1024 * 1024}
BUCKET = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_bucket(bucket):
    if not BUCKET.match(bucket or ""):
        raise ValueError("Bucket names are 3-63 lowercase letters, digits, dots or hyphens")
    return bucket


def check_key(key):
    if not key or key.startswith("/") or any(part in {".", ".."} for part in key.split("/")) or re.search(r"[\x00-\x1f\x7f]", key):
        raise ValueError("Object keys are relative paths without . or .. segments")
    return key


def object_url(bucket, key=""):
    return f"/{check_bucket(bucket)}" + (f"/{quote(check_key(key), safe='/')}" if key else "")


def parse(response):
    """Parse an S3 XML response with namespaces stripped: implementations differ on whether
    (and on which documents) the 2006-03-01 namespace appears."""
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise ValueError("The S3 endpoint returned a response that is not XML") from exc
    for element in root.iter():
        element.tag = element.tag.rpartition("}")[2]
    return root


def text(element, name, default=""):
    child = element.find(name) if element is not None else None
    return child.text if child is not None and child.text is not None else default


def raise_for(response):
    if response.status_code < 400:
        return
    if response.content:
        try:
            root = ET.fromstring(response.content)
            raise ValueError(f"{root.findtext('Code') or 'S3Error'}: {root.findtext('Message') or ''}"[:400])
        except ET.ParseError:
            pass
    raise ValueError({403: "AccessDenied", 404: "NotFound"}.get(response.status_code, f"HTTP {response.status_code}") + " from the S3 endpoint")


def request(ctx, method, url, **kwargs):
    with ctx.client(timeout=60.0) as client:
        response = client.request(method, url, **kwargs)
    raise_for(response)
    return response


@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Check that the connection accepts signed S3 requests by listing buckets."""
    root = parse(request(ctx, "GET", "/"))
    count = len(list(root.iter("Bucket")))
    return {"ok": True, "message": f"S3 endpoint accepted the signature; {count} bucket(s) visible"}


@pack_tool(effect="read", requires_connection=True)
def list_buckets(ctx: ToolContext) -> dict:
    """List the buckets this connection can see."""
    root = parse(request(ctx, "GET", "/"))
    buckets = [{"name": text(b, "Name"), "created": text(b, "CreationDate")} for b in root.iter("Bucket")]
    return {"buckets": buckets, "total": len(buckets)}


@pack_tool(effect="read", requires_connection=True)
def list_objects(ctx: ToolContext, bucket: str, prefix: str = "", delimiter: str = "/", limit: int = 200, continuation_token: str = "") -> dict:
    """List objects in a bucket under a prefix, folder-style when delimiter is '/'. Use the returned continuation_token to fetch the next page."""
    params = {"list-type": "2", "prefix": prefix, "max-keys": str(max(1, min(limit, 1000)))}
    if delimiter:
        params["delimiter"] = delimiter
    if continuation_token:
        params["continuation-token"] = continuation_token
    root = parse(request(ctx, "GET", object_url(bucket), params=params))
    objects = [{"key": text(c, "Key"), "size": int(text(c, "Size", "0")), "last_modified": text(c, "LastModified"), "etag": text(c, "ETag").strip('"')} for c in root.iter("Contents")]
    prefixes = [text(p, "Prefix") for p in root.iter("CommonPrefixes")]
    return {"bucket": bucket, "prefix": prefix, "objects": objects, "prefixes": prefixes, "truncated": text(root, "IsTruncated") == "true", "continuation_token": text(root, "NextContinuationToken")}


@pack_tool(effect="read", requires_connection=True)
def get_object_info(ctx: ToolContext, bucket: str, key: str) -> dict:
    """Describe one object: size, content type, last modified time, ETag and user metadata."""
    response = request(ctx, "HEAD", object_url(bucket, key))
    metadata = {name[11:]: value for name, value in response.headers.items() if name.lower().startswith("x-amz-meta-")}
    return {"bucket": bucket, "key": key, "size": int(response.headers.get("content-length", 0)), "content_type": response.headers.get("content-type", ""),
        "last_modified": response.headers.get("last-modified", ""), "etag": response.headers.get("etag", "").strip('"'), "metadata": metadata}


@pack_tool(effect="read", requires_connection=True)
def download_object(ctx: ToolContext, bucket: str, key: str, offset: int = 0, max_bytes: int = 65536) -> dict:
    """Read an object's contents. Text is returned as UTF-8, other data as base64; large objects are read in slices with offset and max_bytes."""
    limit = max(1, min(max_bytes, setting(ctx, "max_download_bytes")))
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    response = request(ctx, "GET", object_url(bucket, key), headers={"Range": f"bytes={offset}-{offset + limit}"})
    data = response.content
    total = int(response.headers.get("content-range", "").rpartition("/")[2] or len(data) + offset)
    truncated = offset + limit < total
    data = data[:limit]
    try:
        content, encoding = data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        content, encoding = base64.b64encode(data).decode(), "base64"
    return {"bucket": bucket, "key": key, "offset": offset, "length": len(data), "total": total, "truncated": truncated, "encoding": encoding, "content": content}


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
def upload_object(ctx: ToolContext, bucket: str, key: str, content: str, encoding: str = "utf-8", content_type: str = "", overwrite: bool = False) -> dict:
    """Write an object from inline content (UTF-8 text, or base64 for binary data). Fails if the object exists unless overwrite=true."""
    data = decode_upload(ctx, content, encoding)
    url = object_url(bucket, key)
    if not overwrite:
        with ctx.client(timeout=30.0) as client:
            if client.head(url).status_code == 200:
                raise ValueError(f"Object {key} already exists in {bucket}; pass overwrite=true to replace it")
    headers = {"Content-Type": content_type or ("text/plain; charset=utf-8" if encoding == "utf-8" else "application/octet-stream")}
    response = request(ctx, "PUT", url, content=data, headers=headers)
    return {"bucket": bucket, "key": key, "length": len(data), "etag": response.headers.get("etag", "").strip('"'), "overwritten": overwrite}


def multipart_copy(ctx, source, destination, size):
    """Server-side copy in parts (UploadPartCopy): no bytes flow through the executor."""
    part_size = max(5 * 1024 * 1024, int(setting(ctx, "part_size")))
    with ctx.client(timeout=120.0) as client:
        started = client.post(destination, params={"uploads": ""})
        raise_for(started)
        upload_id = text(parse(started), "UploadId")
        try:
            etags = []
            for number, start in enumerate(range(0, size, part_size), start=1):
                end = min(start + part_size, size) - 1
                part = client.put(destination, params={"partNumber": str(number), "uploadId": upload_id}, headers={"x-amz-copy-source": source, "x-amz-copy-source-range": f"bytes={start}-{end}"})
                raise_for(part)
                etags.append((number, text(parse(part), "ETag")))
            body = "<CompleteMultipartUpload>" + "".join(f"<Part><PartNumber>{n}</PartNumber><ETag>{e}</ETag></Part>" for n, e in etags) + "</CompleteMultipartUpload>"
            completed = client.post(destination, params={"uploadId": upload_id}, content=body.encode(), headers={"Content-Type": "application/xml"})
            raise_for(completed)
            return {"parts": len(etags), "etag": text(parse(completed), "ETag").strip('"')}
        except BaseException:
            client.delete(destination, params={"uploadId": upload_id})
            raise


@pack_tool(effect="write", requires_connection=True)
def copy_object(ctx: ToolContext, source_bucket: str, source_key: str, destination_bucket: str, destination_key: str, overwrite: bool = False) -> dict:
    """Copy an object server-side, using a multipart copy for large objects. Fails if the destination exists unless overwrite=true."""
    size = get_object_info(ctx, source_bucket, source_key)["size"]
    if size > setting(ctx, "max_copy_bytes"):
        raise ValueError(f"Copies are limited to {setting(ctx, 'max_copy_bytes')} bytes for this tool")
    destination = object_url(destination_bucket, destination_key)
    if not overwrite:
        with ctx.client(timeout=30.0) as client:
            if client.head(destination).status_code == 200:
                raise ValueError(f"Object {destination_key} already exists in {destination_bucket}; pass overwrite=true to replace it")
    source = object_url(source_bucket, source_key)
    if size > setting(ctx, "multipart_threshold"):
        result = multipart_copy(ctx, source, destination, size)
        return {"source": f"{source_bucket}/{source_key}", "destination": f"{destination_bucket}/{destination_key}", "size": size, "multipart": True, **result}
    response = request(ctx, "PUT", destination, headers={"x-amz-copy-source": source})
    return {"source": f"{source_bucket}/{source_key}", "destination": f"{destination_bucket}/{destination_key}", "size": size, "multipart": False, "etag": text(parse(response), "ETag").strip('"')}


@pack_tool(effect="write", requires_connection=True)
def move_object(ctx: ToolContext, source_bucket: str, source_key: str, destination_bucket: str, destination_key: str) -> dict:
    """Move or rename an object: a server-side copy followed by deleting the source. The destination must not exist."""
    copied = copy_object(ctx, source_bucket, source_key, destination_bucket, destination_key)
    request(ctx, "DELETE", object_url(source_bucket, source_key))
    return {"source": copied["source"], "destination": copied["destination"], "size": copied["size"], "moved": True}


@pack_tool(effect="write", requires_connection=True)
def delete_object(ctx: ToolContext, bucket: str, key: str) -> dict:
    """Delete one object. Deleting a key that does not exist is not an error."""
    request(ctx, "DELETE", object_url(bucket, key))
    return {"bucket": bucket, "key": key, "deleted": True}
