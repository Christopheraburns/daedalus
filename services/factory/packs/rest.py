"""Checks for plain REST connections; the HTTP tools themselves are declarative."""
from . import ToolContext, pack_probe


@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Check that the connection's base URL answers HTTP requests with the configured credentials."""
    with ctx.client(timeout=10.0) as client:
        response = client.get("/")
    if response.status_code in (401, 403):
        raise ValueError(f"The API answered {response.status_code}: the connection's credentials were rejected")
    return {"ok": True, "message": f"The API answered HTTP {response.status_code}"}
