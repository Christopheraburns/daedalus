"""Cloudera Lakehouse Optimizer through the CDP control plane: which environments run it, the Iceberg namespaces and
tables it maintains, the maintenance policies (compaction, snapshot expiry, orphan cleanup), which tables each policy
covers, each table's maintenance status, and the tasks that ran. Read-only. Lets an agent explain why a table is slow or
paused and what maintenance it gets; changing policies and pausing tables are phase 2."""
import base64
import json
import re
from datetime import datetime, timezone

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   datahub_crn  the CRN of the Lakehouse Optimizer Data Hub the tools work on; list_environments shows each environment's.
#                Set it here so agents need not pass it on every call; a datahub_crn argument still overrides it.
#   prefix       path of the service on the connection, default "/api/v1/lakehouseopt"
#   page_size    default 50, the most environments or tasks one call returns
# The connection is the CDP control plane for the region (https://api.us-west-1.cdp.cloudera.com, https://api.eu-1...,
# https://api.usg-1.cdp.clouderagovt.com) with auth_mode cdp-apikey. The API key is a service identity: CDP applies that
# user's roles, not the caller's.
DEFAULTS = {"datahub_crn": "", "prefix": "/api/v1/lakehouseopt", "page_size": 50}
CRN = re.compile(r"^crn:[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]*:[^:]+:[a-z0-9-]+:[^\s]+$", re.I)
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
STATUSES = ("UNAVAILABLE", "SUCCESS", "ERROR", "PAUSED")


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def check_name(value, what):
    value = (value or "").strip()
    if not NAME.match(value):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
    return value


def crn(ctx, value):
    value = (value or "").strip() or str(setting(ctx, "datahub_crn")).strip()
    if not value:
        raise ValueError("Pass datahub_crn or set it in the tool configuration; list_environments shows each environment's Lakehouse Optimizer Data Hub CRN")
    if not CRN.match(value):
        raise ValueError("datahub_crn must be a CRN like crn:cdp:datahub:us-west-1:<tenant>:cluster:<id>")
    return value


def call(ctx, operation, body):
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
    if response.status_code < 400:
        if detail is None and response.content:
            raise ValueError("The control plane returned a response that is not JSON; check the connection's base URL and the prefix in the tool configuration")
        return detail or {}
    code, message = (detail or {}).get("code"), (detail or {}).get("message") if isinstance(detail, dict) else None
    if response.status_code == 401:
        raise ValueError("CDP rejected the API key (HTTP 401): check the FACTORY_SECRET value, that the key is not expired or revoked, and the Server's clock")
    if response.status_code == 403:
        raise ValueError(f"CDP refused the request: {message or 'the API key owner lacks a Lakehouse Optimizer role on this environment'}")
    if response.status_code in (404, 405) and not message:
        raise ValueError(f"The control plane has no Lakehouse Optimizer endpoint at {url}; check the base URL (api.<region>.cdp.cloudera.com) and the prefix in the tool configuration")
    if response.status_code == 429:
        raise ValueError("CDP is rate limiting this API key; try again shortly")
    raise ValueError(f"CDP error {code or response.status_code}: {message or response.text[:200]}")


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def when(millis):
    return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if millis else None


