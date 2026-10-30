"""Read-only view of Apache Ranger authorization: which services are guarded, what their policies grant to users,
groups and roles, who holds which role, and how security zones divide resources. Lets an agent explain who may
access what. Never changes a policy. Works with Ranger Admin directly or through a proxy such as Knox."""
import json
import re

from factory.packs import ToolContext, pack_probe, pack_tool

PROTOCOL = "rest"

# Tool configuration (inspector → Configuration JSON), all optional:
#   prefix     path of the public API on the connection, default "/service/public/v2/api";
#              through Knox for example "/gateway/cdp-proxy-api/ranger/service/public/v2/api"
#   scope      "all" (default): answers cover every policy the connection's account may read, for an
#              "explain our access policies" server; "caller": policy and role answers are narrowed to the
#              calling user (their own grants, through users, groups and roles). Services, service types
#              and zones describe structure rather than grants and are not narrowed.
#   page_size  default 200, the most entries one search returns
# Authentication is the connection's: basic (a service account; Ranger's Auditor role is the read-only fit),
# forward-token (the caller's own JWT through Knox) or static (a fixed bearer token).
DEFAULTS = {"prefix": "/service/public/v2/api", "scope": "all", "page_size": 200}
SCOPES = ("all", "caller")
NAME = re.compile(r"^[^\x00-\x1f\x7f/]{1,255}$")
FEATURES = {"roles": "roles", "zones": "security zones", "zones-v2": "security zones", "zone-headers": "security zones", "zone-names": "security zones"}
POLICY_TYPES = {0: "access", 1: "masking", 2: "row-filter"}
SENSITIVE = re.compile(r"password|secret|keytab|credential|token", re.I)


def setting(ctx, key):
    return ctx.config.get(key, DEFAULTS[key])


def scoped(ctx):
    scope = setting(ctx, "scope")
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {', '.join(SCOPES)}")
    return scope == "caller"


def check_name(value, what):
    if not NAME.match(value or ""):
        raise ValueError(f"{what} must be 1 to 255 characters without slashes")
    return value


def call(ctx, path, params=None, feature=None):
    """One GET against the public API. Ranger's JSON errors are relayed; an HTML 404 or 405 on a roles or zones
    endpoint means this Ranger predates the feature."""
    query = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    url = setting(ctx, "prefix").rstrip("/") + "/" + path.lstrip("/")
    with ctx.client(timeout=30.0) as client:
        response = client.get(url, params=query)
    if response.status_code == 304:
        return None
    if response.status_code < 400:
        try:
            return response.json() if response.content else None
        except ValueError as exc:
            raise ValueError("Ranger returned a response that is not JSON; check the prefix in the tool configuration") from exc
    detail = None
    try:
        detail = response.json().get("msgDesc") if response.headers.get("content-type", "").startswith("application/json") else None
    except ValueError:
        detail = None
    if response.status_code == 401:
        raise ValueError("Ranger rejected the connection's credentials (HTTP 401)")
    if response.status_code == 403:
        raise ValueError(f"Ranger refused the request: {detail or 'the account may not read this'}")
    if response.status_code in (404, 405) and detail is None:
        feature = feature or FEATURES.get(path.lstrip("/").split("/")[0])
        if feature:
            raise ValueError(f"This Ranger does not offer {feature} ({path}); they need Ranger 2.0 or later")
        raise ValueError(f"Ranger has no endpoint at {url}; check the prefix in the tool configuration")
    raise ValueError(f"Ranger error {response.status_code}: {detail or response.text[:200]}")


def parse_resource(value):
    """name=value pairs separated by commas (database=sales, table=orders) or a JSON object."""
    value = (value or "").strip()
    if not value:
        return {}
    if value.startswith("{"):
        try:
            parsed = json.loads(value)
        except ValueError as exc:
            raise ValueError("resource is not a valid JSON object") from exc
        if not isinstance(parsed, dict) or not all(isinstance(v, str) for v in parsed.values()):
            raise ValueError("resource must be a JSON object of string values")
        return parsed
    result = {}
    for pair in value.split(","):
        name, separator, item = pair.partition("=")
        if not separator or not name.strip():
            raise ValueError(f"{pair.strip()!r} is not a name=value pair; for example database=sales, table=orders or path=/data/shared")
        result[name.strip()] = item.strip()
    return result


