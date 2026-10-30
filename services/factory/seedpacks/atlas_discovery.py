"""Find data in Apache Atlas: search the catalogue by name, type, classification, glossary term, attribute or free text,
follow relationships (a table's columns, a term's assigned entities), run saved searches and get name suggestions.
Read-only. Atlas filters what each identity may see, so results through a forwarded caller token are the caller's view."""
import json
import re

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix     path of the v2 API on the connection, default "/api/atlas/v2";
#              through Knox for example "/gateway/cdp-proxy-api/atlas/api/atlas/v2"
#   page_size  default 100, the most entities one search returns
#   include_deleted  default false; true includes entities Atlas marks DELETED unless a tool says otherwise
# Authentication is the connection's: basic (a service account: results are what that account may see),
# forward-token (the caller's own JWT through Knox: results are the caller's view) or static.
DEFAULTS = {"prefix": "/api/atlas/v2", "page_size": 100, "include_deleted": False}
FEATURES = {"quick": "quick search", "relations": "relationship search", "relationship": "related-entity search", "suggestions": "suggestions"}
OPERATORS = {"=": "eq", "==": "eq", "!=": "neq", "<": "lt", ">": "gt", "<=": "lte", ">=": "gte", "like": "like", "contains": "contains", "startswith": "startsWith", "endswith": "endsWith",
    "isnull": "isNull", "notnull": "notNull"}
FILTER = re.compile(r"^\s*([\w.]+)\s*(==|=|!=|<=|>=|<|>|\b(?:like|contains|startsWith|startswith|endsWith|endswith|isNull|isnull|notNull|notnull)\b)\s*(.*?)\s*$", re.I)
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
KNOWN = {"qualifiedName", "name", "owner", "description", "createTime"}


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_name(value, what):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
    return value


def call(ctx, method, path, params=None, body=None, feature=None):
    """One request to the v2 API. Atlas JSON errors are relayed; an HTML 404 on a newer endpoint means this Atlas predates it."""
    query = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    url = setting(ctx, "prefix").rstrip("/") + "/" + path.lstrip("/")
    with ctx.client(timeout=60.0) as client:
        response = client.request(method, url, params=query, json=body)
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
        feature = feature or FEATURES.get(path.lstrip("/").split("/")[1] if "/" in path.strip("/") else "")
        if feature:
            raise ValueError(f"This Atlas does not offer {feature} ({path}); it needs Atlas 2.1 or later")
        raise ValueError(f"Atlas has no endpoint at {url}; check the prefix in the tool configuration")
    raise ValueError(f"Atlas error {response.status_code}: {detail or response.text[:200]}")


def page(ctx, limit, offset):
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    return max(1, min(limit, int(setting(ctx, "page_size")))), offset


def deleted_param(ctx, include_deleted):
    return "false" if (include_deleted or setting(ctx, "include_deleted")) else "true"


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def entity(header):
    attributes = header.get("attributes") or {}
    return dropped({"guid": header.get("guid"), "type": header.get("typeName"), "name": attributes.get("name") or header.get("displayText"), "qualified_name": attributes.get("qualifiedName"),
        "owner": attributes.get("owner"), "description": attributes.get("description"), "status": (header.get("status") or "").lower() or None,
        "classifications": header.get("classificationNames") or [c.get("typeName") for c in header.get("classifications", [])], "terms": header.get("meaningNames") or [m.get("displayText") for m in header.get("meanings", [])],
        "labels": header.get("labels"), "attributes": {k: v for k, v in attributes.items() if k not in KNOWN}})


def results(found, limit, offset, **extra):
    """An AtlasSearchResult as entities, or as a table when a DSL select clause asked for columns."""
    found = found or {}
    entities = [entity(e) for e in found.get("entities") or []]
    approximate = found.get("approximateCount")
    result = {"entities": entities, "count": len(entities), "offset": offset, "truncated": len(entities) >= limit if approximate in (None, -1) else offset + len(entities) < approximate}
    if approximate not in (None, -1):
        result["approximate_total"] = approximate
    table = found.get("attributes")
    if table and table.get("name"):
        result["columns"] = table.get("name", [])
        result["rows"] = table.get("values", [])
        result["count"] = len(result["rows"])
        result["truncated"] = len(result["rows"]) >= limit
    if found.get("queryText"):
        result["query"] = found["queryText"]
    return {**result, **extra}


def parse_filters(text):
    """Filters as `attribute operator value` pairs separated by commas, or the JSON that SearchParameters.entityFilters takes."""
    text = (text or "").strip()
    if not text:
        return None
    if text.startswith("{"):
        try:
            return json.loads(text)
        except ValueError as exc:
            raise ValueError("filters is not a valid JSON object") from exc
    criteria = []
    for clause in text.split(","):
        match = FILTER.match(clause)
        if not match or not clause.strip():
            raise ValueError(f"{clause.strip()!r} is not a filter; write attribute operator value, for example owner = alice or name like ord*")
        name, operator, value = match.groups()
        criteria.append({"attributeName": name, "operator": OPERATORS[operator.lower()], "attributeValue": value.strip("'\"")})
    return criteria[0] if len(criteria) == 1 else {"condition": "AND", "criterion": criteria}


