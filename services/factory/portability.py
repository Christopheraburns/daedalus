"""Portable server definitions: export one server workspace to a file and import it elsewhere.

An export carries everything needed to rebuild a server in another project or environment:
its approved origins, connections (secret *names* only, never values), tools, canvas layout and
the source of the project packs its tools use. Record IDs are replaced by stable references, so
an import always creates new records. Release history and test evidence are not carried over:
a test only proves something in the environment where it ran, so imported tools start as drafts.
"""
import os
from datetime import datetime, timezone

from sqlalchemy import select

from . import packs
from .compiler import validate_connection
from .contracts import ConnectionSpec, ToolSpec
from .db import ApiOrigin, Connection, Deployment, Layout, Server, Tool, audit, new_id

FORMAT = "daedalus-server/v1"
SECRET_FIELDS = ("secret_ref", "keytab_ref")


def export_server(session, server_id):
    server = session.get(Server, server_id)
    if server is None:
        raise LookupError("Record not found")
    # Ordered by name so the same server always exports to the same file (stable references, readable diffs).
    connections = sorted(session.scalars(select(Connection).where(Connection.server_id == server_id)), key=lambda c: (c.spec["name"], c.spec["base_url"]))
    tools = sorted(session.scalars(select(Tool).where(Tool.server_id == server_id)), key=lambda t: t.spec["name"])
    origins = list(session.scalars(select(ApiOrigin).where(ApiOrigin.server_id == server_id).order_by(ApiOrigin.origin)))
    layout = session.get(Layout, server_id)
    refs = {server.id: "server", **{c.id: f"c{i + 1}" for i, c in enumerate(connections)}, **{t.id: f"t{i + 1}" for i, t in enumerate(tools)}}
    used_packs = sorted({t.spec["pack"] for t in tools if t.spec.get("kind") == "python" and t.spec.get("pack") not in packs.builtin_names()})
    pack_sources = {}
    for name in used_packs:
        path = packs.project_path(name)
        if path.is_file():
            pack_sources[name] = path.read_text()
    secrets = sorted({c.spec[field] for c in connections for field in SECRET_FIELDS if c.spec.get(field)})
    return {
        "format": FORMAT,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": {"server_id": server.id},
        "server": {"name": server.name},
        "origins": [{"origin": o.origin, "description": o.description, "enabled": o.enabled} for o in origins],
        "connections": [{"ref": refs[c.id], "spec": c.spec, "discovered": c.discovered} for c in connections],
        "tools": [{"ref": refs[t.id], "spec": {**t.spec, "connection_id": refs.get(t.connection_id) if t.connection_id else None}} for t in tools],
        "layout": {refs[key]: value for key, value in (layout.positions if layout else {}).items() if key in refs},
        "packs": pack_sources,
        "required_secrets": secrets,
    }


def check_document(document):
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        raise ValueError(f"This is not a Daedalus server export (expected format {FORMAT})")
    for key in ("server", "origins", "connections", "tools", "layout", "packs"):
        if key not in document:
            raise ValueError(f"The export is missing its {key} section")
    refs = [c.get("ref") for c in document["connections"]]
    if len(set(refs)) != len(refs):
        raise ValueError("The export has duplicate connection references")
    names = [t.get("spec", {}).get("name") for t in document["tools"]]
    if len(set(names)) != len(names):
        raise ValueError("The export has duplicate tool names")
    for tool in document["tools"]:
        ref = tool.get("spec", {}).get("connection_id")
        if ref and ref not in refs:
            raise ValueError(f"Tool {tool['spec'].get('name')} refers to a connection that is not in the export")


def pack_conflicts(document):
    """Project packs in the export that already exist here with different code."""
    conflicts = []
    for name, source in document["packs"].items():
        if name in packs.builtin_names():
            raise ValueError(f"The export contains a project pack named {name}, which is a built-in pack here")
        path = packs.project_path(name)
        if path.is_file() and path.read_text() != source:
            conflicts.append(name)
    return conflicts


def import_server(session, document, name, replace_packs, actor, settings, deployment_provider):
    check_document(document)
    conflicts = pack_conflicts(document)
    if conflicts and not replace_packs:
        raise FileExistsError(", ".join(conflicts))
    written = []
    for pack_name, source in document["packs"].items():
        path = packs.project_path(pack_name)
        if not path.is_file() or path.read_text() != source:
            packs.save_project_pack(pack_name, source)  # validated in isolation, like a save from the editor
            written.append(pack_name)
    server = Server(id=new_id(), name=(name or document["server"]["name"])[:80])
    session.add(server)
    session.flush()
    session.add(Deployment(server_id=server.id, provider=deployment_provider))
    approved = set()
    for origin in [*(o for o in settings.allowed_origins if o), *(o["origin"] for o in document["origins"] if o.get("enabled", True))]:
        if origin not in approved:
            description = next((o.get("description", "") for o in document["origins"] if o["origin"] == origin), "Environment bootstrap origin")
            session.add(ApiOrigin(server_id=server.id, origin=origin, description=description[:240]))
            approved.add(origin)
    ids = {"server": server.id}
    for entry in document["connections"]:
        spec = ConnectionSpec.model_validate(entry["spec"]).model_dump()
        validate_connection(spec, sorted(approved))
        connection = Connection(server_id=server.id, spec=spec, discovered=entry.get("discovered"))
        session.add(connection)
        session.flush()
        ids[entry["ref"]] = connection.id
    for entry in document["tools"]:
        spec = dict(entry["spec"])
        spec["connection_id"] = ids[spec["connection_id"]] if spec.get("connection_id") else None
        spec = ToolSpec.model_validate(spec).model_dump()
        if spec["kind"] == "python":
            packs.tool_info(spec["pack"], spec["function"])  # the pack and function exist here
        tool = Tool(server_id=server.id, spec=spec, connection_id=spec["connection_id"])
        session.add(tool)
        session.flush()
        ids[entry["ref"]] = tool.id
    session.add(Layout(server_id=server.id, positions={ids[ref]: value for ref, value in document["layout"].items() if ref in ids}))
    secrets = sorted(set(document.get("required_secrets", [])))
    audit(session, actor, "server.import", server.id, name=server.name, source=document.get("source", {}).get("server_id"),
        tools=len(document["tools"]), connections=len(document["connections"]), packs=written)
    return {"server": {"id": server.id, "name": server.name, "revision": server.revision}, "tools": len(document["tools"]),
        "connections": len(document["connections"]), "packs_written": written, "required_secrets": secrets,
        "missing_secrets": [s for s in secrets if not os.environ.get(s)]}
