"""Connection authentication strategies: how a tool call becomes a backend identity.

Tools never see credentials. They call `ctx.client()`, which asks `credentials()`
for the headers and query parameters that a connection's `auth_mode` requires
for the current caller. The same modes drive agentgateway's per-target policies
for declarative HTTP tools (see gateway.target_policies).

    none           no credential; the backend is open or network-trusted
    static         a service secret from the Server application's environment
                   (FACTORY_SECRET_*), sent as a bearer token
    forward-token  the caller's own bearer token, as presented to the gateway
    proxy-doas     a fixed service principal acting as the caller (doAs); the
                   Kerberos/SPNEGO exchange is integrated on the target cluster
"""
import os
import re

MODES = ("none", "static", "forward-token", "proxy-doas")
SECRET_REF = re.compile(r"^FACTORY_SECRET_[A-Z0-9_]{1,60}$")


def validate(connection):
    mode = connection.get("auth_mode", "none")
    if mode not in MODES:
        raise ValueError("Unknown authentication mode")
    if mode == "static" and not SECRET_REF.match(connection.get("secret_ref", "")):
        raise ValueError("Static authentication needs a secret reference named FACTORY_SECRET_<NAME>; the value lives in the Server application's environment")
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
    if mode == "forward-token":
        if not caller.token:
            raise ValueError("This connection forwards the caller's token, but the request carried none")
        return {"Authorization": f"Bearer {caller.token}"}, {}
    if mode == "proxy-doas":
        # The HTTP shape is settled: the request carries doAs=<caller>; the service identity itself
        # needs a Kerberos ticket from the keytab, which only the target cluster can issue.
        raise ValueError(f"Proxy authentication as {connection['proxy_principal']} for {caller.username} needs Kerberos support that this build does not include; integrate it on the target cluster")
    raise ValueError("Unknown authentication mode")