def decoded(value):
    """A base64-encoded JSON document as data (policy arguments, task details), or the text when it is not JSON."""
    if not value:
        return None
    try:
        text = base64.b64decode(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return value
    try:
        return json.loads(text)
    except ValueError:
        return text


def page(ctx, limit):
    return max(1, min(limit, int(setting(ctx, "page_size"))))


def environment(item):
    return dropped({"name": item.get("environmentName"), "crn": item.get("environmentCrn"), "cloud_platform": item.get("cloudPlatform"), "optimizer_enabled": bool(item.get("isCloEnabled")),
        "datahub_name": item.get("datahubName"), "datahub_crn": item.get("datahubCrn"), "datahub_status": item.get("status")})


def table(item):
    return dropped({"namespace": item.get("namespace"), "name": item.get("tableName"), "status": item.get("status"), "policies": item.get("policies"), "last_execution": when(item.get("lastExecutionTime") or item.get("lastExecutionEpoch"))})


def policy(item):
    return dropped({"name": item.get("policyName"), "status": item.get("status"), "default": bool(item.get("isDefault")) if "isDefault" in item else None, "tables": item.get("tableCount"), "tasks": item.get("taskCount"),
        "created": when(item.get("creationTime")), "last_execution": when(item.get("lastExecutionTime"))})


def task(item):
    return dropped({"id": item.get("taskId"), "status": item.get("status"), "policy": item.get("policy"), "catalog": item.get("catalog"), "namespace": item.get("namespace"), "table": item.get("table"), "created": when(item.get("createdAt")), "details": decoded(item.get("details"))})


# ---- Probe ---------------------------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the API key works by listing the environments."""
    result = call(ctx, "listEnvironments", {"pageSize": 100})
    items = result.get("environments") or []
    enabled = sum(1 for e in items if e.get("isCloEnabled"))
    return {"ok": True, "message": f"CDP answered: {result.get('totalEnvironments', len(items))} environments, {enabled} with Lakehouse Optimizer enabled"}


# ---- Environments and catalogue ---------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_environments(ctx: ToolContext, limit: int = 50, page_token: str = "") -> dict:
    """List the CDP environments the API key can see and, for each, whether Lakehouse Optimizer is enabled and the CRN of its Data Hub. Start here: the other tools take that datahub_crn."""
    size = page(ctx, limit)
    result = call(ctx, "listEnvironments", {"pageSize": size, "pageToken": page_token.strip()})
    items = [environment(e) for e in result.get("environments") or []]
    return dropped({"environments": items, "count": len(items), "total": result.get("totalEnvironments"), "next_page_token": result.get("nextPageToken")}) | {"environments": items}


@pack_tool(effect="read", requires_connection=True)
def list_namespaces(ctx: ToolContext, datahub_crn: str = "") -> dict:
    """List the Iceberg namespaces (databases) the Lakehouse Optimizer Data Hub maintains."""
    hub = crn(ctx, datahub_crn)
    names = sorted(call(ctx, "getNamespaces", {"datahubCrn": hub}).get("namespaces") or [])
    return {"datahub_crn": hub, "namespaces": names, "count": len(names)}


@pack_tool(effect="read", requires_connection=True)
def list_table_names(ctx: ToolContext, namespace: str, datahub_crn: str = "") -> dict:
    """List the table names in a namespace, without status: the cheap way to find a table."""
    hub = crn(ctx, datahub_crn)
    names = sorted(call(ctx, "getTableNames", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace")}).get("tables") or [])
    return {"namespace": namespace.strip(), "tables": names, "count": len(names)}


@pack_tool(effect="read", requires_connection=True)
def list_tables(ctx: ToolContext, namespace: str, datahub_crn: str = "") -> dict:
    """List a namespace's tables with their maintenance status (SUCCESS, WARNING, ERROR, PAUSED, USER_PAUSED, AUTO_PAUSED, UNAVAILABLE), the policies applied to each and when maintenance last ran."""
    hub = crn(ctx, datahub_crn)
    items = [table(t) for t in call(ctx, "listTables", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace")}).get("tables") or []]
    return {"namespace": namespace.strip(), "tables": items, "count": len(items)}


# ---- Policies ----------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_policies(ctx: ToolContext, namespace: str = "", datahub_crn: str = "") -> dict:
    """List the maintenance policies, across the catalogue or in one namespace, with status, how many tables and tasks each has, whether Cloudera provides it by default, and when it last ran."""
    hub = crn(ctx, datahub_crn)
    items = [policy(p) for p in call(ctx, "listPolicies", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace") if namespace.strip() else ""}).get("policies") or []]
    return dropped({"namespace": namespace.strip()}) | {"policies": items, "count": len(items)}


@pack_tool(effect="read", requires_connection=True)
def list_policy_names(ctx: ToolContext, namespace: str = "*", datahub_crn: str = "") -> dict:
    """List the names of the policies applied in a namespace, or in every namespace with "*"."""
    hub = crn(ctx, datahub_crn)
    namespace = namespace.strip() or "*"
    names = sorted(call(ctx, "getPolicyNames", {"datahubCrn": hub, "namespace": namespace if namespace == "*" else check_name(namespace, "namespace")}).get("policyNames") or [])
    return {"namespace": namespace, "policies": names, "count": len(names)}


@pack_tool(effect="read", requires_connection=True)
def get_policy(ctx: ToolContext, policy_name: str, datahub_crn: str = "") -> dict:
    """Show one policy in full: its scope (Catalog or Namespace), the actions and schedule it runs (decoded from its arguments), its versions, and every namespace and table it is associated with, each with status and last run."""
    hub = crn(ctx, datahub_crn)
    result = call(ctx, "getPolicy", {"datahubCrn": hub, "policyName": check_name(policy_name, "policy_name")})
    detail = result.get("policyDetail") or {}
    associations = [dropped({"namespace": a.get("namespace"), "status": a.get("status"), "tables": [dropped({"name": t.get("name"), "status": t.get("status"), "tasks": t.get("taskCount"), "policy_version": t.get("version"), "last_execution": when(t.get("lastExecutionTime"))}) for t in a.get("tableAssociations") or []]})
        for a in detail.get("associations") or []]
    return dropped({"name": policy_name.strip(), "scope": detail.get("scope"), "version": detail.get("version"), "versions": result.get("versions"), "arguments": decoded(detail.get("arguments")), "tables": detail.get("tableCount"),
        "created": when(detail.get("creationTime")), "last_execution": when(detail.get("lastExecutionTime")), "associations": associations})


@pack_tool(effect="read", requires_connection=True)
def get_table_policies(ctx: ToolContext, namespace: str, table_name: str, datahub_crn: str = "") -> dict:
    """List the policies applied to one table, each with its status on that table, how many tasks ran and when the last one ran."""
    hub = crn(ctx, datahub_crn)
    result = call(ctx, "getTablePolicies", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace"), "tableName": check_name(table_name, "table_name")})
    items = [dropped({"name": p.get("policyName"), "status": p.get("status"), "tasks": p.get("taskCount"), "last_execution": when(p.get("lastExecutionTime"))}) for p in result.get("policies") or []]
    return {"namespace": namespace.strip(), "table": table_name.strip(), "policies": items, "count": len(items)}


@pack_tool(effect="read", requires_connection=True)
def get_table_status(ctx: ToolContext, namespace: str, table_name: str, policy_name: str, status: str, datahub_crn: str = "") -> dict:
    """Explain a table's current status under a policy: for a PAUSED table, since when and why; otherwise the most recent task, its actions and their outcome. Pass the status shown by list_tables or get_table_policies (UNAVAILABLE, SUCCESS, ERROR or PAUSED)."""
    hub = crn(ctx, datahub_crn)
    status = status.strip().upper().replace("USER_PAUSED", "PAUSED").replace("AUTO_PAUSED", "PAUSED").replace("WARNING", "SUCCESS")
    if status not in STATUSES:
        raise ValueError("status must be one of " + ", ".join(STATUSES))
    result = call(ctx, "getTableStatusDetails", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace"), "tableName": check_name(table_name, "table_name"), "policyName": check_name(policy_name, "policy_name"), "status": status})
    paused, recent = result.get("pausedTable") or {}, result.get("recentTask") or {}
    out = {"namespace": namespace.strip(), "table": table_name.strip(), "policy": policy_name.strip(), "status": status}
    if paused:
        out["paused"] = dropped({"message": paused.get("message"), "since": (paused.get("details") or {}).get("pausedSince"), "reasons": (paused.get("details") or {}).get("reasons")})
    if recent:
        out["recent_task"] = dropped({"policy": recent.get("policyName"), "last_execution": when(recent.get("lastExecutionTime")), "actions": [dropped({"action": a.get("action"), "status": a.get("status")}) for a in recent.get("actions") or []]})
    if not paused and not recent:
        out["note"] = "No task has run for this table under this policy yet"
    return out


# ---- Associations --------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def get_associations(ctx: ToolContext, policy_name: str, datahub_crn: str = "") -> dict:
    """List the tables a policy is associated with, grouped by namespace."""
    hub = crn(ctx, datahub_crn)
    items = [{"namespace": a.get("namespace"), "tables": sorted(a.get("tables") or [])} for a in call(ctx, "getAssociations", {"datahubCrn": hub, "policyName": check_name(policy_name, "policy_name")}).get("associations") or []]
    return {"policy": policy_name.strip(), "associations": items, "table_count": sum(len(a["tables"]) for a in items)}


@pack_tool(effect="read", requires_connection=True)
def get_associated_namespaces(ctx: ToolContext, policy_name: str, datahub_crn: str = "", only_associated: bool = False) -> dict:
    """Show every namespace with a flag saying whether a policy applies to it; only_associated keeps just the ones it does."""
    hub = crn(ctx, datahub_crn)
    items = [{"namespace": a.get("namespace"), "associated": bool(a.get("isAssociated"))} for a in call(ctx, "getAssociatedNamespaces", {"datahubCrn": hub, "policyName": check_name(policy_name, "policy_name")}).get("associatedNamespaces") or []]
    if only_associated:
        items = [a for a in items if a["associated"]]
    return {"policy": policy_name.strip(), "namespaces": items, "count": len(items)}


@pack_tool(effect="read", requires_connection=True)
def get_associated_tables(ctx: ToolContext, policy_name: str, datahub_crn: str = "", only_associated: bool = False) -> dict:
    """Show every table, per namespace, with a flag saying whether a policy applies to it; only_associated keeps just the ones it does. Use it to find tables a policy misses."""
    hub = crn(ctx, datahub_crn)
    groups = []
    for a in call(ctx, "getAssociatedTables", {"datahubCrn": hub, "policyName": check_name(policy_name, "policy_name")}).get("associatedTables") or []:
        tables = [{"name": t.get("tableName"), "associated": bool(t.get("isAssociated"))} for t in a.get("tables") or []]
        if only_associated:
            tables = [t for t in tables if t["associated"]]
        if tables or not only_associated:
            groups.append({"namespace": a.get("namespace"), "tables": tables})
    return {"policy": policy_name.strip(), "namespaces": groups, "table_count": sum(len(g["tables"]) for g in groups)}


@pack_tool(effect="read", requires_connection=True)
def get_association_overview(ctx: ToolContext, datahub_crn: str = "") -> dict:
    """The whole picture of a Data Hub's maintenance: per namespace, each table's policies, status and last run (direct associations), and the catalogue-wide policies applied to every namespace (star associations)."""
    hub = crn(ctx, datahub_crn)
    result = call(ctx, "getAssociationDetails", {"datahubCrn": hub})
    direct = [dropped({"namespace": ns.get("namespace"), "status": ns.get("status"), "tables": [table(t) for t in ns.get("tables") or []]}) for ns in result.get("directAssociation") or result.get("directionAssociation") or []]
    star = [dropped({"catalog": c.get("catalog"), "status": c.get("status"), "namespaces": [dropped({"namespace": n.get("namespace"), "status": n.get("status"), "policies": n.get("policies")}) for n in c.get("namespaces") or []]}) for c in result.get("starAssociation") or []]
    return {"datahub_crn": hub, "direct": direct, "catalog_wide": star}


# ---- Tasks ---------------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_tasks(ctx: ToolContext, namespace: str, limit: int = 50, page_token: str = "", datahub_crn: str = "") -> dict:
    """List the maintenance tasks that ran in a namespace, newest first: policy, table, status (INIT, SUBMITTED, COMPLETED, FAILED) and the decoded task details (files rewritten, snapshots expired, errors). Pass next_page_token to continue."""
    hub = crn(ctx, datahub_crn)
    size = page(ctx, limit)
    result = call(ctx, "listTasks", {"datahubCrn": hub, "namespace": check_name(namespace, "namespace"), "pageSize": size, "pageToken": page_token.strip()})
    items = [task(t) for t in result.get("tasks") or []]
    return dropped({"namespace": namespace.strip(), "count": len(items), "next_page_token": result.get("nextPageToken")}) | {"tasks": items}