def resource_params(resource):
    return {f"resource:{name}": value for name, value in parse_resource(resource).items()}


# ---- Compact shapes -------------------------------------------------------------------------------------------------

def dropped(mapping):
    return {k: v for k, v in mapping.items() if v not in (None, "", [], {})}


def item(entry, kind=None):
    result = {"accesses": [a.get("type") for a in entry.get("accesses", []) if a.get("isAllowed", True)], "users": entry.get("users", []), "groups": entry.get("groups", []),
        "roles": entry.get("roles", []), "conditions": [c.get("type") for c in entry.get("conditions", [])], "delegate_admin": entry.get("delegateAdmin") or None}
    if kind == "mask":
        result["mask"] = (entry.get("dataMaskInfo") or {}).get("dataMaskType")
    if kind == "filter":
        result["filter"] = (entry.get("rowFilterInfo") or {}).get("filterExpr")
    return dropped(result)


def policy_summary(policy):
    return dropped({"id": policy.get("id"), "guid": policy.get("guid"), "name": policy.get("name"), "service": policy.get("service"), "service_type": policy.get("serviceType"),
        "policy_type": POLICY_TYPES.get(policy.get("policyType", 0), str(policy.get("policyType"))), "zone": policy.get("zoneName"), "enabled": policy.get("isEnabled", True),
        "description": policy.get("description"), "priority": policy.get("policyPriority") or None,
        "resources": {name: dropped({"values": r.get("values", []), "excludes": r.get("isExcludes") or None, "recursive": r.get("isRecursive") or None}) for name, r in (policy.get("resources") or {}).items()},
        "allow": [item(i) for i in policy.get("policyItems", [])], "deny": [item(i) for i in policy.get("denyPolicyItems", [])],
        "allow_exceptions": [item(i) for i in policy.get("allowExceptions", [])], "deny_exceptions": [item(i) for i in policy.get("denyExceptions", [])],
        "masks": [item(i, "mask") for i in policy.get("dataMaskPolicyItems", [])], "row_filters": [item(i, "filter") for i in policy.get("rowFilterPolicyItems", [])],
        "deny_all_else": policy.get("isDenyAllElse") or None})


def role_summary(role):
    return dropped({"id": role.get("id"), "name": role.get("name"), "description": role.get("description"), "enabled": role.get("isEnabled", True),
        "users": [u["name"] for u in role.get("users", [])], "user_admins": [u["name"] for u in role.get("users", []) if u.get("isAdmin")],
        "groups": [g["name"] for g in role.get("groups", [])], "group_admins": [g["name"] for g in role.get("groups", []) if g.get("isAdmin")],
        "roles": [r["name"] for r in role.get("roles", [])]})


def service_summary(service):
    configs = {k: v for k, v in (service.get("configs") or {}).items() if not SENSITIVE.search(k)}
    return dropped({"id": service.get("id"), "name": service.get("name"), "display_name": service.get("displayName"), "type": service.get("type"), "enabled": service.get("isEnabled", True),
        "description": service.get("description"), "policy_version": service.get("policyVersion"), "tag_version": service.get("tagVersion"), "configs": configs})


def service_header(header):
    return dropped({"id": header.get("id"), "name": header.get("name"), "display_name": header.get("displayName"), "type": header.get("type"), "enabled": header.get("isEnabled", True),
        "tag_service": header.get("isTagService") or None})


def service_type_summary(definition):
    return dropped({"id": definition.get("id"), "name": definition.get("name"), "display_name": definition.get("displayName"), "label": definition.get("label"), "description": definition.get("description"),
        "resources": [dropped({"name": r.get("name"), "type": r.get("type"), "level": r.get("level"), "parent": r.get("parent"), "recursive_supported": r.get("recursiveSupported") or None,
            "excludes_supported": r.get("excludesSupported") or None}) for r in definition.get("resources", [])],
        "access_types": [a.get("name") for a in definition.get("accessTypes", [])]})


