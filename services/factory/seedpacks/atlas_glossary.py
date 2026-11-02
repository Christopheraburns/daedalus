"""Business vocabulary in Apache Atlas: glossaries, their categories and terms, what each term means, how terms relate
(synonyms, see-also, broader and narrower) and which data assets carry a term. Read-only. Lets an agent translate
between business language and the tables and columns that hold the data. Pairs with atlas_discovery and atlas_entities."""
import re

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix     path of the v2 API on the connection, default "/api/atlas/v2";
#              through Knox for example "/gateway/cdp-proxy-api/atlas/api/atlas/v2"
#   page_size  default 100, the most items one listing returns
# Authentication is the connection's: basic (a service account), forward-token (the caller's own JWT through Knox) or static.
# Glossaries are visible to every Atlas user; the entities a term is assigned to are filtered by Atlas for the identity.
DEFAULTS = {"prefix": "/api/atlas/v2", "page_size": 100}
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
RELATIONS = ("seeAlso", "synonyms", "antonyms", "preferredTerms", "preferredToTerms", "replacementTerms", "replacedBy", "translationTerms", "translatedTerms", "isA", "classifies", "validValues", "validValuesFor")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_guid(value, what="guid"):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
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
    size = max(1, min(limit, int(setting(ctx, "page_size"))))
    return size, {"limit": size + 1, "offset": offset}


def listed(items, size, offset, key):
    items = items or []
    return {key: items[:size], "count": min(len(items), size), "offset": offset, "truncated": len(items) > size}


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def term_header(item):
    return dropped({"guid": item.get("termGuid"), "name": item.get("displayText"), "status": (item.get("status") or "").lower() or None})


def category_header(item):
    return dropped({"guid": item.get("categoryGuid"), "name": item.get("displayText"), "parent_guid": item.get("parentCategoryGuid")})


def glossary(item, detailed=False):
    out = dropped({"guid": item.get("guid"), "name": item.get("name"), "qualified_name": item.get("qualifiedName"), "short_description": item.get("shortDescription"), "long_description": item.get("longDescription"),
        "language": item.get("language"), "usage": item.get("usage"), "terms": [term_header(t) for t in item.get("terms", [])], "categories": [category_header(c) for c in item.get("categories", [])]})
    if detailed:
        out["terms"] = [term(t) for t in (item.get("termInfo") or {}).values()]
        out["categories"] = [category(c) for c in (item.get("categoryInfo") or {}).values()]
    return out


def category(item):
    return dropped({"guid": item.get("guid"), "name": item.get("name"), "qualified_name": item.get("qualifiedName"), "glossary_guid": (item.get("anchor") or {}).get("glossaryGuid"),
        "short_description": item.get("shortDescription"), "long_description": item.get("longDescription"), "parent": category_header(item["parentCategory"]) if item.get("parentCategory") else None,
        "children": [category_header(c) for c in item.get("childrenCategories", [])], "terms": [term_header(t) for t in item.get("terms", [])]})


def assigned(item):
    return dropped({"guid": item.get("guid"), "type": item.get("typeName"), "name": item.get("displayText"), "qualified_name": (item.get("uniqueAttributes") or {}).get("qualifiedName"), "status": (item.get("entityStatus") or "").lower() or None})


def term(item):
    return dropped({"guid": item.get("guid"), "name": item.get("name"), "qualified_name": item.get("qualifiedName"), "glossary_guid": (item.get("anchor") or {}).get("glossaryGuid"),
        "short_description": item.get("shortDescription"), "long_description": item.get("longDescription"), "abbreviation": item.get("abbreviation"), "usage": item.get("usage"), "examples": item.get("examples"),
        "categories": [category_header(c) for c in item.get("categories", [])], "assigned_entities": [assigned(e) for e in item.get("assignedEntities", [])],
        "related": {relation: [term_header(t) for t in item.get(relation, [])] for relation in RELATIONS if item.get(relation)},
        "classifications": [c.get("typeName") for c in item.get("classifications", [])]})


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the credentials work by listing the glossaries."""
    glossaries = call(ctx, "glossary") or []
    return {"ok": True, "message": f"Atlas answered: {len(glossaries)} glossar(ies): " + ", ".join(g.get("name", "?") for g in glossaries[:5])}


# ---- Glossaries -----------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_glossaries(ctx: ToolContext, name_contains: str = "", limit: int = 25, offset: int = 0) -> dict:
    """List the glossaries (vocabularies) in Atlas with their term and category names. Filter by part of a glossary name. Start here to find a term's guid."""
    size, params = page(ctx, limit, offset)
    items = [glossary(g) for g in call(ctx, "glossary", params) or []]
    if name_contains:
        items = [g for g in items if name_contains.lower() in (g.get("name") or "").lower()]
    return listed(items, size, offset, "glossaries")


