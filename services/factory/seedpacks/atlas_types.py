"""The type system of Apache Atlas: which entity types exist (hive_table, hdfs_path, ...), the attributes each carries
including the inherited ones, which classifications may be applied and to what, plus enums, structs, relationships and
business metadata. Read-only. An agent reads a type's attributes here before writing a DSL or filtered search in
atlas_discovery, and understands an entity from atlas_entities by its type's definition."""
import re

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix     path of the v2 API on the connection, default "/api/atlas/v2";
#              through Knox for example "/gateway/cdp-proxy-api/atlas/api/atlas/v2"
#   page_size  default 100, the most types one listing returns
# Authentication is the connection's: basic (a service account), forward-token (the caller's own JWT through Knox) or static.
# Type definitions are not filtered by identity in Atlas; everyone who may read types sees the same answers.
DEFAULTS = {"prefix": "/api/atlas/v2", "page_size": 100}
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
CATEGORIES = {"entity": "entityDefs", "classification": "classificationDefs", "enum": "enumDefs", "struct": "structDefs", "relationship": "relationshipDefs", "business_metadata": "businessMetadataDefs"}
MAX_SUPER_TYPE_DEPTH = 12


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_name(value, what="name"):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
    return value


def check_category(value):
    value = (value or "").strip().lower()
    if value and value not in CATEGORIES:
        raise ValueError("category must be one of " + ", ".join(CATEGORIES))
    return value


def call(ctx, path, params=None):
    query = {k: v for k, v in (params or {}).items() if v not in (None, "")}
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
        raise ValueError(f"Atlas has no endpoint at {url}; check the prefix in the tool configuration")
    raise ValueError(f"Atlas error {response.status_code}: {detail or response.text[:200]}")


def page(ctx, limit, offset):
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    return max(1, min(limit, int(setting(ctx, "page_size"))))


def listed(items, size, offset, key):
    items = items[offset:]
    return {key: items[:size], "count": min(len(items), size), "offset": offset, "truncated": len(items) > size}


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def header(item):
    return dropped({"name": item.get("name"), "category": (item.get("category") or "").lower(), "guid": item.get("guid"), "service_type": item.get("serviceType")})


def attribute(item):
    options = item.get("options") or {}
    return dropped({"name": item.get("name"), "type": item.get("typeName"), "optional": item.get("isOptional"), "cardinality": None if item.get("cardinality") in (None, "SINGLE") else item.get("cardinality"),
        "unique": item.get("isUnique") or None, "indexed": item.get("isIndexable") or None, "default": item.get("defaultValue"), "description": item.get("description"),
        "applicable_entity_types": options.get("applicableEntityTypes"), "max_length": options.get("maxStrLength")})


def relationship_attribute(item):
    return dropped({"name": item.get("name"), "type": item.get("typeName"), "relationship": item.get("relationshipTypeName"), "optional": item.get("isOptional"),
        "cardinality": None if item.get("cardinality") in (None, "SINGLE") else item.get("cardinality"), "description": item.get("description")})


def end(item):
    return dropped({"type": item.get("type"), "name": item.get("name"), "cardinality": item.get("cardinality"), "container": item.get("isContainer") or None, "description": item.get("description")})


def definition(item):
    category = (item.get("category") or "").lower()
    out = dropped({"name": item.get("name"), "category": category, "guid": item.get("guid"), "description": item.get("description"), "service_type": item.get("serviceType"), "version": item.get("typeVersion"),
        "super_types": item.get("superTypes"), "sub_types": item.get("subTypes"), "attributes": [attribute(a) for a in item.get("attributeDefs", [])],
        "relationship_attributes": [relationship_attribute(a) for a in item.get("relationshipAttributeDefs", [])]})
    if category == "enum":
        out["values"] = [dropped({"value": e.get("value"), "ordinal": e.get("ordinal"), "description": e.get("description")}) for e in item.get("elementDefs", [])]
        out.update(dropped({"default": item.get("defaultValue")}))
    if category == "classification":
        out.update(dropped({"entity_types": item.get("entityTypes")}))
    if category == "relationship":
        out.update(dropped({"relationship_category": item.get("relationshipCategory"), "propagate_tags": item.get("propagateTags"), "ends": [end(item[k]) for k in ("endDef1", "endDef2") if item.get(k)]}))
    return out