def zone_summary(zone):
    services = zone.get("services") or {}
    return dropped({"id": zone.get("id"), "name": zone.get("name"), "description": zone.get("description"), "enabled": zone.get("isEnabled", True),
        "services": {name: (entry or {}).get("resources", []) for name, entry in services.items()}, "tag_services": zone.get("tagServices", []),
        "admin_users": zone.get("adminUsers", []), "admin_groups": zone.get("adminUserGroups", []), "admin_roles": zone.get("adminRoles", []),
        "audit_users": zone.get("auditUsers", []), "audit_groups": zone.get("auditUserGroups", []), "audit_roles": zone.get("auditRoles", [])})


def zone_header(header):
    return {"id": header.get("id"), "name": header.get("name")}


def tags_summary(service, tags):
    definitions = {str(k): v for k, v in (tags.get("tagDefinitions") or {}).items()}
    tag_by_id = {str(k): v for k, v in (tags.get("tags") or {}).items()}
    resources = {str(r.get("id")): r for r in tags.get("serviceResources", [])}
    tagged = []
    for resource_id, tag_ids in (tags.get("resourceToTagIds") or {}).items():
        resource = resources.get(str(resource_id), {})
        tagged.append({"resource": {name: e.get("values", []) for name, e in (resource.get("resourceElements") or {}).items()},
            "tags": [dropped({"type": tag_by_id.get(str(t), {}).get("type"), "attributes": tag_by_id.get(str(t), {}).get("attributes")}) for t in tag_ids]})
    return {"service": service, "tag_version": tags.get("tagVersion"), "tag_types": sorted({d.get("name") for d in definitions.values() if d.get("name")}), "tagged_resources": tagged}


def paged(ctx, limit, offset):
    size = max(1, min(limit, int(setting(ctx, "page_size"))))
    if offset < 0:
        raise ValueError("offset must be zero or positive")
    return {"startIndex": offset, "pageSize": size + 1}, size


def policy_page(ctx, path, params, limit, offset, caller=None):
    page, size = paged(ctx, limit, offset)
    policies = call(ctx, path, {**params, **page}) or []
    result = {"policies": [policy_summary(p) for p in policies[:size]], "offset": offset, "truncated": len(policies) > size}
    if caller:
        result["scoped_to"] = caller
    return result


def caller_roles(ctx):
    return call(ctx, f"roles/user/{ctx.caller.username}") or []


# ---- Services and service types --------------------------------------------------------------------------------------

@pack_probe
def probe(ctx: ToolContext) -> dict:
    """Confirm the credentials work and report which feature groups this Ranger offers."""
    services = call(ctx, "service-headers") or []
    features = []
    for path, label in (("roles/names", "roles"), ("zone-headers", "security zones")):
        try:
            call(ctx, path)
            features.append(label)
        except ValueError as exc:
            if "does not offer" not in str(exc):
                raise
    offered = ", ".join(features) if features else "neither roles nor security zones (Ranger before 2.0)"
    return {"ok": True, "message": f"Ranger answered: {len(services)} service(s) guarded; offers {offered}"}


@pack_tool(effect="read", requires_connection=True)
def list_service_types(ctx: ToolContext, name: str = "") -> dict:
    """List the kinds of service Ranger can guard (hdfs, hive, hbase, kafka, ozone, s3 and so on) with the resource levels and access types each defines. Filter by exact name."""
    definitions = call(ctx, "servicedef", {"serviceType": name}) or []
    return {"service_types": [service_type_summary(d) for d in definitions], "total": len(definitions)}


@pack_tool(effect="read", requires_connection=True)
def get_service_type(ctx: ToolContext, name: str) -> dict:
    """Describe one service type by name: its resource hierarchy (for Hive database, table, column) and access types (select, update, all). Use it to phrase resource filters correctly."""
    return service_type_summary(call(ctx, f"servicedef/name/{check_name(name, 'name')}"))


@pack_tool(effect="read", requires_connection=True)
def get_service_type_by_id(ctx: ToolContext, id: int) -> dict:
    """Describe one service type by its numeric id."""
    return service_type_summary(call(ctx, f"servicedef/{id}"))


