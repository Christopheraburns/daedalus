"""Inspect data assets in Apache Atlas: an entity's full definition, its classifications and glossary terms, its
relationships, its change history, and its lineage upstream and downstream. Read-only. Atlas filters what each
identity may see, so results through a forwarded caller token are the caller's view. Pairs with atlas_discovery,
which finds entities; this pack explains them."""
import re
from datetime import datetime, timezone

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix  path of the v2 API on the connection, default "/api/atlas/v2";
#           through Knox for example "/gateway/cdp-proxy-api/atlas/api/atlas/v2"
#   max_lineage_depth  default 10; the furthest an agent may ask lineage to walk
# Authentication is the connection's: basic (a service account), forward-token (the caller's own JWT through Knox) or static.
DEFAULTS = {"prefix": "/api/atlas/v2", "max_lineage_depth": 10}
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
DIRECTIONS = {"input": "INPUT", "upstream": "INPUT", "output": "OUTPUT", "downstream": "OUTPUT", "both": "BOTH"}
KNOWN = {"qualifiedName", "name", "owner", "description", "createTime"}


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_name(value, what):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
    return value


def call(ctx, path, params=None, feature=None):
    """One GET against the v2 API; Atlas JSON errors are relayed, an HTML 404 means the endpoint or the prefix is wrong."""
    query = [(k, v) for k, v in (params or []) if v not in (None, "")] if isinstance(params, list) else {k: v for k, v in (params or {}).items() if v not in (None, "")}
    url = setting(ctx, "prefix").rstrip("/") + "/" + path.lstrip("/")
    with ctx.client(timeout=60.0) as client:
        response = client.get(url, params=query)
    if response.status_code < 400:
        try:
            return response.json() if response.content else None
        except ValueError as exc:
            raise ValueError("Atlas returned a response that is not JSON; check the prefix in the tool configuration") from exc
    detail = None
    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            detail = response.json().get("errorMessage")
        except ValueError:
            detail = None
    if response.status_code == 401:
        raise ValueError("Atlas rejected the connection's credentials (HTTP 401)")
    if response.status_code == 403:
        raise ValueError(f"Atlas refused the request: {detail or 'the identity may not read this'}")
    if response.status_code in (404, 405) and detail is None:
        if feature:
            raise ValueError(f"This Atlas does not offer {feature} ({path}); it needs Atlas 2.0 or later")
        raise ValueError(f"Atlas has no endpoint at {url}; check the prefix in the tool configuration")
    raise ValueError(f"Atlas error {response.status_code}: {detail or response.text[:200]}")


def when(millis):
    return datetime.fromtimestamp(millis / 1000, timezone.utc).isoformat(timespec="seconds") if isinstance(millis, (int, float)) and millis > 0 else None


