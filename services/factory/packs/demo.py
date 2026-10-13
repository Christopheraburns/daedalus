"""Demonstration tools that exercise the executor, caller identity and connections."""
from . import ToolContext, pack_tool

MAX_BODY = 64 * 1024


@pack_tool()
def echo(ctx: ToolContext, text: str) -> dict:
    """Return the given text unchanged. Use it to confirm the server responds."""
    return {"text": text}


@pack_tool()
def whoami(ctx: ToolContext) -> dict:
    """Report which user this server acts for on the current request."""
    return {"username": ctx.caller.username, "token_presented": ctx.caller.token is not None}


@pack_tool(requires_connection=True)
def fetch_json(ctx: ToolContext, path: str, limit: int = 20) -> dict:
    """Fetch a JSON document from the connected API and return at most `limit` top-level items."""
    if not path.startswith("/") or ".." in path:
        raise ValueError("path must be an absolute API path without traversal")
    with ctx.client() as client:
        response = client.get(path)
        response.raise_for_status()
        if len(response.content) > MAX_BODY:
            raise ValueError("Response exceeds 64 KiB")
        document = response.json()
    if isinstance(document, list):
        return {"items": document[:limit], "total": len(document)}
    if isinstance(document, dict):
        return {"items": dict(list(document.items())[:limit]), "total": len(document)}
    return {"value": document}