@pack_tool(effect="read", requires_connection=True)
def list_services(ctx: ToolContext, service_type: str = "", name_contains: str = "") -> dict:
    """List the services Ranger guards (for example cm_hdfs, cm_hive), each the home of a set of policies. Filter by type or a part of the name."""
    services = call(ctx, "service", {"serviceType": service_type, "serviceNamePartial": name_contains}) or []
    return {"services": [service_summary(s) for s in services], "total": len(services)}


@pack_tool(effect="read", requires_connection=True)
def list_service_headers(ctx: ToolContext) -> dict:
    """List every guarded service by id, name and type only: the cheapest way to see what Ranger covers."""
    headers = call(ctx, "service-headers") or []
    return {"services": [service_header(h) for h in headers], "total": len(headers)}


@pack_tool(effect="read", requires_connection=True)
def get_service(ctx: ToolContext, name: str) -> dict:
    """Describe one guarded service by name, with its type, versions and non-secret configuration."""
    return service_summary(call(ctx, f"service/name/{check_name(name, 'name')}"))


@pack_tool(effect="read", requires_connection=True)
def get_service_by_id(ctx: ToolContext, id: int) -> dict:
    """Describe one guarded service by its numeric id."""
    return service_summary(call(ctx, f"service/{id}"))


@pack_tool(effect="read", requires_connection=True)
def get_service_tags(ctx: ToolContext, service: str) -> dict:
    """List the classification tags (for example PII) attached to a service's resources, usually synchronised from Atlas, and which resources carry them."""
    tags = call(ctx, f"service/{check_name(service, 'service')}/tags")
    return tags_summary(service, tags or {})


# ---- Policies ------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def search_policies(ctx: ToolContext, service: str = "", service_type: str = "", name_contains: str = "", user: str = "", group: str = "", role: str = "", zone: str = "",
        policy_type: str = "", resource: str = "", limit: int = 50, offset: int = 0) -> dict:
    """Search policies across services. Filter by service, service type, part of the name, a user, group or role they grant to, zone, policy type (access, masking, row-filter) or a resource such as database=sales, table=orders. Each policy lists what it allows and denies to whom."""
    if policy_type and policy_type not in POLICY_TYPES.values():
        raise ValueError("policy_type must be access, masking or row-filter")
    caller = ctx.caller.username if scoped(ctx) else None
    params = {"serviceName": service, "serviceType": service_type, "policyNamePartial": name_contains, "user": caller or user, "group": group, "role": role, "zoneName": zone,
        "policyType": next((str(k) for k, v in POLICY_TYPES.items() if v == policy_type), ""), **resource_params(resource)}
    return policy_page(ctx, "policy", params, limit, offset, caller)


@pack_tool(effect="read", requires_connection=True)
def list_service_policies(ctx: ToolContext, service: str, zone: str = "", name_contains: str = "", limit: int = 50, offset: int = 0) -> dict:
    """List the policies of one guarded service, optionally within a security zone or matching part of a name."""
    caller = ctx.caller.username if scoped(ctx) else None
    params = {"zoneName": zone, "policyNamePartial": name_contains, "user": caller}
    return policy_page(ctx, f"service/{check_name(service, 'service')}/policy", params, limit, offset, caller)


def scoped_policy(ctx, params, what):
    """In caller scope a single policy is fetched through the search with the caller as user filter, so a policy that grants the caller nothing stays invisible."""
    policies = call(ctx, "policy", {**params, "user": ctx.caller.username}) or []
    if not policies:
        raise ValueError(f"{what} is not visible to {ctx.caller.username}: it grants them nothing, or does not exist")
    return {**policy_summary(policies[0]), "scoped_to": ctx.caller.username}


@pack_tool(effect="read", requires_connection=True)
def get_policy(ctx: ToolContext, id: int) -> dict:
    """Show one policy in full by its numeric id: resources, and what is allowed, denied, masked or filtered for which users, groups and roles."""
    if scoped(ctx):
        return scoped_policy(ctx, {"policyId": str(id)}, f"Policy {id}")
    return policy_summary(call(ctx, f"policy/{id}"))


@pack_tool(effect="read", requires_connection=True)
def get_policy_by_name(ctx: ToolContext, service: str, name: str, zone: str = "") -> dict:
    """Show one policy by its service and name (and zone, when the policy sits in a security zone)."""
    check_name(service, "service")
    check_name(name, "name")
    if scoped(ctx):
        return scoped_policy(ctx, {"serviceName": service, "policyName": name, "zoneName": zone}, f"Policy {name} in {service}")
    return policy_summary(call(ctx, f"service/{service}/policy/{name}", {"zoneName": zone}))


