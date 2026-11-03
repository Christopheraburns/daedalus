"""Connection authentication strategies: how a tool call becomes a backend identity.

Tools never see credentials. They call `ctx.client()`, which asks `credentials()`
for the headers and query parameters that a connection's `auth_mode` requires
for the current caller. The same modes drive agentgateway's per-target policies
for declarative HTTP tools (see gateway.target_policies).

    none           no credential; the backend is open or network-trusted
    static         a service secret from the Server application's environment
                   (FACTORY_SECRET_*), sent as a bearer token
    basic          a service account's HTTP Basic credential from the environment as
                   FACTORY_SECRET_<NAME>="user:password" (Ranger, Atlas, Recon, LDAP-backed APIs)
    forward-token  the caller's own bearer token, as presented to the gateway
    proxy-doas     a fixed service principal acting as the caller (doAs); the
                   Kerberos/SPNEGO exchange is integrated on the target cluster
    s3-sigv4       an S3 access key pair (Ozone S3 Gateway, MinIO, AWS) from the
                   environment as FACTORY_SECRET_<NAME>="ACCESS_KEY:SECRET_KEY";
                   every request is signed with AWS Signature Version 4
    cdp-apikey     a Cloudera CDP API key from the environment as
                   FACTORY_SECRET_<NAME>="ACCESS_KEY_ID:PRIVATE_KEY" (the two values in the
                   credentials file the CDP console generates); every request to the control
                   plane is signed per CDP request signing V1 (x-altus-date, x-altus-auth)
"""
import base64
import binascii
import datetime
import email.utils
import hashlib
import json
import hmac
import os
import re
from urllib.parse import quote

import httpx

MODES = ("none", "static", "basic", "forward-token", "proxy-doas", "s3-sigv4", "cdp-apikey")
SECRET_REF = re.compile(r"^FACTORY_SECRET_[A-Z0-9_]{1,60}$")


def validate(connection):
    mode = connection.get("auth_mode", "none")
    if mode not in MODES:
        raise ValueError("Unknown authentication mode")
    if mode == "static" and not SECRET_REF.match(connection.get("secret_ref", "")):
        raise ValueError("Static authentication needs a secret reference named FACTORY_SECRET_<NAME>; the value lives in the Server application's environment")
    if mode == "basic" and not SECRET_REF.match(connection.get("secret_ref", "")):
        raise ValueError("Basic authentication needs a secret reference named FACTORY_SECRET_<NAME> whose value is user:password")
    if mode == "s3-sigv4" and not SECRET_REF.match(connection.get("secret_ref", "")):
        raise ValueError("S3 authentication needs a secret reference named FACTORY_SECRET_<NAME> whose value is ACCESS_KEY:SECRET_KEY")
    if mode == "cdp-apikey" and not SECRET_REF.match(connection.get("secret_ref", "")):
        raise ValueError("CDP API key authentication needs a secret reference named FACTORY_SECRET_<NAME> whose value is ACCESS_KEY_ID:PRIVATE_KEY")
    if mode == "proxy-doas":
        if not connection.get("proxy_principal"):
            raise ValueError("Proxy authentication needs the service principal that acts for callers")
        if not SECRET_REF.match(connection.get("keytab_ref", "")):
            raise ValueError("Proxy authentication needs a keytab reference named FACTORY_SECRET_<NAME>")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]{0,39}", connection.get("doas_parameter", "doAs")):
            raise ValueError("The doAs parameter must be a simple query parameter name")


def credentials(connection, caller, environ=None):
    """Headers and query parameters for one backend request on behalf of `caller`."""
    environ = os.environ if environ is None else environ
    mode = (connection or {}).get("auth_mode", "none")
    if mode == "none":
        return {}, {}
    if mode == "static":
        value = environ.get(connection["secret_ref"], "")
        if not value:
            raise ValueError(f"Secret {connection['secret_ref']} is not set in the Server application's environment")
        return {"Authorization": f"Bearer {value}"}, {}
    if mode == "basic":
        return {"Authorization": basic_header(connection, environ)}, {}
    if mode == "forward-token":
        # Live servers with caller identity always have a token; Builder tests and loopback probes run without
        # one, and like REST tools they send no credential rather than inventing one.
        return ({"Authorization": f"Bearer {caller.token}"}, {}) if caller.token else ({}, {})
    if mode in ("s3-sigv4", "cdp-apikey"):
        return {}, {}  # signing happens per request; see s3_auth() and cdp_auth()
    if mode == "proxy-doas":
        # The HTTP shape is settled: the request carries doAs=<caller>; the service identity itself
        # needs a Kerberos ticket from the keytab, which only the target cluster can issue.
        raise ValueError(f"Proxy authentication as {connection['proxy_principal']} for {caller.username} needs Kerberos support that this build does not include; integrate it on the target cluster")
    raise ValueError("Unknown authentication mode")


def basic_header(connection, environ=None):
    """The Authorization header for a basic connection, from FACTORY_SECRET_<NAME>="user:password"."""
    environ = os.environ if environ is None else environ
    value = environ.get(connection["secret_ref"], "")
    if not value:
        raise ValueError(f"Secret {connection['secret_ref']} is not set in the Server application's environment")
    if ":" not in value:
        raise ValueError(f"Secret {connection['secret_ref']} must be set to user:password for Basic authentication")
    return "Basic " + base64.b64encode(value.encode("utf-8")).decode()


