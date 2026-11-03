"""Cloudera Data Catalog through the CDP control plane: the Data Shares a Data Lake publishes (what tables and columns
they contain, who outside the company may read them, when they expire), whether tables carry fine-grained Ranger
access policies before they are shared, and the sensitivity tags the Data Compliance profiler suggests for tables and
columns. Read-only. Creating shares, inviting external users and accepting tags are phase 2."""
import re

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   datalake_crn     the Data Lake the tools work on; environment_crn its environment. Set them here so agents need not
#   environment_crn  pass them on every call; the matching arguments still override them.
#   prefix           path of the service on the connection, default "/api/v1/datacatalog"
#   page_size        default 50, the most Data Shares one call returns
# The connection is the CDP control plane for the region with auth_mode cdp-apikey. The API key is a service
# identity: CDP applies that user's roles, not the caller's.
DEFAULTS = {"datalake_crn": "", "environment_crn": "", "prefix": "/api/v1/datacatalog", "page_size": 50}
CRN = re.compile(r"^crn:[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]*:[^:]+:[a-z0-9-]+:[^\s]+$", re.I)
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,512}$")
TABLE = re.compile(r"^[A-Za-z0-9_$-]{1,255}\.[A-Za-z0-9_$-]{1,255}$")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def crn(ctx, value, key, hint):
    value = (value or "").strip() or str(setting(ctx, key)).strip()
    if not value:
        raise ValueError(f"Pass {key} or set it in the tool configuration; {hint}")
    if not CRN.match(value):
        raise ValueError(f"{key} must be a CRN like crn:cdp:{key.split('_')[0]}:us-west-1:<tenant>:{key.split('_')[0]}:<id>")
    return value


def scope(ctx, datalake_crn, environment_crn):
    return {"datalakeCrn": crn(ctx, datalake_crn, "datalake_crn", "the CDP console shows it on the Data Lake"), "environmentCrn": crn(ctx, environment_crn, "environment_crn", "the CDP console shows it on the environment")}


def check_name(value, what):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 512 characters without slashes")
    return value


def send(ctx, operation, body):
    body = {k: v for k, v in body.items() if v not in (None, "")}
    url = setting(ctx, "prefix").rstrip("/") + "/" + operation
    with ctx.client(timeout=60.0) as client:
        response = client.post(url, json=body)
    detail = None
    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            detail = response.json()
        except ValueError:
            detail = None
    return response, detail


def call(ctx, operation, body):
    response, detail = send(ctx, operation, body)
    if response.status_code < 400:
        if detail is None and response.content:
            raise ValueError("The control plane returned a response that is not JSON; check the connection's base URL and the prefix in the tool configuration")
        return detail or {}
    code, message = ((detail or {}).get("code"), (detail or {}).get("message")) if isinstance(detail, dict) else (None, None)
    if response.status_code == 401:
        raise ValueError("CDP rejected the API key (HTTP 401): check the FACTORY_SECRET value, that the key is not expired or revoked, and the Server's clock")
    if response.status_code == 403:
        raise ValueError(f"CDP refused the request: {message or 'the API key owner lacks a Data Catalog role on this environment'}")
    if response.status_code in (404, 405) and not message:
        raise ValueError(f"The control plane has no Data Catalog endpoint at {url_of(ctx, operation)}; check the base URL (api.<region>.cdp.cloudera.com) and the prefix in the tool configuration")
    if response.status_code == 429:
        raise ValueError("CDP is rate limiting this API key; try again shortly")
    raise ValueError(f"CDP error {code or response.status_code}: {message or response.text[:200]}")


def url_of(ctx, operation):
    return setting(ctx, "prefix").rstrip("/") + "/" + operation


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def share(item, detailed=False):
    out = dropped({"id": item.get("dataShareId"), "name": item.get("dataShareName"), "shared": bool(item.get("isShared")), "created": item.get("createdAt"), "updated": item.get("updatedAt"), "created_by": item.get("createdBy"),
        "keywords": item.get("keywords"), "tags": item.get("tags"), "expires": item.get("expiryTime"), "summary": item.get("summary"), "terms_of_use": item.get("termsOfUse")})
    if detailed:
        out["assets"] = [dropped({"resource_id": a.get("resourceId"), "guid": a.get("guid"), "database": a.get("databaseName"), "table": a.get("tableName"), "columns": a.get("columns"), "created": a.get("createTime"), "created_by": a.get("createdBy"),
            "updated": a.get("updateTime"), "updated_by": a.get("updatedBy")}) for a in item.get("assets") or []]
        out["external_users"] = [dropped({"id": u.get("userId"), "username": u.get("username"), "company": u.get("companyName"), "client_id": u.get("clientId"), "permissions": u.get("permissions"), "shared_on": u.get("sharedOn"), "valid_till": u.get("validTill")})
            for u in item.get("externalUsers") or []]
    return out


