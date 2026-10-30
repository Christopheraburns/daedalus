"""The ranger_public seed pack against the Ranger fake: direct and Knox prefixes, Basic and forwarded credentials,
an auditor and a limited account, whole-instance and caller scope, and a Ranger without roles or zones."""
import base64
import json
import os

import httpx
import pytest

from factory import packs, packstore
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, TOKEN_HEADER, USER_HEADER, start_executor, stop_process

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"
PACK = "ranger_public"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "auditor": {**BASE, "name": "Ranger", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_RANGER"},
    "alice": {**BASE, "name": "Ranger as alice", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_RANGER_ALICE"},
    "knox": {**BASE, "name": "Ranger via Knox", "auth_mode": "forward-token", "secret_ref": ""},
}
KNOX = {"prefix": "/gateway/cdp-proxy-api/ranger/service/public/v2/api", "scope": "caller"}
OLD = {"prefix": "/ranger-1/service/public/v2/api"}


def ranger_tool(name, function, connection="auditor", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Ranger", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    """What the gateway hands the executor after verifying a Knox JWT: the token itself, whose subject the fake trusts."""
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject, "iss": "https://knox.example/gateway"}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_RANGER"] = "auditor:auditor-secret"
    os.environ["FACTORY_SECRET_RANGER_ALICE"] = "alice:alice-secret"
    tools = [ranger_tool(f, f) for f in FUNCTIONS]
    tools += [ranger_tool(f"knox_{f}", f, "knox", KNOX) for f in FUNCTIONS]
    tools += [ranger_tool(f"scoped_{f}", f, "auditor", {"scope": "caller"}) for f in ("search_policies", "get_policy", "get_policies_for_resource", "list_roles", "get_role", "get_user_roles")]
    tools += [ranger_tool(f"alice_{f}", f, "alice") for f in ("search_policies", "get_user_roles", "list_services")]
    tools += [ranger_tool(f"old_{f}", f, "auditor", OLD) for f in ("search_policies", "list_role_names", "list_zones", "get_user_roles")]
    tools += [ranger_tool("bad_scope", "search_policies", "auditor", {"scope": "mine"}), ranger_tool("bad_prefix", "list_services", "auditor", {"prefix": "/nowhere"})]
    bundle = compile_bundle(tools, CONNECTIONS, [MOCK], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)
        os.environ.pop("FACTORY_SECRET_RANGER", None)
        os.environ.pop("FACTORY_SECRET_RANGER_ALICE", None)


def call(executor, tool, caller="alice", token=None, **arguments):
    headers = {KEY_HEADER: executor.key, USER_HEADER: caller, **({TOKEN_HEADER: token} if token else {})}
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{tool}", headers=headers, json=arguments, timeout=30)
    return response.status_code, response.json()


def ok(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status == 200, payload
    return payload


def error(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


def names(policies):
    return sorted(p["name"] for p in policies)


def test_the_seed_declares_thirty_one_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 31
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_services_and_service_types(executor):
    types = ok(executor, "list_service_types")
    assert [t["name"] for t in types["service_types"]] == ["hdfs", "hive"] and types["total"] == 2
    hive = ok(executor, "get_service_type", name="hive")
    assert [r["name"] for r in hive["resources"]] == ["database", "table", "column"] and "select" in hive["access_types"] and hive["resources"][1]["parent"] == "database"
    assert ok(executor, "get_service_type_by_id", id=1)["name"] == "hdfs"
    assert "not found" in error(executor, "get_service_type", name="kafka")
    services = ok(executor, "list_services")
    assert [s["name"] for s in services["services"]] == ["cm_hdfs", "cm_hive"]
    assert [s["name"] for s in ok(executor, "list_services", service_type="hive")["services"]] == ["cm_hive"]
    assert [s["name"] for s in ok(executor, "list_services", name_contains="HDFS")["services"]] == ["cm_hdfs"]
    assert ok(executor, "list_service_headers") == {"services": [{"id": 1, "name": "cm_hdfs", "display_name": "cm_hdfs", "type": "hdfs", "enabled": True}, {"id": 2, "name": "cm_hive", "display_name": "Hadoop SQL", "type": "hive", "enabled": True}], "total": 2}
    service = ok(executor, "get_service", name="cm_hive")
    assert service["type"] == "hive" and service["policy_version"] == 31 and service["configs"]["jdbc.url"].startswith("jdbc:hive2") and "password" not in json.dumps(service)
    assert ok(executor, "get_service_by_id", id=1)["name"] == "cm_hdfs"
    tags = ok(executor, "get_service_tags", service="cm_hive")
    assert tags["tag_types"] == ["PII"] and tags["tagged_resources"] == [{"resource": {"database": ["finance"], "table": ["payroll"], "column": ["salary"]}, "tags": [{"type": "PII", "attributes": {"type": "salary"}}]}]
    assert ok(executor, "get_service_tags", service="cm_hdfs")["tagged_resources"] == []


@gateway
def test_policies_for_the_whole_instance(executor):
    everything = ok(executor, "search_policies")
    assert names(everything["policies"]) == ["alice home", "all - path", "finance database", "mask salaries", "sales database", "shared datasets"] and not everything["truncated"] and "scoped_to" not in everything
    page = ok(executor, "search_policies", limit=2)
    assert len(page["policies"]) == 2 and page["truncated"]
    assert names(ok(executor, "search_policies", service="cm_hive")["policies"]) == ["finance database", "mask salaries", "sales database"]
    assert names(ok(executor, "search_policies", user="bob")["policies"]) == ["finance database"]  # through the finance group and the finance_admins role
    assert names(ok(executor, "search_policies", user="alice")["policies"]) == ["alice home", "mask salaries", "sales database", "shared datasets"]
    assert names(ok(executor, "search_policies", group="analysts")["policies"]) == ["mask salaries", "sales database", "shared datasets"]
    assert names(ok(executor, "search_policies", role="data_stewards")["policies"]) == ["sales database", "shared datasets"]
    assert names(ok(executor, "search_policies", zone="finance-zone")["policies"]) == ["finance database", "mask salaries"]
    assert names(ok(executor, "search_policies", policy_type="masking")["policies"]) == ["mask salaries"]
    assert "access, masking or row-filter" in error(executor, "search_policies", policy_type="deny")
    assert names(ok(executor, "search_policies", resource="database=finance")["policies"]) == ["finance database", "mask salaries"]
    assert "name=value" in error(executor, "search_policies", resource="finance")
    listed = ok(executor, "list_service_policies", service="cm_hdfs")
    assert names(listed["policies"]) == ["alice home", "all - path", "shared datasets"]
    assert names(ok(executor, "list_service_policies", service="cm_hive", zone="finance-zone", name_contains="mask")["policies"]) == ["mask salaries"]
    assert "not found" in error(executor, "list_service_policies", service="cm_kafka")
    shared = ok(executor, "get_policy", id=2)
    assert shared["resources"] == {"path": {"values": ["/data/shared"], "recursive": True}} and shared["policy_type"] == "access"
    assert shared["allow"] == [{"accesses": ["read", "execute"], "groups": ["analysts"]}, {"accesses": ["read", "write", "execute"], "roles": ["data_stewards"]}]
    assert "deny" not in shared and "zone" not in shared
    mask = ok(executor, "get_policy_by_name", service="cm_hive", name="mask salaries", zone="finance-zone")
    assert mask["policy_type"] == "masking" and mask["masks"] == [{"accesses": ["select"], "groups": ["analysts"], "mask": "MASK"}]
    assert "not found" in error(executor, "get_policy_by_name", service="cm_hive", name="mask salaries")  # the zone is part of the identity
    assert ok(executor, "get_policy_by_guid", guid="p-0005-cm_hive", zone="finance-zone")["name"] == "finance database"
    assert "not found" in error(executor, "get_policy", id=99)
    payroll = ok(executor, "get_policies_for_resource", service_type="hive", resource="database=finance, table=payroll")
    assert names(payroll["policies"]) == ["finance database", "mask salaries"] and payroll["resource"] == {"database": "finance", "table": "payroll"}
    assert names(ok(executor, "get_policies_for_resource", service_type="hdfs", resource="path=/data/shared/2026")["policies"]) == ["all - path", "shared datasets"]
    assert names(ok(executor, "get_policies_for_resource", service_type="hdfs", resource=json.dumps({"path": "/user/alice/notes"}), service="cm_hdfs")["policies"]) == ["alice home", "all - path"]
    assert "name=value" in error(executor, "get_policies_for_resource", service_type="hdfs", resource="")
    assert "not found" in error(executor, "get_policies_for_resource", service_type="kafka", resource="topic=x")


@gateway
def test_roles_and_zones(executor):
    roles = ok(executor, "list_roles")
    assert [r["name"] for r in roles["roles"]] == ["data_stewards", "finance_admins"]
    assert roles["roles"][0] == {"id": 1, "name": "data_stewards", "description": "Curate shared datasets", "enabled": True, "users": ["alice", "carol"], "user_admins": ["carol"], "groups": ["analysts"]}
    assert [r["name"] for r in ok(executor, "list_roles", user="bob")["roles"]] == ["finance_admins"]
    assert [r["name"] for r in ok(executor, "list_roles", group="analysts")["roles"]] == ["data_stewards"]
    assert [r["name"] for r in ok(executor, "list_roles", name_contains="FIN")["roles"]] == ["finance_admins"]
    assert ok(executor, "list_role_names") == {"roles": ["data_stewards", "finance_admins"], "total": 2}
    assert ok(executor, "get_role", name="finance_admins")["user_admins"] == ["bob"]
    assert ok(executor, "get_role_by_id", id=1)["name"] == "data_stewards"
    assert "not found" in error(executor, "get_role", name="nobody")
    assert ok(executor, "get_user_roles", user="carol") == {"user": "carol", "roles": ["data_stewards", "finance_admins"], "total": 2}
    assert ok(executor, "get_user_roles") == {"user": "alice", "roles": ["data_stewards"], "total": 1}  # empty user means the caller
    assert ok(executor, "list_zone_headers") == {"zones": [{"id": 1, "name": "finance-zone"}], "total": 1}
    assert ok(executor, "get_zone_names_for_resource", service="cm_hive", resource="database=finance")["zones"] == ["finance-zone"]
    assert ok(executor, "get_zone_names_for_resource", service="cm_hive", resource="database=sales")["zones"] == []
    zone = ok(executor, "list_zones")["zones"][0]
    assert zone["services"] == {"cm_hive": [{"database": ["finance"]}]} and zone["admin_users"] == ["bob"] and zone["admin_groups"] == ["finance"] and zone["audit_users"] == ["auditor"]
    assert ok(executor, "list_zones_v2")["zones"][0]["name"] == "finance-zone"
    assert ok(executor, "get_zone_v2", name="finance-zone")["id"] == 1
    assert ok(executor, "get_zone_v2_resources", name="finance-zone", service="cm_hive") == {"zone": "finance-zone", "service": "cm_hive", "resources": [{"database": ["finance"]}], "total": 1}
    assert "not part of zone" in error(executor, "get_zone_v2_resources", name="finance-zone", service="cm_hdfs")
    assert ok(executor, "get_zone_v2_by_id", id=1)["name"] == "finance-zone"
    assert ok(executor, "get_zone_v2_resources_by_id", id=1, service="cm_hive")["total"] == 1
    assert ok(executor, "get_zone", name="finance-zone")["description"].startswith("Finance data")
    assert ok(executor, "list_zone_headers_for_service", service_id=2)["zones"] == [{"id": 1, "name": "finance-zone"}]
    assert ok(executor, "list_zone_headers_for_service", service_id=1)["zones"] == []
    assert ok(executor, "get_zone_by_id", id=1)["name"] == "finance-zone"
    assert ok(executor, "list_zone_service_headers", zone_id=1)["services"][0]["name"] == "cm_hive"
    assert "not found" in error(executor, "get_zone", name="nope")


@gateway
def test_caller_scope_narrows_policies_and_roles_to_the_calling_user(executor):
    mine = ok(executor, "scoped_search_policies")
    assert names(mine["policies"]) == ["alice home", "mask salaries", "sales database", "shared datasets"] and mine["scoped_to"] == "alice"
    assert names(ok(executor, "scoped_search_policies", user="bob")["policies"]) == names(mine["policies"])  # the user filter cannot widen the scope
    assert names(ok(executor, "scoped_search_policies", caller="bob")["policies"]) == ["finance database"]  # a different caller sees their own
    assert ok(executor, "scoped_get_policy", id=3)["name"] == "alice home"
    assert "not visible to alice" in error(executor, "scoped_get_policy", id=5)  # finance database grants alice nothing
    assert "not visible to alice" in error(executor, "scoped_get_policy", id=99)  # and a missing one looks the same
    payroll = ok(executor, "scoped_get_policies_for_resource", service_type="hive", resource="database=finance, table=payroll")
    assert names(payroll["policies"]) == ["mask salaries"] and payroll["scoped_to"] == "alice"
    assert [r["name"] for r in ok(executor, "scoped_list_roles")["roles"]] == ["data_stewards"]
    assert [r["name"] for r in ok(executor, "scoped_list_roles", user="bob")["roles"]] == ["data_stewards"]
    assert ok(executor, "scoped_get_role", name="data_stewards")["name"] == "data_stewards"
    assert "not visible to alice" in error(executor, "scoped_get_role", name="finance_admins")
    assert ok(executor, "scoped_get_user_roles", user="bob") == {"user": "alice", "roles": ["data_stewards"], "total": 1}
    assert "scope must be one of" in error(executor, "bad_scope")


@gateway
def test_knox_prefix_with_the_callers_forwarded_token(executor):
    token = jwt_for("bob")
    assert "credentials" in error(executor, "knox_list_services")  # no token forwarded: Ranger answers 401
    # bob is a plain user at Ranger: policies are refused, but his own roles are visible.
    assert "only administrators and auditors" in error(executor, "knox_search_policies", caller="bob", token=token)
    assert ok(executor, "knox_get_user_roles", caller="bob", token=token) == {"user": "bob", "roles": ["finance_admins"], "total": 1}
    assert ok(executor, "knox_list_role_names", caller="bob", token=token) == {"roles": ["finance_admins"], "total": 1, "scoped_to": "bob"}
    # The auditor through Knox in caller scope: narrowed to the auditor's own grants, which are none.
    auditor = jwt_for("auditor")
    assert ok(executor, "knox_search_policies", caller="auditor", token=auditor) == {"policies": [], "offset": 0, "truncated": False, "scoped_to": "auditor"}
    assert ok(executor, "knox_list_zones", caller="auditor", token=auditor)["total"] == 1  # structure is never narrowed


@gateway
def test_a_limited_service_account_and_an_old_ranger_explain_themselves(executor):
    assert "only administrators and auditors" in error(executor, "alice_search_policies")
    assert "only administrators and auditors" in error(executor, "alice_list_services")
    assert ok(executor, "alice_get_user_roles") == {"user": "alice", "roles": ["data_stewards"], "total": 1}
    assert "not authorized to view roles of bob" in error(executor, "alice_get_user_roles", user="bob")
    assert names(ok(executor, "old_search_policies", service="cm_hdfs")["policies"]) == ["alice home", "all - path", "shared datasets"]
    assert "does not offer roles" in error(executor, "old_list_role_names")
    assert "does not offer security zones" in error(executor, "old_list_zones")
    assert "does not offer roles" in error(executor, "old_get_user_roles")
    assert "check the prefix" in error(executor, "bad_prefix")


@gateway
def test_the_builder_checks_a_ranger_connection_with_the_packs_own_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_RANGER", "auditor:auditor-secret")
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Ranger", "base_url": MOCK, "protocol": "rest", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_RANGER"}).json()
    # Without Ranger tools the generic REST probe checks the connection.
    generic = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert generic["probe_summary"]["pack"] == "rest", generic
    tool = client.post("/api/tools", json={"name": "who_may_access", "description": "Policies for a resource.", "kind": "python", "pack": PACK, "function": "get_policies_for_resource", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = client.get(f"/api/connections/{connection['id']}").json() if client.get(f"/api/connections/{connection['id']}").status_code == 200 else next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Ranger answered: 2 service(s) guarded; offers roles, security zones"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"service_type": "hive", "resource": "database=finance, table=payroll"}}}).json()
    assert result["success"], result
    assert sorted(p["name"] for p in result["result"]["structuredContent"]["policies"]) == ["finance database", "mask salaries"]
    monkeypatch.setenv("FACTORY_SECRET_RANGER", "auditor:wrong")
    failed = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(checked["revision"])}).json()
    assert not failed["probe_summary"]["success"] and "credentials" in failed["probe_summary"]["message"]