def saved_search(item):
    parameters = item.get("searchParameters") or {}
    return dropped({"guid": item.get("guid"), "name": item.get("name"), "owner": item.get("ownerName"), "kind": "dsl" if item.get("searchType") == "ADVANCED" else "basic",
        "query": parameters.get("query"), "type": parameters.get("typeName"), "classification": parameters.get("classification"), "term": parameters.get("termName"),
        "filters": parameters.get("entityFilters")})


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the credentials work and report whether this Atlas offers the newer search endpoints."""
    saved = call(ctx, "GET", "search/saved") or []
    try:
        call(ctx, "GET", "search/suggestions", {"prefixString": "a"})
        newer = "offers quick search, relationship search and suggestions"
    except ValueError as exc:
        if "does not offer" not in str(exc):
            raise
        newer = "predates quick search, relationship search and suggestions (Atlas 2.1)"
    return {"ok": True, "message": f"Atlas answered: {len(saved)} saved search(es) for this identity; {newer}"}


# ---- Searches -------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def search_basic(ctx: ToolContext, query: str = "", type_name: str = "", classification: str = "", include_deleted: bool = False, sort_by: str = "", sort_order: str = "ASCENDING", limit: int = 25, offset: int = 0) -> dict:
    """Find entities by free text (name, qualified name, description), entity type (hive_table, hive_db, hdfs_path, ...) and/or classification (PII, Confidential). The usual first search."""
    if not (query or type_name or classification):
        raise ValueError("Give a query, a type_name or a classification")
    if sort_order not in ("ASCENDING", "DESCENDING"):
        raise ValueError("sort_order must be ASCENDING or DESCENDING")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/basic", {"query": query, "typeName": type_name, "classification": classification, "excludeDeletedEntities": deleted_param(ctx, include_deleted),
        "sortBy": sort_by, "sortOrder": sort_order if sort_by else "", "limit": size, "offset": offset})
    return results(found, size, offset)


@pack_tool(effect="read", requires_connection=True)
def search_with_filters(ctx: ToolContext, type_name: str, filters: str = "", query: str = "", classification: str = "", term: str = "", attributes: str = "", include_deleted: bool = False, limit: int = 25, offset: int = 0) -> dict:
    """Find entities of a type whose attributes match filters such as owner = alice, name like ord*, createTime > 1700000000000 (comma-separated, all must hold), optionally with a glossary term or classification. attributes names extra attributes to return."""
    check_name(type_name, "type_name")
    size, offset = page(ctx, limit, offset)
    body = dropped({"typeName": type_name, "query": query, "classification": classification, "termName": term, "entityFilters": parse_filters(filters),
        "attributes": [a.strip() for a in attributes.split(",") if a.strip()], "excludeDeletedEntities": deleted_param(ctx, include_deleted) == "true", "limit": size, "offset": offset})
    body.setdefault("excludeDeletedEntities", False)
    return results(call(ctx, "POST", "search/basic", body=body), size, offset)


@pack_tool(effect="read", requires_connection=True)
def search_dsl(ctx: ToolContext, query: str, type_name: str = "", classification: str = "", limit: int = 25, offset: int = 0) -> dict:
    """Run an Atlas DSL query, for example: hive_table where owner = 'alice' select name, qualifiedName. With a select clause the answer is a table of columns and rows; otherwise a list of entities."""
    if not query.strip():
        raise ValueError("Give a DSL query, for example hive_table where name like 'ord*'")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/dsl", {"query": query, "typeName": type_name, "classification": classification, "limit": size, "offset": offset})
    return results(found, size, offset)


@pack_tool(effect="read", requires_connection=True)
def search_full_text(ctx: ToolContext, query: str, include_deleted: bool = False, limit: int = 25, offset: int = 0) -> dict:
    """Search every indexed attribute for words, for when the name is unknown but a description or comment is remembered."""
    if not query.strip():
        raise ValueError("Give the words to search for")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/fulltext", {"query": query, "excludeDeletedEntities": deleted_param(ctx, include_deleted), "limit": size, "offset": offset})
    return results(found, size, offset)


@pack_tool(effect="read", requires_connection=True)
def quick_search(ctx: ToolContext, query: str, type_name: str = "", include_deleted: bool = False, limit: int = 25, offset: int = 0) -> dict:
    """Search like search_basic and also get counts of matching entities per type, to see where a term appears before narrowing down. Needs Atlas 2.1 or later."""
    if not query.strip():
        raise ValueError("Give a query")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/quick", {"query": query, "typeName": type_name, "excludeDeletedEntities": deleted_param(ctx, include_deleted), "limit": size, "offset": offset}) or {}
    metrics = found.get("aggregationMetrics") or {}
    return results(found.get("searchResults"), size, offset, by_type=metrics.get("__typeName", {}))


@pack_tool(effect="read", requires_connection=True)
def search_by_attribute(ctx: ToolContext, attribute: str, value_prefix: str, type_name: str = "", limit: int = 25, offset: int = 0) -> dict:
    """Find entities whose attribute starts with a value, for example attribute qualifiedName with value_prefix sales. or attribute owner with alice. Optionally restrict to a type."""
    attribute = check_name(attribute, "attribute")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/attribute", {"attrName": attribute, "attrValuePrefix": value_prefix, "typeName": type_name, "limit": size, "offset": offset})
    return results(found, size, offset)


# ---- Relationships -------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def search_relations(ctx: ToolContext, relationship_type: str = "", limit: int = 25, offset: int = 0) -> dict:
    """List relationships (the edges between entities) of a type such as hive_table_columns, hive_table_db or AtlasGlossarySemanticAssignment, with both ends. Needs Atlas 2.2 or later."""
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/relations", {"relationshipName": relationship_type, "limit": size, "offset": offset}, feature="relationship search") or {}
    relations = [dropped({"guid": r.get("guid"), "type": r.get("typeName"), "status": (r.get("status") or "").lower() or None,
        "from": dropped({"guid": r.get("end1", {}).get("guid"), "type": r.get("end1", {}).get("typeName"), "qualified_name": (r.get("end1", {}).get("uniqueAttributes") or {}).get("qualifiedName")}),
        "to": dropped({"guid": r.get("end2", {}).get("guid"), "type": r.get("end2", {}).get("typeName"), "qualified_name": (r.get("end2", {}).get("uniqueAttributes") or {}).get("qualifiedName")})})
        for r in found.get("relations") or []]
    approximate = found.get("approximateCount")
    return dropped({"relations": relations, "count": len(relations), "offset": offset, "approximate_total": approximate if approximate not in (None, -1) else None,
        "truncated": offset + len(relations) < approximate if approximate not in (None, -1) else len(relations) >= size})


@pack_tool(effect="read", requires_connection=True)
def get_related_entities(ctx: ToolContext, guid: str, relation: str, sort_by: str = "", sort_order: str = "ASCENDING", limit: int = 25, offset: int = 0) -> dict:
    """List the entities related to one entity through a relationship attribute: for a hive_table, relation columns or db; for a hive_db, tables; for a glossary term, assignedEntities; for any entity, meanings (its terms)."""
    check_name(guid, "guid")
    check_name(relation, "relation")
    if sort_order not in ("ASCENDING", "DESCENDING"):
        raise ValueError("sort_order must be ASCENDING or DESCENDING")
    size, offset = page(ctx, limit, offset)
    found = call(ctx, "GET", "search/relationship", {"guid": guid, "relation": relation, "sortBy": sort_by, "sortOrder": sort_order if sort_by else "", "limit": size, "offset": offset}, feature="related-entity search")
    return results(found, size, offset, guid=guid, relation=relation)


# ---- Saved searches and suggestions ---------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_saved_searches(ctx: ToolContext, kind: str = "", user: str = "") -> dict:
    """List the saved searches of the connection's identity (or of another user, when permitted): kind basic or dsl."""
    if kind and kind not in ("basic", "dsl"):
        raise ValueError("kind must be basic or dsl")
    saved = call(ctx, "GET", "search/saved", {"searchType": {"basic": "BASIC", "dsl": "ADVANCED"}.get(kind, ""), "user": user}) or []
    return {"saved_searches": [saved_search(s) for s in saved], "total": len(saved)}


