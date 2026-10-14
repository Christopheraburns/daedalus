"""A deliberately small, lossless OpenAPI 3.0.3 compilation profile."""

import hashlib
import json
import re
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, SchemaError

from . import auth, packs
from .contracts import ConnectionSpec, ToolSpec


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate_connection(spec, allowed):
    ConnectionSpec.model_validate(spec)
    auth.validate(spec)
    protocol, mode = spec.get("protocol", "rest"), spec.get("auth_mode", "none")
    if (mode == "s3-sigv4") != (protocol == "s3") and not (protocol == "s3" and mode == "none"):
        raise ValueError("S3 connections use S3 access-key authentication (or none); other protocols cannot use it")
    url = urlsplit(spec["base_url"])
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Use an HTTP(S) base URL without credentials, query, or fragment")
    origin = f"{url.scheme}://{url.netloc}"
    if origin not in allowed:
        raise ValueError("API origin is not approved. Add it to FACTORY_ALLOWED_API_ORIGINS on both applications")
    if url.path not in ("", "/") and spec.get("protocol") != "mcp":
        raise ValueError("Use an origin-only connection URL; put the API prefix in the tool path")


def validate_body(schema, depth=0):
    if depth > 5 or len(canonical(schema)) > 20000:
        raise ValueError("Body schema exceeds size or depth limits")
    if not isinstance(schema, dict):
        raise ValueError("Body schemas must be objects")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError("Invalid body schema: " + exc.message) from exc
    allowed = {"type", "properties", "required", "additionalProperties", "description", "enum", "minimum", "maximum", "minLength", "maxLength"}
    if set(schema) - allowed:
        raise ValueError("Unsupported body schema keywords: " + ", ".join(sorted(set(schema) - allowed)))
    if schema.get("type") not in {"object", "string", "number", "integer", "boolean"}:
        raise ValueError("Body schemas support objects and scalar types only")
    if schema.get("additionalProperties") not in (None, False, True):
        raise ValueError("additionalProperties must be a boolean")
    for prop in schema.get("properties", {}).values():
        validate_body(prop, depth + 1)


def validate_python_tool(spec, connection, allowed):
    info = packs.tool_info(spec["pack"], spec["function"])
    if info["requires_connection"]:
        if connection is None:
            raise ValueError(f"{spec['pack']}.{spec['function']} requires a connection")
        validate_connection(connection, allowed)
        if connection.get("protocol", "rest") != info["protocol"]:
            raise ValueError(f"{spec['pack']}.{spec['function']} needs a {info['protocol']} connection; {connection['name']} is {connection.get('protocol', 'rest')}")
    elif connection is not None:
        validate_connection(connection, allowed)
    if spec["effect"] != info["effect"]:
        raise ValueError(f"{spec['pack']}.{spec['function']} is a {info['effect']} tool; set the matching side effect")
    if not spec["description"].strip():
        raise ValueError("Add a description explaining when the tool should be used")


def validate_tool(spec, connection, allowed):
    ToolSpec.model_validate(spec)
    if spec.get("kind") == "python":
        return validate_python_tool(spec, connection, allowed)
    validate_connection(connection, allowed)
    if connection.get("protocol", "rest") != "rest":
        raise ValueError(f"REST tools need a rest connection; {connection['name']} is {connection['protocol']}")
    if connection.get("auth_mode") in {"proxy-doas", "s3-sigv4"}:
        raise ValueError("Proxy (doAs) and S3 connections serve Python pack tools only; the gateway cannot sign or obtain tickets for REST tools")
    path = spec["path"]
    if not re.fullmatch(r"/(?:[A-Za-z0-9_{}./-])*", path) or path.startswith("//") or any(p in {".", ".."} for p in path.split("/")):
        raise ValueError("Use a relative API path with named {parameters}; URLs, query strings, and traversal are unsupported")
    placeholders = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", path)
    if "{" in re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*\}", "", path) or "}" in re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*\}", "", path):
        raise ValueError("Invalid path placeholder")
    parameters = spec.get("parameters", [])
    keys = [(p["location"], p["name"]) for p in parameters]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate parameter binding")
    path_params = [p for p in parameters if p["location"] == "path"]
    if set(placeholders) != {p["name"] for p in path_params} or any(not p["required"] or p["type"] == "boolean" for p in path_params):
        raise ValueError("Every path placeholder needs a required string or numeric path parameter")
    if not spec["description"].strip():
        raise ValueError("Add a description explaining when the tool should be used")
    if spec["method"] == "POST" and spec["effect"] != "write":
        raise ValueError("POST tools must be classified as writes in this profile")
    if spec.get("body_schema") is not None:
        if spec["method"] != "POST" or spec["body_schema"].get("type") != "object":
            raise ValueError("JSON request bodies must be objects on POST tools")
        validate_body(spec["body_schema"])