def s3_auth(connection, region="us-east-1", environ=None):
    """An httpx auth object that signs requests for an s3-sigv4 connection."""
    environ = os.environ if environ is None else environ
    value = environ.get(connection["secret_ref"], "")
    if ":" not in value:
        raise ValueError(f"Secret {connection['secret_ref']} must be set to ACCESS_KEY:SECRET_KEY in the Server application's environment")
    access_key, secret_key = value.split(":", 1)
    return SigV4Auth(access_key, secret_key, region)


class SigV4Auth(httpx.Auth):
    """AWS Signature Version 4 for S3-compatible services, using only the standard library."""
    requires_request_body = True

    def __init__(self, access_key, secret_key, region="us-east-1", service="s3"):
        self.access_key, self.secret_key, self.region, self.service = access_key, secret_key, region, service

    def auth_flow(self, request):
        now = datetime.datetime.now(datetime.timezone.utc)
        amz_date, scope_date = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(request.content or b"").hexdigest()
        request.headers["x-amz-date"] = amz_date
        request.headers["x-amz-content-sha256"] = payload_hash
        request.headers["host"] = request.url.netloc.decode()
        signed = sorted(name.lower() for name in request.headers if name.lower() == "host" or name.lower().startswith("x-amz-"))
        canonical_headers = "".join(f"{name}:{' '.join(request.headers[name].split())}\n" for name in signed)
        query = "&".join(f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in sorted(request.url.params.multi_items()))
        canonical = "\n".join([request.method, quote(request.url.path, safe="/-_.~"), query, canonical_headers, ";".join(signed), payload_hash])
        scope = f"{scope_date}/{self.region}/{self.service}/aws4_request"
        to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])
        key = b"AWS4" + self.secret_key.encode()
        for part in (scope_date, self.region, self.service, "aws4_request"):
            key = hmac.new(key, part.encode(), hashlib.sha256).digest()
        signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
        request.headers["Authorization"] = f"AWS4-HMAC-SHA256 Credential={self.access_key}/{scope}, SignedHeaders={';'.join(signed)}, Signature={signature}"
        yield request


def cdp_auth(connection, environ=None):
    """An httpx auth object that signs requests for a cdp-apikey connection."""
    environ = os.environ if environ is None else environ
    value = environ.get(connection["secret_ref"], "")
    if ":" not in value:
        raise ValueError(f"Secret {connection['secret_ref']} must be set to ACCESS_KEY_ID:PRIVATE_KEY in the Server application's environment")
    access_key_id, private_key = value.split(":", 1)
    return CdpAuth(access_key_id.strip(), private_key)


def load_cdp_key(private_key):
    """The signing key and CDP method name for a CDP API key's private part: the 44-character base64 Ed25519 seed the
    CDP console issues (ed25519v1), or an RSA private key in PEM form (rsav1, the legacy key type)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
    text = private_key.replace("\\n", "\n").strip()
    if text.startswith("-----BEGIN"):
        try:
            key = serialization.load_pem_private_key(text.encode(), password=None)
        except (ValueError, TypeError) as exc:
            raise ValueError("The CDP private key is not a readable unencrypted PEM key") from exc
        if not isinstance(key, rsa.RSAPrivateKey):
            raise ValueError("CDP API keys are Ed25519 seeds or RSA PEM keys")
        return key, "rsav1"
    try:
        seed = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("The CDP private key must be the 44-character base64 seed from the API key credentials file, or an RSA PEM key") from exc
    if len(seed) != 32:
        raise ValueError("The CDP private key must be the 44-character base64 seed from the API key credentials file, or an RSA PEM key")
    return ed25519.Ed25519PrivateKey.from_private_bytes(seed), "ed25519v1"


class CdpAuth(httpx.Auth):
    """CDP control plane request signing V1, the scheme the cdp CLI uses: x-altus-date carries the request time and
    x-altus-auth carries the access key ID, the signing method and a signature over the method, content type, date,
    path and signing method, each on its own line."""

    def __init__(self, access_key_id, private_key):
        self.access_key_id = access_key_id
        self.key, self.method = load_cdp_key(private_key)

    def string_to_sign(self, method, content_type, date, path):
        return "\n".join([method.upper(), content_type, date, path, self.method])

    def sign(self, text):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        data = text.encode("utf-8")
        return self.key.sign(data) if self.method == "ed25519v1" else self.key.sign(data, padding.PKCS1v15(), hashes.SHA256())

    def auth_flow(self, request):
        date = email.utils.formatdate(usegmt=True)
        signature = self.sign(self.string_to_sign(request.method, request.headers.get("content-type", ""), date, request.url.path))
        metadata = json.dumps({"access_key_id": self.access_key_id, "auth_method": self.method}).encode("utf-8")
        request.headers["x-altus-date"] = date
        request.headers["x-altus-auth"] = base64.urlsafe_b64encode(metadata).decode() + "." + base64.urlsafe_b64encode(signature).decode()
        yield request