def dsl_hint(entity):
    names = {a["name"] for a in entity.get("attributes", [])}
    where = "qualifiedName" if "qualifiedName" in names else next(iter(sorted(names)), "name")
    select = ", ".join(n for n in ("name", "qualifiedName", "owner") if n in names) or where
    return f"{entity['name']} where {where} like '*...*' select {select}"


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the credentials work by listing the type names."""
    headers = call(ctx, "types/typedefs/headers") or []
    counts = {}
    for item in headers:
        counts[(item.get("category") or "?").lower()] = counts.get((item.get("category") or "?").lower(), 0) + 1
    return {"ok": True, "message": f"Atlas answered: {len(headers)} types (" + ", ".join(f"{n} {c}" for c, n in sorted(counts.items())) + ")"}


# ---- Tools ----------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_type_names(ctx: ToolContext, category: str = "", name_contains: str = "", service_type: str = "", limit: int = 100, offset: int = 0) -> dict:
    """List the type names in Atlas as name, category and service type (hive, hdfs, ...). Filter by category (entity, classification, enum, struct, relationship, business_metadata), by part of the name, or by service type. Start here to learn what a catalogue can hold."""
    size = page(ctx, limit, offset)
    items = [header(h) for h in call(ctx, "types/typedefs/headers", {"type": check_category(category), "serviceType": service_type.strip()}) or []]
    if name_contains:
        items = [h for h in items if name_contains.lower() in (h.get("name") or "").lower()]
    return listed(sorted(items, key=lambda h: (h["category"], h["name"])), size, offset, "types")


@pack_tool(effect="read", requires_connection=True)
def list_type_definitions(ctx: ToolContext, category: str = "", super_type: str = "", service_type: str = "", limit: int = 25, offset: int = 0) -> dict:
    """List type definitions in full: attributes, super types, enum values, relationship ends. Filter by category, by a super type (every entity type under DataSet, say) or by service type. Large without a filter; list_type_names is the cheap first look."""
    size = page(ctx, limit, offset)
    types = call(ctx, "types/typedefs", {"type": check_category(category), "supertype": super_type.strip(), "serviceType": service_type.strip()}) or {}
    items = [definition(d) for key in CATEGORIES.values() for d in types.get(key, [])]
    counts = {c: len(types.get(key, [])) for c, key in CATEGORIES.items() if types.get(key)}
    return {**listed(items, size, offset, "types"), "total": sum(counts.values()), "by_category": counts}


@pack_tool(effect="read", requires_connection=True)
def get_type_definition(ctx: ToolContext, name: str) -> dict:
    """Show one type of any category by name: its attributes, super and sub types, and for enums the values, for relationships the two ends. Use when the category is unknown."""
    return definition(call(ctx, f"types/typedef/name/{check_name(name)}"))


@pack_tool(effect="read", requires_connection=True)
def get_entity_type(ctx: ToolContext, name: str, include_inherited: bool = True) -> dict:
    """Show an entity type (hive_table, hdfs_path, ...) with every attribute an entity of that type carries, including those inherited from its super types (name, owner and qualifiedName come from Asset and Referenceable), each marked with where it comes from. Includes a DSL search hint for atlas_discovery."""
    entity = definition(call(ctx, f"types/entitydef/name/{check_name(name)}"))
    if include_inherited:
        own = {a["name"] for a in entity.get("attributes", [])}
        inherited, seen, pending = [], {entity["name"]}, list(entity.get("super_types") or [])
        depth = 0
        while pending and depth < MAX_SUPER_TYPE_DEPTH:
            depth, current, pending = depth + 1, pending, []
            for super_name in current:
                if super_name in seen:
                    continue
                seen.add(super_name)
                parent = call(ctx, f"types/entitydef/name/{super_name}") or {}
                for a in parent.get("attributeDefs", []):
                    if a.get("name") not in own:
                        own.add(a.get("name"))
                        inherited.append({**attribute(a), "inherited_from": super_name})
                pending.extend(parent.get("superTypes") or [])
        entity["attributes"] = entity.get("attributes", []) + inherited
        entity["all_super_types"] = sorted(seen - {entity["name"]})
    entity["dsl_hint"] = dsl_hint(entity)
    return entity


@pack_tool(effect="read", requires_connection=True)
def get_classification_type(ctx: ToolContext, name: str) -> dict:
    """Show a classification (tag) type such as PII: its attributes, super and sub classifications, and the entity types it may be applied to (all, when none are listed)."""
    return definition(call(ctx, f"types/classificationdef/name/{check_name(name)}"))
