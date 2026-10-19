import hmac
import ipaddress
import json
import socket
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jsonschema import Draft202012Validator
from sqlalchemy import select, text

from .compiler import compile_bundle, digest, fingerprint, validate_connection, validate_tool
from . import auth, mcp_client, packs
from .packs import Caller
from .contracts import ApiOriginSpec, ConnectionSpec, DeploymentAction, LayoutSpec, PackSource, PublishRequest, RollbackRequest, ServerSpec, TestRequest, ToolSpec
from .db import ApiOrigin, Audit, Connection, Deployment, Layout, Release, Server, Tool, audit, database, new_id
from .gateway import candidate, rpc
from .settings import MODERN, SERVER_ID, Settings


def create_app(settings=None):
    settings = settings or Settings()
    identities = settings.identities()
    engine, sessions = database(settings.database_url)
    slots = threading.BoundedSemaphore(2)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(title="Daedalus Builder", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def bounds(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin not in settings.browser_origins:
            return JSONResponse({"detail": "Origin is not allowed"}, status_code=403)
        # Bound streamed requests too, not only trusted Content-Length values.
        if request.method in {"POST", "PUT", "PATCH"}:
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 256 * 1024:
                    return JSONResponse({"detail": "Request exceeds 256 KiB"}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    def identity(authorization: str = Header(default="")):
        if settings.auth_mode == "development-open":
            return "administrator"
        value = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
        for token, role in identities:
            if hmac.compare_digest(value.encode(), token.encode()):
                return role
        raise HTTPException(401, "A valid management token is required", headers={"WWW-Authenticate": "Bearer"})

    def require(*roles):
        def dependency(role=Depends(identity)):
            if role != "administrator" and role not in roles:
                raise HTTPException(403, "Your role does not permit this action")
            return role
        return dependency

    def policy_origins(session, server_id):
        rows = list(session.scalars(select(ApiOrigin).where(ApiOrigin.server_id == server_id, ApiOrigin.enabled.is_(True)).order_by(ApiOrigin.origin)))
        return [row.origin for row in rows] or settings.allowed_origins

    def origin_value(value):
        parsed = urlsplit(value.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("Use an HTTP(S) origin without credentials, path, query, or fragment")
        return f"{parsed.scheme}://{parsed.netloc}"

    def origin_json(item):
        return {"id": item.id, "server_id": item.server_id, "revision": item.revision, "origin": item.origin, "description": item.description, "enabled": item.enabled, "created_at": item.created_at.isoformat()}

    def selected(server_id):
        return server_id or SERVER_ID

    def server_lock(session, server_id):
        server = session.scalar(select(Server).where(Server.id == selected(server_id)).with_for_update())
        if not server:
            raise HTTPException(503, "Registry not initialized; run migrations")
        return server

    def revision(current, provided):
        if provided is None:
            raise HTTPException(428, "If-Match revision is required")
        if provided.strip('"') != str(current):
            raise HTTPException(409, "This record changed. Reload before saving")

    def get(session, model, id):
        item = session.get(model, id)
        if item is None:
            raise HTTPException(404, "Record not found")
        return item

    def connection_json(item):
        return {"id": item.id, "revision": item.revision, **item.spec, "probe_summary": item.probe_summary, "discovered": item.discovered}

    def connection_bundle_spec(item):
        """The connection as the compiler sees it: mcp connections carry their discovered tool names."""
        return {**item.spec, "_discovered": [t["name"] for t in item.discovered or []]} if item.spec.get("protocol") == "mcp" else item.spec

    def connection_spec(session, item):
        return get(session, Connection, item.connection_id).spec if item.connection_id else None

    def tool_json(session, item, server_id):
        fp = fingerprint(item.spec, connection_spec(session, item))
        server = get(session, Server, selected(server_id))
        active = session.get(Release, server.active_release_id) if server.active_release_id else None
        published = bool(active and item.spec["enabled"] and any(t["id"] == item.id and t["fingerprint"] == fp for t in active.bundle["tools"]))
        return {"id": item.id, "revision": item.revision, **item.spec, "validated": item.validated_fingerprint == fp, "tested": item.tested_fingerprint == fp, "published": published, "test_summary": item.test_summary}

    def snapshot(session, server_id):
        server_id = selected(server_id)
        connections = {c.id: connection_bundle_spec(c) for c in session.scalars(select(Connection).where(Connection.server_id == server_id))}
        tools = [{"id": t.id, "revision": t.revision, "spec": t.spec, "fingerprint": fingerprint(t.spec, connections.get(t.connection_id))} for t in session.scalars(select(Tool).where(Tool.server_id == server_id).order_by(Tool.id))]
        return tools, connections

    def publish_checks(session, tools, server_id=None):
        problems = []
        for t in tools:
            if t["spec"]["enabled"] and get(session, Tool, t["id"]).tested_fingerprint != t["fingerprint"]:
                problems.append(f"{t['spec']['name']}: test the current definition successfully before publishing")
        if server_id:
            for c in session.scalars(select(Connection).where(Connection.server_id == server_id)):
                if c.spec.get("protocol") == "mcp" and c.spec.get("federate") and not (c.probe_summary or {}).get("success"):
                    problems.append(f"{c.spec['name']}: check the MCP connection to discover its tools before publishing")
                elif c.spec.get("protocol") == "mcp" and c.spec.get("federate") and (c.probe_summary or {}).get("federation_ok") is False:
                    problems.append(f"{c.spec['name']}: cannot be federated because it does not implement server/discover; turn off \"Serve this server's tools from here\" and add its tools individually")
        return problems

    def federated_names(bundle):
        return [name for entry in bundle.get("federated", []) for name in entry["tools"]]

    def release_json(release):
        return {"id": release.id, "status": release.status, "checksum": release.checksum, "error": release.error, "created_at": release.created_at.isoformat(), "created_by": release.created_by, "tool_names": [t["spec"]["name"] for t in release.bundle["tools"]] + federated_names(release.bundle)}

    def deployment_json(deployment):
        return {"id": deployment.id, "revision": deployment.revision, "status": deployment.status,
            "desired_release_id": deployment.desired_release_id, "deployed_release_id": deployment.deployed_release_id,
            "application_name": deployment.application_name, "application_id": deployment.application_id,
            "endpoint": deployment.endpoint, "provider": deployment.provider, "message": deployment.message,
            "metrics": deployment.metrics, "updated_at": deployment.updated_at.isoformat()}

    def safe_error(exc):
        # Known credentials never reach responses or audit, including upstream echoes.
        message = str(exc)[:1200]
        for token in [*(t for t, _ in identities), settings.gateway_token, settings.cloudera_api_token]:
            if token:  # an empty credential would otherwise redact between every character
                message = message.replace(token, "[REDACTED]")
        return message

    @app.get("/healthz")
    def health():
        return {"status": "ok", "application": "builder"}

    @app.get("/readyz")
    def ready():
        try:
            with sessions() as session:
                session.execute(text("SELECT 1 FROM servers LIMIT 1"))
        except Exception:
            raise HTTPException(503, "Registry is unavailable")
        return {"status": "ready"}

    @app.get("/api/servers")
    def servers(role=Depends(identity)):
        with sessions() as session:
            return [{"id": s.id, "name": s.name, "revision": s.revision, "active_release_id": s.active_release_id,
                "deployment": deployment_json(session.scalar(select(Deployment).where(Deployment.server_id == s.id)))}
                for s in session.scalars(select(Server).order_by(Server.name))]

    @app.post("/api/openapi/preview")
    def openapi_preview(request: dict, role=Depends(identity)):
        url = request.get("url", "") if isinstance(request, dict) else ""
        if not isinstance(url, str) or len(url) > 500 or not url.startswith(("http://", "https://")):
            raise HTTPException(422, "OpenAPI URL must be an HTTP(S) URL")
        from urllib.parse import urlsplit
        parsed = urlsplit(url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname:
            raise HTTPException(422, "OpenAPI URL cannot contain credentials, query parameters, or fragments")
        try:
            addresses = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
            if any(address.is_private or address.is_loopback or address.is_link_local or address.is_reserved for address in addresses):
                raise HTTPException(422, "OpenAPI URL resolves to a private or local address")
        except socket.gaierror:
            raise HTTPException(422, "OpenAPI host could not be resolved")
        import httpx
        try:
            response = httpx.get(url, follow_redirects=False, timeout=10, trust_env=False, headers={"Accept": "application/json, application/yaml, text/yaml"})
            response.raise_for_status()
            if len(response.content) > 1024 * 1024:
                raise HTTPException(422, "OpenAPI document exceeds 1 MiB")
            import yaml
            document = json.loads(response.text) if "json" in response.headers.get("content-type", "") or response.text.lstrip().startswith(("{", "[")) else yaml.safe_load(response.text)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(422, f"Could not load OpenAPI document: {str(exc)[:240]}")
        if not isinstance(document, dict) or not (document.get("openapi") or document.get("swagger")) or not isinstance(document.get("paths"), dict):
            raise HTTPException(422, "Document must contain OpenAPI/Swagger metadata and a paths object")
        servers = document.get("servers") or []
        base_url = servers[0].get("url") if servers and isinstance(servers[0], dict) else f"{parsed.scheme}://{parsed.netloc}"
        if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
        operations = []
        for path, path_item in document["paths"].items():
            if not isinstance(path, str) or not isinstance(path_item, dict): continue
            for method, operation in path_item.items():
                if method.lower() not in methods or not isinstance(operation, dict): continue
                params = []
                for parameter in [*(path_item.get("parameters") or []), *(operation.get("parameters") or [])]:
                    if not isinstance(parameter, dict) or parameter.get("in") not in {"path", "query"}: continue
                    schema = parameter.get("schema") or {}
                    params.append({"name": parameter.get("name", "parameter"), "location": parameter["in"], "type": schema.get("type", "string") if schema.get("type") in {"string", "integer", "number", "boolean"} else "string", "required": bool(parameter.get("required", parameter["in"] == "path")), "description": parameter.get("description", "")})
                body = None
                request_body = operation.get("requestBody", {})
                if isinstance(request_body, dict):
                    body = ((request_body.get("content") or {}).get("application/json") or {}).get("schema")
                operations.append({"method": method.upper(), "path": path, "name": operation.get("operationId") or f"{method}_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '') or 'root'}", "description": operation.get("summary") or operation.get("description") or f"{method.upper()} {path}", "parameters": params, "body_schema": body if isinstance(body, dict) else None, "effect": "write" if method.lower() in {"post", "put", "patch", "delete"} else "read", "supported": method.lower() in {"get", "post"}})
        return {"title": (document.get("info") or {}).get("title", parsed.hostname), "version": (document.get("info") or {}).get("version", ""), "base_url": base_url.rstrip("/"), "operations": operations[:200], "truncated": len(operations) > 200}

    @app.post("/api/servers", status_code=201)
    def create_server(spec: ServerSpec, role=Depends(require("author"))):
        with sessions.begin() as session:
            server = Server(id=new_id(), name=spec.name)
            session.add(server); session.flush()
            session.add(Layout(server_id=server.id)); session.add(Deployment(server_id=server.id, provider=settings.deployment_provider))
            for origin in settings.allowed_origins:
                if origin:
                    session.add(ApiOrigin(server_id=server.id, origin=origin, description="Environment bootstrap origin"))
            audit(session, role, "server.create", server.id, name=server.name)
            return {"id": server.id, "name": server.name, "revision": server.revision}

    @app.get("/api/workspace")
    def workspace(server_id: str | None = Query(default=None), role=Depends(identity)):
        with sessions() as session:
            server_id = selected(server_id)
            server = get(session, Server, server_id)
            layout = get(session, Layout, server_id)
            deployment = session.scalar(select(Deployment).where(Deployment.server_id == server_id))
            active = session.get(Release, server.active_release_id) if server.active_release_id else None
            runtime = dict(server.runtime)
            heartbeat = runtime.get("heartbeat")
            runtime["online"] = bool(heartbeat and (datetime.now(timezone.utc) - datetime.fromisoformat(heartbeat)).total_seconds() < 12)
            return {"identity": {"role": role, "mode": settings.auth_mode},
                "server": {"id": server.id, "name": server.name, "revision": server.revision, "desired_release_id": server.desired_release_id, "active_release_id": server.active_release_id, "mcp_url": settings.public_mcp_url, "runtime": runtime},
                "connections": [connection_json(c) for c in session.scalars(select(Connection).where(Connection.server_id == server_id).order_by(Connection.id))],
                "tools": [tool_json(session, t, server_id) for t in session.scalars(select(Tool).where(Tool.server_id == server_id).order_by(Tool.id))],
                "layout": {"revision": layout.revision, "positions": layout.positions},
                "active_tools": active.bundle["tools"] if active else [],
                "releases": [release_json(r) for r in session.scalars(select(Release).where(Release.server_id == server_id).order_by(Release.created_at.desc()).limit(20))],
                "deployment": deployment_json(deployment),
                "allowed_api_origins": policy_origins(session, server_id),
                "limits": {"methods": ["GET", "POST"], "parameter_locations": ["path", "query"], "max_tools": 100, "kinds": ["http", "python"]}}

    @app.get("/api/packs")
    def list_packs(role=Depends(identity)):
        return packs.catalog()

    @app.get("/api/packs/{name}")
    def get_pack(name: str, role=Depends(identity)):
        try:
            return packs.pack_info(name)
        except ValueError as exc:
            raise HTTPException(404, str(exc))

    # Project packs are code that runs inside Server applications; only administrators write them.
    @app.put("/api/packs/{name}")
    def save_pack(name: str, request: PackSource, role=Depends(require())):
        try:
            info = packs.save_project_pack(name, request.source)
        except (ValueError, SyntaxError) as exc:
            raise HTTPException(422, str(exc))
        with sessions.begin() as session:
            audit(session, role, "pack.save", f"pack:{name}", tools=[t["function"] for t in info["tools"]])
        return info

    @app.delete("/api/packs/{name}", status_code=204)
    def delete_pack(name: str, role=Depends(require())):
        with sessions.begin() as session:
            if session.scalar(select(Tool.id).where(Tool.spec["pack"].as_string() == name)):
                raise HTTPException(409, "Remove the tools that use this pack before deleting it")
            try:
                packs.delete_project_pack(name)
            except ValueError as exc:
                raise HTTPException(404, str(exc))
            audit(session, role, "pack.delete", f"pack:{name}")

    @app.get("/api/policies/origins")
    def list_origins(server_id: str | None = Query(default=None), role=Depends(identity)):
        with sessions() as session:
            server_id = selected(server_id); rows = list(session.scalars(select(ApiOrigin).where(ApiOrigin.server_id == server_id).order_by(ApiOrigin.origin)))
            if not rows:
                return [{"id": f"bootstrap-{index}", "server_id": server_id, "revision": 0, "origin": origin, "description": "Environment bootstrap origin", "enabled": True, "bootstrap": True} for index, origin in enumerate(settings.allowed_origins) if origin]
            return [origin_json(row) for row in rows]

    @app.post("/api/policies/origins", status_code=201)
    def create_origin(spec: ApiOriginSpec, server_id: str | None = Query(default=None), role=Depends(require("author"))):
        try: origin = origin_value(spec.origin)
        except ValueError as exc: raise HTTPException(422, str(exc))
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            if session.scalar(select(ApiOrigin).where(ApiOrigin.server_id == server_id, ApiOrigin.origin == origin)):
                raise HTTPException(409, "This API origin is already registered")
            item = ApiOrigin(server_id=server_id, origin=origin, description=spec.description, enabled=spec.enabled)
            session.add(item); server.revision += 1; session.flush(); audit(session, role, "policy.origin.create", item.id, origin=origin)
            return origin_json(item)

    @app.patch("/api/policies/origins/{id}")
    def update_origin(id: str, spec: ApiOriginSpec, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        try: origin = origin_value(spec.origin)
        except ValueError as exc: raise HTTPException(422, str(exc))
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id); item = get(session, ApiOrigin, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match); item.origin, item.description, item.enabled, item.revision = origin, spec.description, spec.enabled, item.revision + 1
            server.revision += 1; audit(session, role, "policy.origin.update", id, origin=origin); return origin_json(item)

    @app.delete("/api/policies/origins/{id}", status_code=204)
    def delete_origin(id: str, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id); item = get(session, ApiOrigin, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match); session.delete(item); server.revision += 1; audit(session, role, "policy.origin.delete", id, origin=item.origin)

    @app.post("/api/connections", status_code=201)
    def create_connection(spec: ConnectionSpec, server_id: str | None = Query(default=None), role=Depends(require())):
        data = spec.model_dump()
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            try:
                validate_connection(data, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
            item = Connection(spec=data, server_id=server_id)
            session.add(item)
            session.flush()
            server.revision += 1
            audit(session, role, "connection.create", item.id)
            return connection_json(item)

    @app.patch("/api/connections/{id}")
    def update_connection(id: str, spec: ConnectionSpec, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require())):
        data = spec.model_dump()
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            item = get(session, Connection, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match)
            try:
                validate_connection(data, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
            item.spec, item.revision = data, item.revision + 1
            item.probe_summary, item.discovered = None, None  # the endpoint or credentials changed; check again
            server.revision += 1
            audit(session, role, "connection.update", id)
            return connection_json(item)

    def tool_connection(session, spec, server_id):
        """The tool's connection, checked for workspace ownership; Python tools may have none.
        Python tools are validated immediately so unknown packs never become drafts."""
        connection = get(session, Connection, spec.connection_id) if spec.connection_id else None
        if connection and connection.server_id != server_id: raise HTTPException(422, "Connection belongs to another server")
        if spec.kind == "python":
            try:
                validate_tool(spec.model_dump(), connection.spec if connection else None, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
        return connection

    def tool_data(session, spec, server_id):
        """The stored tool spec. MCP tools take their input schema from the connection's discovery,
        never from the client, so a release always matches what the upstream advertised."""
        connection = tool_connection(session, spec, server_id)
        data = spec.model_dump()
        if spec.kind == "mcp":
            if connection is None or connection.spec.get("protocol") != "mcp":
                raise HTTPException(422, "MCP tools need an mcp connection")
            found = next((t for t in connection.discovered or [] if t["name"] == spec.upstream_tool), None)
            if found is None:
                raise HTTPException(422, f"{connection.spec['name']} has no discovered tool named {spec.upstream_tool}; check the connection again")
            data["input_schema"], data["wrap_body"] = found["input_schema"], bool(found.get("wrap_body"))
            try:
                validate_tool(data, connection.spec, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
        return data

    @app.post("/api/tools", status_code=201)
    def create_tool(spec: ToolSpec, server_id: str | None = Query(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            data = tool_data(session, spec, server_id)
            tools = list(session.scalars(select(Tool).where(Tool.server_id == server_id)))
            if len(tools) >= 100:
                raise HTTPException(422, "This profile supports at most 100 tools")
            if any(t.spec["name"] == spec.name for t in tools):
                raise HTTPException(409, "Tool name is already in use")
            item = Tool(server_id=server_id, spec=data, connection_id=spec.connection_id)
            session.add(item)
            session.flush()
            server.revision += 1
            audit(session, role, "tool.create", item.id)
            return tool_json(session, item, server_id)

    @app.patch("/api/tools/{id}")
    def update_tool(id: str, spec: ToolSpec, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            item = get(session, Tool, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match)
            data = tool_data(session, spec, server_id)
            if any(t.id != id and t.spec["name"] == spec.name for t in session.scalars(select(Tool).where(Tool.server_id == server_id))):
                raise HTTPException(409, "Tool name is already in use")
            item.spec, item.connection_id = data, spec.connection_id
            item.revision += 1
            server.revision += 1
            audit(session, role, "tool.update", id)
            return tool_json(session, item, server_id)

    @app.delete("/api/tools/{id}", status_code=204)
    def delete_tool(id: str, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            item = get(session, Tool, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match)
            layout = session.scalar(select(Layout).where(Layout.server_id == server_id).with_for_update())
            if layout and id in layout.positions:
                layout.positions = {key: value for key, value in layout.positions.items() if key != id}
                layout.revision += 1
            session.delete(item)
            server.revision += 1
            audit(session, role, "tool.delete", id)

    @app.post("/api/connections/{id}/check")
    def check_connection(id: str, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        """Probe the endpoint through an isolated candidate (the pack's probe for rest/webhdfs/s3) or, for an
        mcp connection, discover the upstream tools. The result is stored on the connection and shown on the canvas."""
        if not slots.acquire(blocking=False):
            raise HTTPException(429, "Two tests/compilations are already running; try again shortly")
        try:
            with sessions() as session:
                server_id = selected(server_id); item = get(session, Connection, id)
                if item.server_id != server_id: raise HTTPException(404, "Record not found")
                revision(item.revision, if_match)
                spec, origins = item.spec, policy_origins(session, server_id)
            started = time.monotonic()
            protocol = spec.get("protocol", "rest")
            discovered = None
            try:
                if protocol == "mcp":
                    validate_connection(spec, origins)
                    headers, params = auth.credentials(spec, Caller("builder"))
                    url = str(httpx.URL(spec["base_url"], params=params)) if params else spec["base_url"]
                    discovered, profile = mcp_client.discover(url, headers)
                    summary = {"success": True, "message": f"{len(discovered)} tools discovered ({'protocol ' + MODERN if profile == 'modern' else 'protocol ' + str(profile)})", "pack": None}
                    if spec.get("federate"):
                        # Federation goes through agentgateway, which starts every request with server/discover.
                        summary["federation_ok"] = profile == "modern" and mcp_client.supports_discover(url, headers)
                        if not summary["federation_ok"]:
                            summary["message"] += "; it cannot be federated (no server/discover on protocol " + MODERN + "), add its tools individually instead"
                else:
                    available = packs.probes(protocol)
                    if not available:
                        raise HTTPException(422, f"No installed pack can check a {protocol} connection")
                    pack = available[0][0]
                    probe = {"id": "probe", "revision": 1, "fingerprint": "", "spec": ToolSpec(name="probe", description=available[0][1], kind="python", pack=pack, function="probe", connection_id=id).model_dump()}
                    bundle = compile_bundle([probe], {id: spec}, origins)
                    with candidate(bundle, settings) as (url, token, _):
                        result = rpc(url, token, "tools/call", {"name": "probe", "arguments": {}})
                    payload = result.get("structuredContent") or {}
                    failure = payload.get("error") if isinstance(payload, dict) else None
                    summary = {"success": not result.get("isError") and not failure, "message": safe_error(Exception(failure)) if failure else payload.get("message", "Connection answered"), "pack": pack}
            except HTTPException:
                raise
            except Exception as exc:
                summary = {"success": False, "message": safe_error(exc), "pack": None}
            summary.update(duration_ms=round((time.monotonic() - started) * 1000), checked_at=datetime.now(timezone.utc).isoformat())
            with sessions.begin() as session:
                server_lock(session, server_id)
                current = get(session, Connection, id)
                if current.revision != int(if_match.strip('"')):
                    raise HTTPException(409, "Connection changed during the check; run it again")
                current.probe_summary = summary
                if discovered is not None:
                    current.discovered = discovered
                audit(session, role, "connection.check", id, success=summary["success"], message=summary["message"][:200])
                return connection_json(current)
        finally:
            slots.release()

    @app.delete("/api/connections/{id}", status_code=204)
    def delete_connection(id: str, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            item = get(session, Connection, id)
            if item.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(item.revision, if_match)
            if session.scalar(select(Tool.id).where(Tool.server_id == server_id, Tool.connection_id == id)):
                raise HTTPException(409, "Remove or reassign this connection's tools before deleting it")
            layout = session.scalar(select(Layout).where(Layout.server_id == server_id).with_for_update())
            if layout and id in layout.positions:
                layout.positions = {key: value for key, value in layout.positions.items() if key != id}
                layout.revision += 1
            session.delete(item)
            server.revision += 1
            audit(session, role, "connection.delete", id)

    @app.put("/api/layout")
    def save_layout(spec: LayoutSpec, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id)
            layout = session.scalar(select(Layout).where(Layout.server_id == server_id).with_for_update())
            revision(layout.revision, if_match)
            valid = {server_id} | set(session.scalars(select(Tool.id).where(Tool.server_id == server_id))) | set(session.scalars(select(Connection.id).where(Connection.server_id == server_id)))
            if set(spec.positions) - valid:
                raise HTTPException(422, "Layout contains unknown records")
            layout.positions = spec.model_dump()["positions"]
            layout.revision += 1
            return {"revision": layout.revision, "positions": layout.positions}

    @app.post("/api/tools/{id}/validate")
    def validate(id: str, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        with sessions.begin() as session:
            server_id = selected(server_id); server_lock(session, server_id)
            tool = get(session, Tool, id)
            if tool.server_id != server_id: raise HTTPException(404, "Record not found")
            revision(tool.revision, if_match)
            conn = connection_spec(session, tool)
            try:
                validate_tool(tool.spec, conn, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
            tool.validated_fingerprint = fingerprint(tool.spec, conn)
            audit(session, role, "tool.validate", id)
            profile = f"Python pack {tool.spec['pack']}.{tool.spec['function']} served by the executor" if tool.spec.get("kind") == "python" else "OpenAPI 3.0.3: scalar path/query parameters and JSON object bodies"
            return {"valid": True, "profile": profile}

    @app.post("/api/tools/{id}/test")
    def test_tool(id: str, request: TestRequest, server_id: str | None = Query(default=None), if_match: str | None = Header(default=None), role=Depends(require("author"))):
        if not slots.acquire(blocking=False):
            raise HTTPException(429, "Two tests/compilations are already running; try again shortly")
        try:
            with sessions() as session:
                server_id = selected(server_id); tool = get(session, Tool, id)
                if tool.server_id != server_id: raise HTTPException(404, "Record not found")
                revision(tool.revision, if_match)
                conn = connection_spec(session, tool)
                fp = fingerprint(tool.spec, conn)
                if tool.spec["effect"] == "write" and not request.confirm_write:
                    raise HTTPException(422, "Confirm the live write test explicitly")
                tool_data = {"id": tool.id, "revision": tool.revision, "spec": {**tool.spec, "enabled": True}, "fingerprint": fp}
                # A tool test covers this tool only; a federated connection's whole server is not part of it.
                isolated = {**conn, "federate": False} if conn and conn.get("protocol") == "mcp" else conn
                bundle = compile_bundle([tool_data], {tool.connection_id: isolated} if conn else {}, policy_origins(session, server_id))
            started = time.monotonic()
            log = []

            def event(code, level="info", **values):
                # Values are redacted like errors; the UI renders each code in the selected language.
                log.append({"t": round((time.monotonic() - started) * 1000), "level": level, "code": code,
                    "values": {k: safe_error(Exception(str(v)))[:600] for k, v in values.items()}})

            kind = tool_data["spec"].get("kind", "http")
            event("bundle_compiled", name=tool_data["spec"]["name"], kind=kind, connection=(conn or {}).get("name", "-"))
            try:
                with candidate(bundle, settings, events=event) as (url, token, tools):
                    Draft202012Validator(tools[0]["inputSchema"]).validate(request.arguments)
                    event("arguments_validated")
                    event("calling_tool", name=tool_data["spec"]["name"])
                    called = time.monotonic()
                    result = rpc(url, token, "tools/call", {"name": tool_data["spec"]["name"], "arguments": request.arguments})
                    elapsed = round((time.monotonic() - called) * 1000)
                    structured = result.get("structuredContent")
                    success = not result.get("isError", False)
                    if isinstance(structured, dict) and set(structured) == {"error"}:
                        # Packs and MCP tools report failures this way (the gateway does not set isError); a test
                        # that ends in an error must not qualify the tool for publishing.
                        success = False
                        event("tool_reported_error", level="error", ms=elapsed, message=structured["error"])
                    elif success:
                        event("tool_returned", level="success", ms=elapsed)
                    else:
                        event("tool_failed", level="error", ms=elapsed)
                    # Remove temporary candidate credentials if a backend echoes them.
                    result = json.loads(safe_error_json(result, token))
                outcome = {"success": success, "result": result, "input_schema": tools[0]["inputSchema"]}
            except Exception as exc:
                outcome = {"success": False, "error": safe_error(exc)}
                event("test_failed", level="error", message=outcome["error"])
            outcome["duration_ms"] = round((time.monotonic() - started) * 1000)
            outcome["log"] = log
            with sessions.begin() as session:
                server_lock(session, server_id)
                current = get(session, Tool, id)
                if current.server_id != server_id: raise HTTPException(404, "Record not found")
                if fingerprint(current.spec, connection_spec(session, current)) != fp:
                    raise HTTPException(409, "Definition changed during testing; result cannot qualify this draft")
                current.tested_fingerprint = fp if outcome["success"] else None
                if outcome["success"]:
                    current.validated_fingerprint = fp
                current.test_summary = {"success": outcome["success"], "duration_ms": outcome["duration_ms"], "tested_at": datetime.now(timezone.utc).isoformat()}
                audit(session, role, "tool.test", id, **current.test_summary)
            return outcome
        except ValueError as exc:
            raise HTTPException(422, safe_error(exc))
        finally:
            slots.release()

    def safe_error_json(result, candidate_token):
        output = json.dumps(result)
        for token in [candidate_token, settings.gateway_token, *[t for t, _ in identities]]:
            if token:
                output = output.replace(token, "[REDACTED]")
        return output

    @app.get("/api/releases/preview")
    def preview(server_id: str | None = Query(default=None), role=Depends(identity)):
        with sessions() as session:
            server_id = selected(server_id); server = get(session, Server, server_id)
            tools, connections = snapshot(session, server_id)
            problems = publish_checks(session, tools, server_id)
            federated_after = []
            try:
                federated_after = federated_names(compile_bundle(tools, connections, policy_origins(session, server_id)))
            except ValueError as exc:
                problems.append(str(exc))
            active = session.get(Release, server.active_release_id) if server.active_release_id else None
            before = {t["id"]: t for t in active.bundle["tools"]} if active else {}
            after = {t["id"]: t for t in tools if t["spec"]["enabled"]}
            federated_before = federated_names(active.bundle) if active else []
            return {"revision": server.revision, "added": [t["spec"]["name"] for id, t in after.items() if id not in before] + [n for n in federated_after if n not in federated_before],
                "changed": [t["spec"]["name"] for id, t in after.items() if id in before and t["fingerprint"] != before[id]["fingerprint"]],
                "removed": [t["spec"]["name"] for id, t in before.items() if id not in after] + [n for n in federated_before if n not in federated_after], "problems": problems}

    def enqueue(bundle, expected_revision, actor, server_id):
        if not slots.acquire(blocking=False):
            raise HTTPException(429, "Two tests/compilations are already running; try again shortly")
        try:
            with candidate(bundle, settings):
                pass
        except Exception as exc:
            raise HTTPException(422, "Candidate release failed: " + safe_error(exc))
        finally:
            slots.release()
        with sessions.begin() as session:
            server_id = selected(server_id); server = server_lock(session, server_id)
            revision(server.revision, str(expected_revision))
            desired = session.get(Release, server.desired_release_id) if server.desired_release_id else None
            if desired and desired.status in {"pending", "applying"}:
                raise HTTPException(409, "A release is already being applied")
            release = Release(id=new_id(), server_id=server_id, parent_id=server.active_release_id, bundle=bundle, checksum=digest(bundle), created_by=actor)
            session.add(release)
            session.flush()
            server.desired_release_id = release.id
            server.revision += 1
            audit(session, actor, "release.request", release.id, checksum=release.checksum)
            return release_json(release)

    @app.post("/api/releases", status_code=202)
    def publish(request: PublishRequest, server_id: str | None = Query(default=None), role=Depends(require("publisher"))):
        with sessions() as session:
            server_id = selected(server_id); server = get(session, Server, server_id)
            revision(server.revision, str(request.revision))
            tools, connections = snapshot(session, server_id)
            problems = publish_checks(session, tools, server_id)
            if problems:
                raise HTTPException(422, "; ".join(problems))
            try:
                bundle = compile_bundle(tools, connections, policy_origins(session, server_id))
            except ValueError as exc:
                raise HTTPException(422, str(exc))
        return enqueue(bundle, request.revision, role, server_id)

    @app.post("/api/releases/rollback", status_code=202)
    def rollback(request: RollbackRequest, server_id: str | None = Query(default=None), role=Depends(require("publisher"))):
        with sessions() as session:
            server_id = selected(server_id)
            release = get(session, Release, request.release_id)
            if release.server_id != server_id: raise HTTPException(404, "Record not found")
            if release.status not in {"active", "superseded"}:
                raise HTTPException(422, "Only a previously verified release can be restored")
            if digest(release.bundle) != release.checksum:
                raise HTTPException(422, "Stored release checksum mismatch")
            discovered = {e["connection_id"]: e["tools"] for e in release.bundle.get("federated", [])}
            connections = {cid: {**spec, "_discovered": discovered[cid]} if cid in discovered else spec for cid, spec in release.bundle["connections"].items()}
            bundle = compile_bundle(release.bundle["tools"], connections, policy_origins(session, server_id))
        return enqueue(bundle, request.revision, role, server_id)

    @app.post("/api/deployments")
    def deploy(request: DeploymentAction, server_id: str | None = Query(default=None), role=Depends(require("publisher"))):
        from .deployment import deploy_server
        server_id = selected(server_id)
        with sessions.begin() as session:
            server = server_lock(session, server_id); revision(server.revision, str(request.revision))
            deployment = session.scalar(select(Deployment).where(Deployment.server_id == server_id).with_for_update())
            if not server.active_release_id: raise HTTPException(422, "Publish and activate a release before deployment")
            release = get(session, Release, server.active_release_id)
            deployment.desired_release_id = release.id; deployment.status = "provisioning"; deployment.message = None; deployment.revision += 1
            audit(session, role, "deployment.request", deployment.id, release_id=release.id)
        try:
            result = deploy_server(server_id, release.id, server.name, settings)
        except Exception as exc:
            result = {"status": "failed", "message": safe_error(exc)}
        with sessions.begin() as session:
            deployment = session.scalar(select(Deployment).where(Deployment.server_id == server_id).with_for_update())
            deployment.status = result["status"]; deployment.application_name = result.get("application_name")
            deployment.application_id = result.get("application_id"); deployment.endpoint = result.get("endpoint")
            deployment.provider = result.get("provider", settings.deployment_provider); deployment.message = result.get("message")
            if result["status"] == "running": deployment.deployed_release_id = release.id
            deployment.revision += 1; audit(session, role, "deployment." + result["status"], deployment.id, release_id=release.id)
            return deployment_json(deployment)

    @app.post("/api/deployments/{action}")
    def deployment_action(action: str, request: DeploymentAction, server_id: str | None = Query(default=None), role=Depends(require("publisher"))):
        if action not in {"stop", "delete", "refresh"}: raise HTTPException(404, "Unknown deployment action")
        from .deployment import deployment_action as apply_action
        server_id = selected(server_id)
        with sessions.begin() as session:
            server = server_lock(session, server_id); revision(server.revision, str(request.revision))
            deployment = session.scalar(select(Deployment).where(Deployment.server_id == server_id).with_for_update())
            result = apply_action(action, deployment_json(deployment), settings)
            deployment.status = result["status"]; deployment.message = result.get("message"); deployment.metrics = result.get("metrics", deployment.metrics)
            deployment.revision += 1; audit(session, role, "deployment." + action, deployment.id)
            return deployment_json(deployment)

    @app.get("/api/audit")
    def audit_log(server_id: str | None = Query(default=None), role=Depends(identity)):
        with sessions() as session:
            server_id = selected(server_id)
            targets = {server_id} | set(session.scalars(select(Tool.id).where(Tool.server_id == server_id))) | set(session.scalars(select(Connection.id).where(Connection.server_id == server_id))) | set(session.scalars(select(Release.id).where(Release.server_id == server_id)))
            return [{"id": a.id, "actor": a.actor, "action": a.action, "target_id": a.target_id, "details": a.details, "created_at": a.created_at.isoformat()} for a in session.scalars(select(Audit).where(Audit.target_id.in_(targets)).order_by(Audit.created_at.desc()).limit(100))]

    if (settings.ui_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=settings.ui_dir / "assets"), name="assets")
    if (settings.ui_dir / "help").exists():
        # In-app help pages shipped with the UI build (apps/builder-ui/public/help).
        app.mount("/help", StaticFiles(directory=settings.ui_dir / "help", html=True), name="help")

    @app.get("/favicon.svg")
    def favicon():
        if (settings.ui_dir / "favicon.svg").exists():
            return FileResponse(settings.ui_dir / "favicon.svg", media_type="image/svg+xml")
        raise HTTPException(404, "Record not found")

    @app.get("/")
    def index():
        if (settings.ui_dir / "index.html").exists():
            return FileResponse(settings.ui_dir / "index.html")
        return JSONResponse({"message": "Use the frontend development server, or build apps/builder-ui first"})

    return app