@pack_tool(effect="read", requires_connection=True)
def get_saved_search(ctx: ToolContext, name: str, user: str = "") -> dict:
    """Show one saved search by name: its query or filters, without running it."""
    return saved_search(call(ctx, "GET", f"search/saved/{check_name(name, 'name')}", {"user": user}))


@pack_tool(effect="read", requires_connection=True)
def run_saved_search(ctx: ToolContext, name: str, user: str = "") -> dict:
    """Run a saved search by name and return its entities."""
    found = call(ctx, "GET", f"search/saved/execute/{check_name(name, 'name')}", {"user": user})
    return results(found, int(setting(ctx, "page_size")), 0, saved_search=name)


@pack_tool(effect="read", requires_connection=True)
def run_saved_search_by_guid(ctx: ToolContext, guid: str) -> dict:
    """Run a saved search by its guid and return its entities."""
    found = call(ctx, "GET", f"search/saved/execute/guid/{check_name(guid, 'guid')}")
    return results(found, int(setting(ctx, "page_size")), 0, saved_search=guid)


@pack_tool(effect="read", requires_connection=True)
def suggest(ctx: ToolContext, prefix: str, field: str = "") -> dict:
    """Complete a partial name: the values of a field (default name; or qualifiedName) that start with the prefix. Use it before searching when a user remembers only the start of a name. Needs Atlas 2.1 or later."""
    if not prefix.strip():
        raise ValueError("Give the start of the name")
    found = call(ctx, "GET", "search/suggestions", {"prefixString": prefix, "fieldName": field}, feature="suggestions") or {}
    return {"prefix": prefix, "field": found.get("fieldName") or field or "name", "suggestions": found.get("suggestions") or []}