@pack_tool(effect="read", requires_connection=True)
def get_policy_by_guid(ctx: ToolContext, guid: str, service: str = "", zone: str = "") -> dict:
    """Show one policy by its globally unique id, the identifier Ranger exports and audit logs carry."""
    check_name(guid, "guid")
    if scoped(ctx):
        return scoped_policy(ctx, {"guid": guid, "serviceName": service, "zoneName": zone}, f"Policy {guid}")
    return policy_summary(call(ctx, f"policy/guid/{guid}", {"serviceName": service, "zoneName": zone}))


@pack_tool(effect="read", requires_connection=True)
def get_policies_for_resource(ctx: ToolContext, service_type: str, resource: str, service: str = "") -> dict:
    """Find the policies that apply to one resource: give the service type (hdfs, hive, ...) and the resource as name=value pairs, for example path=/data/shared or database=finance, table=payroll. Answers "who may access this?"."""
    check_name(service_type, "service_type")
    wanted = resource_params(resource)
    if not wanted:
        raise ValueError("Give the resource as name=value pairs, for example path=/data/shared or database=sales, table=orders")
    if scoped(ctx):
        policies = call(ctx, "policy", {"serviceType": service_type, "serviceName": service, "user": ctx.caller.username, **wanted}) or []
        return {"service_type": service_type, "resource": parse_resource(resource), "policies": [policy_summary(p) for p in policies], "scoped_to": ctx.caller.username}
    policies = call(ctx, f"policies/{service_type}/for-resource", {"serviceName": service, **wanted}) or []
    return {"service_type": service_type, "resource": parse_resource(resource), "policies": [policy_summary(p) for p in policies]}


# ---- Roles ---------------------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_roles(ctx: ToolContext, name_contains: str = "", user: str = "", group: str = "") -> dict:
    """List Ranger roles with their member users and groups. Filter by part of the name, or by a user or group that holds the role."""
    caller = ctx.caller.username if scoped(ctx) else None
    roles = call(ctx, "roles", {"roleNamePartial": name_contains, "userName": caller or user, "groupName": group}) or []
    result = {"roles": [role_summary(r) for r in roles], "total": len(roles)}
    return {**result, "scoped_to": caller} if caller else result


@pack_tool(effect="read", requires_connection=True)
def list_role_names(ctx: ToolContext) -> dict:
    """List the names of all roles, cheaply."""
    if scoped(ctx):
        names = caller_roles(ctx)
        return {"roles": names, "total": len(names), "scoped_to": ctx.caller.username}
    names = call(ctx, "roles/names") or []
    return {"roles": names, "total": len(names)}


def visible_role(ctx, role):
    if scoped(ctx) and role.get("name") not in caller_roles(ctx):
        raise ValueError(f"Role {role.get('name')} is not visible to {ctx.caller.username}: they do not hold it")
    return role_summary(role)


@pack_tool(effect="read", requires_connection=True)
def get_role(ctx: ToolContext, name: str) -> dict:
    """Show one role by name: its users, groups and nested roles, and which members may administer it."""
    return visible_role(ctx, call(ctx, f"roles/name/{check_name(name, 'name')}"))


@pack_tool(effect="read", requires_connection=True)
def get_role_by_id(ctx: ToolContext, id: int) -> dict:
    """Show one role by its numeric id."""
    return visible_role(ctx, call(ctx, f"roles/{id}"))


@pack_tool(effect="read", requires_connection=True)
def get_user_roles(ctx: ToolContext, user: str = "") -> dict:
    """List the roles a user holds, directly or through their groups. Leave user empty for the calling user."""
    who = ctx.caller.username if scoped(ctx) or not user else check_name(user, "user")
    names = call(ctx, f"roles/user/{who}") or []
    return {"user": who, "roles": names, "total": len(names)}


# ---- Security zones -----------------------------------------------------------------------------------------------