def millis(text):
    text = (text or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{text!r} is not an ISO 8601 timestamp such as 2026-01-31T09:00:00Z") from exc
    return int((parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).timestamp() * 1000)


def split(text, what):
    items = [i.strip() for i in (text or "").replace("\n", ",").split(",") if i.strip()]
    if not items:
        raise ValueError(f"Give at least one {what}")
    return items


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def header(item):
    attributes = item.get("attributes") or {}
    return dropped({"guid": item.get("guid"), "type": item.get("typeName"), "name": attributes.get("name") or item.get("displayText"), "qualified_name": attributes.get("qualifiedName"),
        "owner": attributes.get("owner"), "description": attributes.get("description"), "status": (item.get("status") or "").lower() or None,
        "classifications": item.get("classificationNames") or [c.get("typeName") for c in item.get("classifications", [])], "terms": item.get("meaningNames") or [m.get("displayText") for m in item.get("meanings", [])],
        "labels": item.get("labels"), "attributes": {k: v for k, v in attributes.items() if k not in KNOWN}})


def classification(item, guid=None):
    return dropped({"name": item.get("typeName"), "attributes": item.get("attributes"), "propagated_from": item.get("entityGuid") if guid and item.get("entityGuid") not in (None, guid) else None,
        "propagates": item.get("propagate"), "validity_periods": item.get("validityPeriods")})


def related(value):
    items = value if isinstance(value, list) else [value]
    return [dropped({"guid": i.get("guid"), "type": i.get("typeName"), "name": i.get("displayText"), "relationship_guid": i.get("relationshipGuid"), "status": (i.get("entityStatus") or "").lower() or None})
        for i in items if isinstance(i, dict)]


def entity(full):
    item = full.get("entity") if "entity" in full else full
    attributes = item.get("attributes") or {}
    return dropped({"guid": item.get("guid"), "type": item.get("typeName"), "name": attributes.get("name"), "qualified_name": attributes.get("qualifiedName"), "owner": attributes.get("owner"),
        "description": attributes.get("description"), "status": (item.get("status") or "").lower() or None, "created_by": item.get("createdBy"), "updated_by": item.get("updatedBy"),
        "created": when(item.get("createTime")), "updated": when(item.get("updateTime")), "version": item.get("version"),
        "classifications": [classification(c, item.get("guid")) for c in item.get("classifications", [])], "terms": [m.get("displayText") for m in item.get("meanings", [])], "labels": item.get("labels"),
        "attributes": {k: v for k, v in attributes.items() if k not in KNOWN and v not in (None, [], {})},
        "relationships": {k: related(v) for k, v in (item.get("relationshipAttributes") or {}).items() if v}})


def entities(result):
    result = result or {}
    return {"entities": [entity(e) for e in result.get("entities", [])], "count": len(result.get("entities", []))}


def lineage(info, requested_direction):
    info = info or {}
    nodes = {g: header(h) for g, h in (info.get("guidEntityMap") or {}).items()}
    edges = [{"from": r.get("fromEntityId"), "to": r.get("toEntityId")} for r in info.get("relations", [])]
    base = info.get("baseEntityGuid")
    processes = [g for g, n in nodes.items() if "process" in (n.get("type") or "").lower()]
    return dropped({"entity": nodes.get(base, {"guid": base}), "direction": requested_direction, "depth": info.get("lineageDepth"),
        "datasets": [n for g, n in nodes.items() if g not in processes and g != base], "processes": [nodes[g] for g in processes], "edges": edges,
        "note": "edges run from inputs to processes and from processes to outputs" if edges else "no lineage recorded for this entity"})


def unique(type_name, qualified_name, attribute):
    check_name(type_name, "type_name")
    check_name(attribute, "attribute")
    if not (qualified_name or "").strip():
        raise ValueError("Give the qualified_name, for example sales.orders@cm")
    return f"attr:{attribute}", qualified_name.strip()


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the credentials work by asking Atlas for the headers of recently classified entities."""
    headers = call(ctx, "entity/bulk/headers", {"tagUpdateStartTime": 0}, feature="entity headers") or {}
    return {"ok": True, "message": f"Atlas answered: {len(headers.get('guidHeaderMap') or {})} classified entit(ies) visible to this identity"}


# ---- Entities -------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_entity(ctx: ToolContext, guid: str) -> dict:
    """Show an entity in full by guid: every attribute, its classifications (with propagated ones marked), glossary terms, labels, change metadata and its relationships (a table's db and columns, a column's table, a process's inputs and outputs)."""
    return entity(call(ctx, f"entity/guid/{check_name(guid, 'guid')}"))


@pack_tool(effect="read", requires_connection=True)
def get_entity_header(ctx: ToolContext, guid: str) -> dict:
    """Show an entity's header by guid: type, name, qualified name, owner, status, classifications and terms, without the full attribute set."""
    return header(call(ctx, f"entity/guid/{check_name(guid, 'guid')}/header"))


@pack_tool(effect="read", requires_connection=True)
def get_entities(ctx: ToolContext, guids: str) -> dict:
    """Show several entities in full at once; guids is a comma-separated list."""
    wanted = [check_name(g, "guid") for g in split(guids, "guid")]
    return entities(call(ctx, "entity/bulk", [("guid", g) for g in wanted]))


@pack_tool(effect="read", requires_connection=True)
def get_entity_by_qualified_name(ctx: ToolContext, type_name: str, qualified_name: str, attribute: str = "qualifiedName") -> dict:
    """Show an entity in full by its type and qualified name, for example hive_table and sales.orders@cm, when the guid is unknown. attribute names another unique attribute if the type has one."""
    key, value = unique(type_name, qualified_name, attribute)
    return entity(call(ctx, f"entity/uniqueAttribute/type/{type_name.strip()}", {key: value}))


@pack_tool(effect="read", requires_connection=True)
def get_entity_header_by_qualified_name(ctx: ToolContext, type_name: str, qualified_name: str, attribute: str = "qualifiedName") -> dict:
    """Show an entity's header by its type and qualified name."""
    key, value = unique(type_name, qualified_name, attribute)
    return header(call(ctx, f"entity/uniqueAttribute/type/{type_name.strip()}/header", {key: value}))


@pack_tool(effect="read", requires_connection=True)
def get_entities_by_qualified_names(ctx: ToolContext, type_name: str, qualified_names: str, attribute: str = "qualifiedName") -> dict:
    """Show several entities of one type in full by their qualified names (comma-separated)."""
    check_name(type_name, "type_name")
    check_name(attribute, "attribute")
    names = split(qualified_names, "qualified name")
    return entities(call(ctx, f"entity/bulk/uniqueAttribute/type/{type_name.strip()}", [(f"attr_{i}:{attribute}", n) for i, n in enumerate(names)]))


@pack_tool(effect="read", requires_connection=True)
def list_recently_classified(ctx: ToolContext, since: str = "") -> dict:
    """List the headers of entities whose classifications changed since a time (ISO 8601 or epoch milliseconds; empty means ever), to review what was tagged recently."""
    result = call(ctx, "entity/bulk/headers", {"tagUpdateStartTime": millis(since) if since else 0}, feature="entity headers") or {}
    headers = [header(h) for h in (result.get("guidHeaderMap") or {}).values()]
    return {"since": since or None, "entities": headers, "count": len(headers)}


# ---- Classifications and history ------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_classifications(ctx: ToolContext, guid: str) -> dict:
    """List an entity's classifications with their attributes, saying which are its own and which propagated from a related entity (a column inheriting PII from its table)."""
    check_name(guid, "guid")
    result = call(ctx, f"entity/guid/{guid}/classifications") or {}
    items = [classification(c, guid) for c in result.get("list", [])]
    return {"guid": guid, "classifications": items, "count": len(items)}


@pack_tool(effect="read", requires_connection=True)
def get_classification(ctx: ToolContext, guid: str, name: str) -> dict:
    """Show one classification on an entity, with its attributes and where it propagated from."""
    check_name(guid, "guid")
    return {"guid": guid, **classification(call(ctx, f"entity/guid/{guid}/classification/{check_name(name, 'name')}"), guid)}


@pack_tool(effect="read", requires_connection=True)
def get_audit_events(ctx: ToolContext, guid: str, action: str = "", limit: int = 25, start_key: str = "") -> dict:
    """Show an entity's change history, newest first: who created or updated it, added or removed classifications and terms, and when. Filter by action (ENTITY_CREATE, ENTITY_UPDATE, CLASSIFICATION_ADD, TERM_ADD, ...); pass next_key as start_key for older events."""
    check_name(guid, "guid")
    size = max(1, min(limit, 100))
    events = call(ctx, f"entity/{guid}/audit", {"count": size + 1, "startKey": start_key, "auditAction": action}) or []
    shown = [dropped({"time": when(e.get("timestamp")), "user": e.get("user"), "action": e.get("action"), "details": e.get("details")}) for e in events[:size]]
    return {"guid": guid, "events": shown, "count": len(shown), **({"next_key": events[size - 1].get("eventKey")} if len(events) > size else {})}


# ---- Lineage and relationships -------------------------------------------------------------------------------------

def lineage_params(ctx, direction, depth):
    chosen = DIRECTIONS.get((direction or "both").lower())
    if not chosen:
        raise ValueError("direction must be upstream (input), downstream (output) or both")
    limit = int(setting(ctx, "max_lineage_depth"))
    if not 1 <= depth <= limit:
        raise ValueError(f"depth must be between 1 and {limit}")
    return chosen, {"direction": chosen, "depth": depth}


@pack_tool(effect="read", requires_connection=True)
def get_lineage(ctx: ToolContext, guid: str, direction: str = "both", depth: int = 3) -> dict:
    """Show where an entity's data comes from and where it goes: the datasets and processes upstream (input), downstream (output) or both, to the given depth, as nodes and edges."""
    check_name(guid, "guid")
    _, params = lineage_params(ctx, direction, depth)
    return lineage(call(ctx, f"lineage/{guid}", params), direction.lower() or "both")


@pack_tool(effect="read", requires_connection=True)
def get_lineage_by_qualified_name(ctx: ToolContext, type_name: str, qualified_name: str, direction: str = "both", depth: int = 3, attribute: str = "qualifiedName") -> dict:
    """Show an entity's lineage by its type and qualified name, when the guid is unknown."""
    key, value = unique(type_name, qualified_name, attribute)
    _, params = lineage_params(ctx, direction, depth)
    return lineage(call(ctx, f"lineage/uniqueAttribute/type/{type_name.strip()}", {key: value, **params}), direction.lower() or "both")


@pack_tool(effect="read", requires_connection=True)
def get_relationship(ctx: ToolContext, guid: str, with_entities: bool = False) -> dict:
    """Show one relationship (an edge) by its guid: its type, both ends and status; with_entities adds the headers of the two entities."""
    check_name(guid, "guid")
    result = call(ctx, f"relationship/guid/{guid}", {"extendedInfo": "true" if with_entities else None}) or {}
    rel = result.get("relationship") or {}
    end = lambda e: dropped({"guid": e.get("guid"), "type": e.get("typeName"), "qualified_name": (e.get("uniqueAttributes") or {}).get("qualifiedName")})
    out = dropped({"guid": rel.get("guid"), "type": rel.get("typeName"), "status": (rel.get("status") or "").lower() or None, "from": end(rel.get("end1") or {}), "to": end(rel.get("end2") or {}),
        "propagate_tags": rel.get("propagateTags"), "created_by": rel.get("createdBy"), "created": when(rel.get("createTime")), "updated": when(rel.get("updateTime"))})
    if with_entities:
        out["entities"] = [header(h) for h in (result.get("referredEntities") or {}).values()]
    return out