def fine_grained(value):
    """Whether an asset has fine-grained policies, read from whichever shape the control plane uses for the status."""
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        flags = [v for k, v in value.items() if isinstance(v, bool) and any(word in k.lower() for word in ("fgac", "enabled", "policy", "policies", "status"))]
        if flags:
            return any(flags)
        if isinstance(value.get("policies"), list):
            return bool(value["policies"])
    if isinstance(value, str):
        return value.strip().lower() in ("true", "enabled", "yes", "present")
    return None


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the API key is accepted: a Data Share listing with no Data Lake named is refused as invalid by the control plane only after the signature passed."""
    response, detail = send(ctx, "listDataShares", {})
    if response.status_code == 401:
        raise ValueError("CDP rejected the API key (HTTP 401): check the FACTORY_SECRET value and that the key is not expired or revoked")
    if response.status_code in (404, 405) and not (isinstance(detail, dict) and detail.get("message")):
        raise ValueError(f"The control plane has no Data Catalog endpoint at {url_of(ctx, 'listDataShares')}; check the base URL and the prefix")
    if response.status_code >= 500:
        raise ValueError(f"CDP error {response.status_code}: {response.text[:200]}")
    return {"ok": True, "message": "CDP accepted the API key for the Data Catalog service; set datalake_crn and environment_crn in each tool's configuration"}


# ---- Tools ----------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_data_shares(ctx: ToolContext, name: str = "", limit: int = 50, page_token: str = "", datalake_crn: str = "", environment_crn: str = "") -> dict:
    """List the Data Shares in a Data Lake: name, whether it is currently shared, who created it, keywords and expiry. Filter by name. Pass next_page_token to continue."""
    size = max(1, min(limit, int(setting(ctx, "page_size"))))
    result = call(ctx, "listDataShares", {**scope(ctx, datalake_crn, environment_crn), "name": check_name(name, "name") if name.strip() else "", "pageSize": size, "startingToken": page_token.strip()})
    items = [share(s) for s in result.get("dataShares") or []]
    return dropped({"count": len(items), "next_page_token": result.get("nextToken")}) | {"shares": items}


@pack_tool(effect="read", requires_connection=True)
def get_data_share(ctx: ToolContext, data_share_id: str, datalake_crn: str = "", environment_crn: str = "") -> dict:
    """Show one Data Share in full: summary and terms of use, the tables and columns it contains, the external users who may read it and until when, keywords, tags and expiry."""
    result = call(ctx, "getDataShare", {**scope(ctx, datalake_crn, environment_crn), "dataShareId": check_name(data_share_id, "data_share_id")})
    return share(result, detailed=True)


@pack_tool(effect="read", requires_connection=True)
def get_fgac_status(ctx: ToolContext, tables: str, datalake_crn: str = "", environment_crn: str = "") -> dict:
    """Check whether tables carry fine-grained access control (Ranger row filters and column masks) before they go into a Data Share. Pass tables as database.table names separated by commas."""
    names = [t.strip() for t in tables.split(",") if t.strip()]
    if not names:
        raise ValueError("tables must name at least one database.table")
    for name in names:
        if not TABLE.match(name):
            raise ValueError(f"{name} is not a database.table name")
    assets = [{"databaseName": n.split(".")[0], "tableName": n.split(".")[1]} for n in names]
    result = call(ctx, "getFgacStatusByAssets", {**scope(ctx, datalake_crn, environment_crn), "assets": assets})
    statuses = result.get("listOfFgacStatus")
    rows = []
    if isinstance(statuses, dict):
        for key, value in statuses.items():
            database, _, table = str(key).partition(".")
            rows.append(dropped({"database": database, "table": table or None, "fine_grained_access": fine_grained(value), "status": value}))
    elif isinstance(statuses, list):
        for value in statuses:
            if isinstance(value, dict):
                rows.append(dropped({"database": value.get("databaseName") or value.get("database"), "table": value.get("tableName") or value.get("table"), "fine_grained_access": fine_grained(value), "status": value}))
            else:
                rows.append({"status": value})
    return {"assets": rows, "count": len(rows), "protected": sum(1 for r in rows if r.get("fine_grained_access") is True)}


@pack_tool(effect="read", requires_connection=True)
def get_suggested_tags(ctx: ToolContext, table: str = "", column: str = "", profiled_since: str = "", datalake_crn: str = "") -> dict:
    """List the sensitivity tags the Data Compliance profiler suggests (dp_email, dp_name, dp_iban and so on) and the tables or columns they apply to. Narrow to one table or column by its qualified name (database.table@cluster) or to suggestions profiled since an ISO date-time."""
    if profiled_since.strip() and not re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?", profiled_since.strip()):
        raise ValueError("profiled_since must be an ISO date or date-time, like 2026-10-01 or 2026-10-01T00:00:00Z")
    result = call(ctx, "getSuggestedTags", {"datalakeCrn": crn(ctx, datalake_crn, "datalake_crn", "the CDP console shows it on the Data Lake"), "tableFQN": check_name(table, "table") if table.strip() else "", "columnFQN": check_name(column, "column") if column.strip() else "", "profiledSince": profiled_since.strip()})
    items = [dropped({"qualified_name": s.get("qualifiedName"), "tags": s.get("tags")}) for s in result.get("suggestedTags") or []]
    return {"suggestions": items, "count": len(items), "tags": sorted({t for s in items for t in s.get("tags") or []})}