@pack_tool(effect="read", requires_connection=True)
def list_zone_headers(ctx: ToolContext) -> dict:
    """List security zones by id and name. Zones carve a service's resources into areas with their own administrators and policies."""
    headers = call(ctx, "zone-headers") or []
    return {"zones": [zone_header(h) for h in headers], "total": len(headers)}


@pack_tool(effect="read", requires_connection=True)
def get_zone_names_for_resource(ctx: ToolContext, service: str, resource: str) -> dict:
    """Tell which security zone(s) a resource of a service falls in, for example service cm_hive and database=finance."""
    wanted = resource_params(resource)
    if not wanted:
        raise ValueError("Give the resource as name=value pairs, for example database=finance")
    names = call(ctx, f"zone-names/{check_name(service, 'service')}/resource", wanted) or []
    return {"service": service, "resource": parse_resource(resource), "zones": names}


@pack_tool(effect="read", requires_connection=True)
def list_zones(ctx: ToolContext) -> dict:
    """List every security zone with the services and resources it covers and who administers and audits it."""
    zones = call(ctx, "zones") or []
    return {"zones": [zone_summary(z) for z in zones], "total": len(zones)}


@pack_tool(effect="read", requires_connection=True)
def list_zones_v2(ctx: ToolContext) -> dict:
    """List every security zone through the v2 endpoint, which Ranger 2.4 and later recommend; same content as list_zones, with role-based administrators where configured."""
    zones = call(ctx, "zones-v2") or []
    return {"zones": [zone_summary(z) for z in zones], "total": len(zones)}


@pack_tool(effect="read", requires_connection=True)
def get_zone_v2(ctx: ToolContext, name: str) -> dict:
    """Show one security zone by name (v2 endpoint)."""
    return zone_summary(call(ctx, f"zones-v2/name/{check_name(name, 'name')}"))


@pack_tool(effect="read", requires_connection=True)
def get_zone_v2_resources(ctx: ToolContext, name: str, service: str) -> dict:
    """List the resources of one service that a security zone covers, by zone name (v2 endpoint)."""
    resources = call(ctx, f"zones-v2/name/{check_name(name, 'name')}/resources/{check_name(service, 'service')}") or []
    return {"zone": name, "service": service, "resources": [r.get("resource", r) for r in resources], "total": len(resources)}


@pack_tool(effect="read", requires_connection=True)
def get_zone_v2_by_id(ctx: ToolContext, id: int) -> dict:
    """Show one security zone by its numeric id (v2 endpoint)."""
    return zone_summary(call(ctx, f"zones-v2/{id}"))


@pack_tool(effect="read", requires_connection=True)
def get_zone_v2_resources_by_id(ctx: ToolContext, id: int, service: str) -> dict:
    """List the resources of one service that a security zone covers, by zone id (v2 endpoint)."""
    resources = call(ctx, f"zones-v2/{id}/resources/{check_name(service, 'service')}") or []
    return {"zone_id": id, "service": service, "resources": [r.get("resource", r) for r in resources], "total": len(resources)}


@pack_tool(effect="read", requires_connection=True)
def get_zone(ctx: ToolContext, name: str) -> dict:
    """Show one security zone by name."""
    return zone_summary(call(ctx, f"zones/name/{check_name(name, 'name')}"))


@pack_tool(effect="read", requires_connection=True)
def list_zone_headers_for_service(ctx: ToolContext, service_id: int) -> dict:
    """List the security zones that include a given service, by the service's numeric id."""
    headers = call(ctx, f"zones/zone-headers/for-service/{service_id}") or []
    return {"service_id": service_id, "zones": [zone_header(h) for h in headers], "total": len(headers)}


@pack_tool(effect="read", requires_connection=True)
def get_zone_by_id(ctx: ToolContext, id: int) -> dict:
    """Show one security zone by its numeric id."""
    return zone_summary(call(ctx, f"zones/{id}"))


@pack_tool(effect="read", requires_connection=True)
def list_zone_service_headers(ctx: ToolContext, zone_id: int) -> dict:
    """List the services that a security zone covers, by the zone's numeric id."""
    headers = call(ctx, f"zones/{zone_id}/service-headers") or []
    return {"zone_id": zone_id, "services": [service_header(h) for h in headers], "total": len(headers)}