@pack_tool(effect="read", requires_connection=True)
def get_glossary(ctx: ToolContext, guid: str) -> dict:
    """Show one glossary: its description, usage and the names and guids of its terms and categories."""
    return glossary(call(ctx, f"glossary/{check_guid(guid)}"))


@pack_tool(effect="read", requires_connection=True)
def get_glossary_detailed(ctx: ToolContext, guid: str) -> dict:
    """Show one glossary with every term and category in full: definitions, relations and the entities each term is assigned to. Large for big glossaries; prefer the list tools for a first look."""
    return glossary(call(ctx, f"glossary/{check_guid(guid)}/detailed"), detailed=True)


@pack_tool(effect="read", requires_connection=True)
def list_glossary_categories(ctx: ToolContext, glossary_guid: str, limit: int = 25, offset: int = 0) -> dict:
    """List a glossary's categories in full, with parent, children and the terms in each."""
    size, params = page(ctx, limit, offset)
    return listed([category(c) for c in call(ctx, f"glossary/{check_guid(glossary_guid, 'glossary_guid')}/categories", params) or []], size, offset, "categories")


@pack_tool(effect="read", requires_connection=True)
def list_glossary_category_names(ctx: ToolContext, glossary_guid: str, limit: int = 100, offset: int = 0) -> dict:
    """List a glossary's categories as names and guids only, with each one's parent: the cheap way to see how a glossary is organised."""
    size, params = page(ctx, limit, offset)
    return listed([category_header(c) for c in call(ctx, f"glossary/{check_guid(glossary_guid, 'glossary_guid')}/categories/headers", params) or []], size, offset, "categories")


@pack_tool(effect="read", requires_connection=True)
def list_glossary_terms(ctx: ToolContext, glossary_guid: str, limit: int = 25, offset: int = 0) -> dict:
    """List a glossary's terms in full: definitions, categories, related terms and assigned entities."""
    size, params = page(ctx, limit, offset)
    return listed([term(t) for t in call(ctx, f"glossary/{check_guid(glossary_guid, 'glossary_guid')}/terms", params) or []], size, offset, "terms")


@pack_tool(effect="read", requires_connection=True)
def list_glossary_term_names(ctx: ToolContext, glossary_guid: str, limit: int = 100, offset: int = 0) -> dict:
    """List a glossary's terms as names and guids only: the cheap way to find a term before asking for its definition."""
    size, params = page(ctx, limit, offset)
    return listed([term_header(t) for t in call(ctx, f"glossary/{check_guid(glossary_guid, 'glossary_guid')}/terms/headers", params) or []], size, offset, "terms")


# ---- Categories -----------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_category(ctx: ToolContext, guid: str) -> dict:
    """Show one category: its description, its parent and children, and the terms filed under it."""
    return category(call(ctx, f"glossary/category/{check_guid(guid)}"))


@pack_tool(effect="read", requires_connection=True)
def get_related_categories(ctx: ToolContext, guid: str) -> dict:
    """Show a category's parent and child categories, to walk the glossary hierarchy."""
    check_guid(guid)
    related = call(ctx, f"glossary/category/{guid}/related") or {}
    return {"guid": guid, "parent": [category_header(c) for c in related.get("parent", [])], "children": [category_header(c) for c in related.get("children", [])]}


@pack_tool(effect="read", requires_connection=True)
def list_category_terms(ctx: ToolContext, guid: str, limit: int = 100, offset: int = 0) -> dict:
    """List the terms filed under a category, as names and guids."""
    size, params = page(ctx, limit, offset)
    return listed([term_header(t) for t in call(ctx, f"glossary/category/{check_guid(guid)}/terms", params) or []], size, offset, "terms")


# ---- Terms ----------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_term(ctx: ToolContext, guid: str) -> dict:
    """Show one term in full: definition, abbreviation, usage, examples, categories, related terms and the data assets it is assigned to."""
    return term(call(ctx, f"glossary/term/{check_guid(guid)}"))


@pack_tool(effect="read", requires_connection=True)
def get_term_assigned_entities(ctx: ToolContext, guid: str, limit: int = 25, offset: int = 0) -> dict:
    """List the data assets (tables, columns, files) that carry a term, as entity headers. Answers "where is customer data?" once the term is known."""
    size, params = page(ctx, limit, offset)
    return {"term_guid": guid, **listed([assigned(e) for e in call(ctx, f"glossary/terms/{check_guid(guid)}/assignedEntities", params) or []], size, offset, "entities")}


@pack_tool(effect="read", requires_connection=True)
def get_related_terms(ctx: ToolContext, guid: str) -> dict:
    """Show how a term relates to others: synonyms, antonyms, see-also, broader (isA) and narrower (classifies), preferred and replacement terms, translations, valid values."""
    check_guid(guid)
    related = call(ctx, f"glossary/terms/{guid}/related") or {}
    return {"guid": guid, "related": {relation: [term_header(t) for t in items] for relation, items in related.items() if items}}
