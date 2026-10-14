"""Loopback HTTP service that runs a release's Python tools; agentgateway is the only client.

agentgateway 1.6.0 forwards a client's MCP protocol version unchanged to `mcp`
targets, so a backend MCP server would have to speak every profile itself. Instead
the executor is an OpenAPI target: the gateway stays the single protocol owner and
Python tools get the same discovery, caching and error handling as HTTP tools.

Started by the controller (live) and by candidate verification (isolated) with a
bundle file and a per-process key. Tool code runs in worker threads.
"""
import argparse
import functools
import json
import logging
import os
from pathlib import Path

import anyio
from jsonschema import Draft202012Validator, ValidationError
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import packs
from .gateway import KEY_HEADER, TOKEN_HEADER, USER_HEADER

MAX_RESULT = 1024 * 1024
log = logging.getLogger("factory.executor")


def caller_from(request, default_user):
    token = request.headers.get(TOKEN_HEADER, "").removeprefix("Bearer ").strip()
    return packs.Caller(username=request.headers.get(USER_HEADER) or default_user, token=token or None)


class KeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, key):
        super().__init__(app)
        self.key = key

    async def dispatch(self, request, call_next):
        if request.url.path != "/healthz" and request.headers.get(KEY_HEADER) != self.key:
            return JSONResponse({"error": "Executor key required"}, status_code=401)
        return await call_next(request)


def materialize(bundle, directory):
    """Write the release's project pack snapshot next to the bundle for import."""
    folder = Path(directory) / "packs"
    folder.mkdir(parents=True, exist_ok=True)
    for name, source in bundle.get("pack_sources", {}).items():
        (folder / f"{name}.py").write_text(source)
    return folder


def build_app(bundle, key, default_user="development", directory="."):
    tools = {}
    search = [materialize(bundle, directory)]
    for tool in bundle.get("python_tools", []):
        function = packs.resolve(tool["pack"], tool["function"], search)
        connection = bundle["connections"].get(tool["connection_id"]) if tool.get("connection_id") else None
        tools[tool["name"]] = (tool, function, connection, Draft202012Validator(tool["input_schema"]))

    async def call(request):
        entry = tools.get(request.path_params["name"])
        if entry is None:
            return JSONResponse({"error": "Unknown tool"}, status_code=404)
        tool, function, connection, validator = entry
        body = await request.body()
        try:
            arguments = json.loads(body) if body.strip() else {}
            validator.validate(arguments)
        except (ValueError, ValidationError) as exc:
            return JSONResponse({"error": "Invalid arguments: " + str(exc).split("\n")[0][:300]}, status_code=422)
        context = packs.ToolContext(caller=caller_from(request, default_user), connection=connection, config=dict(tool.get("config", {})))
        try:
            result = await anyio.to_thread.run_sync(functools.partial(function, context, **arguments))
            payload = json.dumps(result)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)[:600]}, status_code=422)
        except Exception as exc:
            log.warning("tool %s failed: %s", tool["name"], exc)
            return JSONResponse({"error": f"{type(exc).__name__}: {str(exc)[:600]}"}, status_code=502)
        if len(payload) > MAX_RESULT:
            return JSONResponse({"error": "Tool result exceeds 1 MiB"}, status_code=502)
        return JSONResponse(result)

    def health(request):
        return JSONResponse({"status": "ok", "tools": len(tools)})

    return Starlette(routes=[Route("/healthz", health), Route("/tools/{name}", call, methods=["POST"])], middleware=[Middleware(KeyMiddleware, key=key)])


def main():
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s executor %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    options = parser.parse_args()
    key = os.environ.get("FACTORY_EXECUTOR_KEY", "")
    if len(key) < 32:
        raise SystemExit("FACTORY_EXECUTOR_KEY must be set by the supervising process")
    bundle = json.loads(Path(options.bundle).read_text())
    app = build_app(bundle, key, os.getenv("FACTORY_EXECUTOR_DEFAULT_USER", "development"), Path(options.bundle).parent)
    log.info("serving %d Python tools on %s:%d", len(bundle.get("python_tools", [])), options.host, options.port)
    uvicorn.run(app, host=options.host, port=options.port, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