def executor_schema(python_tools):
    """The executor as an OpenAPI target: one POST operation per Python tool, so the
    gateway derives tool schemas exactly as it does for HTTP tools."""
    paths = {}
    for tool in python_tools:
        operation = {"operationId": tool["name"], "description": tool["description"], "responses": {"200": {"description": "JSON result"}}}
        if tool["input_schema"]["properties"]:
            operation["requestBody"] = {"required": True, "content": {"application/json": {"schema": tool["input_schema"]}}}
        paths[f"/tools/{tool['name']}"] = {"post": operation}
    return {"openapi": "3.0.3", "info": {"title": "Daedalus executor", "version": "1"}, "servers": [{"url": "/"}], "paths": paths}


def fingerprint(spec, connection):
    # enabled is release membership; toggling it does not change execution semantics.
    record = {"tool": {k: v for k, v in spec.items() if k != "enabled"}, "connection": connection}
    if spec.get("kind") == "python":
        # Editing a project pack invalidates test evidence for the tools it serves.
        record["pack_source"] = packs.source_digest(spec["pack"])
    return digest(record)


def compile_bundle(tools, connections, allowed):
    targets, names, python_tools = [], set(), []
    enabled = sorted((t for t in tools if t["spec"]["enabled"]), key=lambda t: t["spec"]["name"])
    for tool in (t for t in enabled if t["spec"].get("kind") == "python"):
        spec = tool["spec"]
        connection = connections[spec["connection_id"]] if spec.get("connection_id") else None
        validate_tool(spec, connection, allowed)
        if spec["name"] in names:
            raise ValueError("Tool names must be unique across the server")
        names.add(spec["name"])
        python_tools.append({"name": spec["name"], "description": spec["description"], "pack": spec["pack"], "function": spec["function"],
            "connection_id": spec.get("connection_id"), "config": spec.get("config", {}), "effect": spec["effect"],
            "input_schema": packs.input_schema(packs.tool_info(spec["pack"], spec["function"])["parameters"])})
    http_tools = [t for t in enabled if t["spec"].get("kind", "http") == "http"]
    for connection_id in sorted({t["spec"]["connection_id"] for t in http_tools}):
        connection = connections[connection_id]
        paths = {}
        for tool in (t for t in http_tools if t["spec"]["connection_id"] == connection_id):
            spec = tool["spec"]
            validate_tool(spec, connection, allowed)
            if spec["name"] in names:
                raise ValueError("Tool names must be unique across the server")
            names.add(spec["name"])
            operation = {"operationId": spec["name"], "description": spec["description"], "parameters": [
                {"name": p["name"], "in": p["location"], "required": p["required"], "description": p["description"], "schema": {"type": p["type"]}}
                for p in spec["parameters"]
            ], "responses": {"200": {"description": "JSON response"}}}
            if spec.get("body_schema") is not None:
                operation["requestBody"] = {"required": True, "content": {"application/json": {"schema": spec["body_schema"]}}}
            methods = paths.setdefault(spec["path"], {})
            if spec["method"].lower() in methods:
                raise ValueError("Each API method/path can appear only once per connection")
            methods[spec["method"].lower()] = operation
        schema = {"openapi": "3.0.3", "info": {"title": connection["name"], "version": "1"}, "servers": [{"url": "/"}], "paths": paths}
        targets.append({"connection_id": connection_id, "host": connection["base_url"].rstrip("/"), "schema": schema})
    # Federated MCP connections contribute their discovered tool names; the gateway serves them as extra targets.
    federated = [{"connection_id": cid, "tools": list(connection.get("_discovered", []))} for cid, connection in sorted(connections.items()) if connection.get("protocol") == "mcp" and connection.get("federate")]
    for entry in federated:
        validate_connection({k: v for k, v in connections[entry["connection_id"]].items() if not k.startswith("_")}, allowed)
        for name in entry["tools"]:
            if name in names:
                raise ValueError(f"Tool names must be unique across the server; {name} is also served by the federated MCP server")
            names.add(name)
    used = sorted({t["spec"]["connection_id"] for t in enabled if t["spec"].get("connection_id")} | {e["connection_id"] for e in federated})
    # Project pack code is snapshotted so a published server never changes when the file is edited later.
    pack_sources = {name: packs.project_path(name).read_text() for name in sorted({t["pack"] for t in python_tools}) if name not in packs.builtin_names()}
    stored = {k: {kk: vv for kk, vv in connections[k].items() if not kk.startswith("_")} for k in used}
    return {"schema_version": "factory/v1", "tools": enabled, "connections": stored, "targets": targets, "python_tools": python_tools, "pack_sources": pack_sources, "federated": federated}
