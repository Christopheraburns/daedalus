"""The cdp_lakehouseopt seed pack against the control plane fake: environments, namespaces, tables, policies,
associations, status details and tasks, signed with a CDP API key (the new cdp-apikey connection mode)."""
import base64
import json
import os

import httpx
import pytest

from factory import packs, packstore
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, USER_HEADER, start_executor, stop_process

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"
PACK = "cdp_lakehouseopt"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
ACCESS_KEY_ID = "e6a3f9c1-daedalus-test-key"
PRIVATE_KEY = base64.b64encode(bytes(range(32))).decode()  # the seed the fake's public key belongs to
SECRET = f"{ACCESS_KEY_ID}:{PRIVATE_KEY}"
PROD = "crn:cdp:datahub:us-west-1:tenant:cluster:clo-prod"
EU = "crn:cdp:datahub:eu-1:tenant:cluster:clo-eu"
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "cdp": {**BASE, "name": "CDP", "auth_mode": "cdp-apikey", "secret_ref": "FACTORY_SECRET_CDP"},
    "wrong": {**BASE, "name": "CDP wrong key", "auth_mode": "cdp-apikey", "secret_ref": "FACTORY_SECRET_CDP_WRONG"},
    "anonymous": {**BASE, "name": "CDP unsigned", "auth_mode": "none", "secret_ref": ""},
}


def cdp_tool(name, function, connection="cdp", config=None):
    spec = ToolSpec(name=name, description=f"{function} on CDP", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config if config is not None else {"datahub_crn": PROD}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_CDP"] = SECRET
    os.environ["FACTORY_SECRET_CDP_WRONG"] = f"{ACCESS_KEY_ID}:{base64.b64encode(bytes(32)).decode()}"
    tools = [cdp_tool(f, f) for f in FUNCTIONS]
    tools += [cdp_tool("no_default_crn", "list_namespaces", config={}), cdp_tool("wrong_key", "list_environments", "wrong"), cdp_tool("unsigned", "list_environments", "anonymous"),
        cdp_tool("tiny", "list_environments", config={"page_size": 2}), cdp_tool("bad_prefix", "list_environments", config={"prefix": "/nowhere"})]
    bundle = compile_bundle(tools, CONNECTIONS, [MOCK], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)
        os.environ.pop("FACTORY_SECRET_CDP", None)
        os.environ.pop("FACTORY_SECRET_CDP_WRONG", None)


def call(executor, tool, caller="alice", **arguments):
    headers = {KEY_HEADER: executor.key, USER_HEADER: caller}
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


def names(items, key="name"):
    return [i[key] for i in items]


def test_the_seed_declares_fourteen_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 14
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_environments_and_catalogue(executor):
    envs = ok(executor, "list_environments")
    assert names(envs["environments"]) == ["prod-env", "dev-env", "eu-env"] and envs["total"] == 3 and envs["count"] == 3 and "next_page_token" not in envs
    assert envs["environments"][0] == {"name": "prod-env", "crn": "crn:cdp:environments:us-west-1:tenant:environment:prod", "cloud_platform": "AWS", "optimizer_enabled": True, "datahub_name": "prod-clo", "datahub_crn": PROD, "datahub_status": "AVAILABLE"}
    assert envs["environments"][1] == {"name": "dev-env", "crn": "crn:cdp:environments:us-west-1:tenant:environment:dev", "cloud_platform": "AWS", "optimizer_enabled": False}
    first = ok(executor, "tiny", limit=50)
    assert names(first["environments"]) == ["prod-env", "dev-env"] and first["next_page_token"] == "2"
    assert names(ok(executor, "tiny", page_token="2")["environments"]) == ["eu-env"]
    assert ok(executor, "list_namespaces") == {"datahub_crn": PROD, "namespaces": ["finance", "sales"], "count": 2}
    assert ok(executor, "list_namespaces", datahub_crn=EU)["namespaces"] == ["marketing"]
    assert "list_environments shows" in error(executor, "no_default_crn")
    assert "must be a CRN" in error(executor, "list_namespaces", datahub_crn="clo-prod")
    assert "not found" in error(executor, "list_namespaces", datahub_crn="crn:cdp:datahub:us-west-1:tenant:cluster:gone")
    assert ok(executor, "list_table_names", namespace="sales") == {"namespace": "sales", "tables": ["customers", "orders"], "count": 2}
    tables = ok(executor, "list_tables", namespace="sales")
    assert tables["tables"] == [{"namespace": "sales", "name": "customers", "status": "WARNING", "policies": ["daily-compaction", "weekly-expire-snapshots"], "last_execution": "2026-10-25T03:46:40Z"},
        {"namespace": "sales", "name": "orders", "status": "SUCCESS", "policies": ["daily-compaction"], "last_execution": "2026-10-26T08:56:40Z"}]
    assert ok(executor, "list_tables", namespace="finance")["tables"][0]["status"] == "USER_PAUSED"
    assert ok(executor, "list_tables", namespace="marketing", datahub_crn=EU) == {"namespace": "marketing", "tables": [], "count": 0}
    assert "does not exist" in error(executor, "list_tables", namespace="hr")
    assert "without slashes" in error(executor, "list_tables", namespace="a/b")
    assert "check the base URL" in error(executor, "bad_prefix")


@gateway
def test_policies_and_status(executor):
    policies = ok(executor, "list_policies")
    assert names(policies["policies"]) == ["daily-compaction", "weekly-expire-snapshots", "monthly-orphan-cleanup"] and policies["count"] == 3 and "namespace" not in policies
    assert policies["policies"][0] == {"name": "daily-compaction", "status": "SUCCESS", "default": False, "tables": 2, "tasks": 3, "created": "2026-02-25T06:13:20Z", "last_execution": "2026-10-27T08:33:20Z"}
    assert policies["policies"][1]["default"] is True and policies["policies"][1]["status"] == "ERROR" and policies["policies"][2] == {"name": "monthly-orphan-cleanup", "status": "UNAVAILABLE", "default": False, "tables": 0, "tasks": 0, "created": "2026-07-25T17:20:00Z"}
    finance = ok(executor, "list_policies", namespace="finance")
    assert names(finance["policies"]) == ["weekly-expire-snapshots"] and finance["namespace"] == "finance" and finance["policies"][0]["tables"] == 1
    assert ok(executor, "list_policy_names") == {"namespace": "*", "policies": ["daily-compaction", "weekly-expire-snapshots"], "count": 2}
    assert ok(executor, "list_policy_names", namespace="finance")["policies"] == ["weekly-expire-snapshots"]
    compaction = ok(executor, "get_policy", policy_name="daily-compaction")
    assert compaction["scope"] == "Namespace" and compaction["versions"] == ["v1-daily-compaction"] and compaction["tables"] == 2 and compaction["created"] == "2026-02-25T06:13:20Z"
    assert compaction["arguments"] == {"actions": ["rewrite_data_files"], "schedule": "0 2 * * *", "timezone": "UTC", "targetFileSizeBytes": 536870912}
    assert compaction["associations"] == [{"namespace": "sales", "status": "SUCCESS", "tables": [{"name": "customers", "status": "SUCCESS", "tasks": 1, "policy_version": "v1-daily-compaction", "last_execution": "2026-10-25T03:46:40Z"}, {"name": "orders", "status": "SUCCESS", "tasks": 2, "policy_version": "v1-daily-compaction", "last_execution": "2026-10-26T08:56:40Z"}]}]
    assert "does not exist" in error(executor, "get_policy", policy_name="nightly")
    table_policies = ok(executor, "get_table_policies", namespace="sales", table_name="customers")
    assert table_policies == {"namespace": "sales", "table": "customers", "policies": [{"name": "daily-compaction", "status": "WARNING", "tasks": 1, "last_execution": "2026-10-25T03:46:40Z"}, {"name": "weekly-expire-snapshots", "status": "WARNING", "tasks": 1, "last_execution": "2026-10-25T03:46:40Z"}], "count": 2}
    assert "does not exist" in error(executor, "get_table_policies", namespace="sales", table_name="returns")
    status = ok(executor, "get_table_status", namespace="sales", table_name="customers", policy_name="weekly-expire-snapshots", status="error")
    assert status["recent_task"] == {"policy": "weekly-expire-snapshots", "last_execution": "2026-10-24T13:53:20Z", "actions": [{"action": "expire_snapshots", "status": "FAILED"}]} and "paused" not in status
    paused = ok(executor, "get_table_status", namespace="finance", table_name="ledger", policy_name="weekly-expire-snapshots", status="USER_PAUSED")
    assert paused["status"] == "PAUSED" and paused["paused"] == {"message": "Table paused by user bob", "since": "2026-09-21T00:00:00Z", "reasons": ["Quarter-end close in progress"]}
    assert "No task has run" in ok(executor, "get_table_status", namespace="sales", table_name="orders", policy_name="weekly-expire-snapshots", status="SUCCESS")["note"]
    assert "one of" in error(executor, "get_table_status", namespace="sales", table_name="orders", policy_name="daily-compaction", status="RUNNING")


@gateway
def test_associations_and_tasks(executor):
    assert ok(executor, "get_associations", policy_name="daily-compaction") == {"policy": "daily-compaction", "associations": [{"namespace": "sales", "tables": ["customers", "orders"]}], "table_count": 2}
    assert ok(executor, "get_associations", policy_name="monthly-orphan-cleanup")["associations"] == []
    namespaces = ok(executor, "get_associated_namespaces", policy_name="weekly-expire-snapshots")
    assert namespaces["namespaces"] == [{"namespace": "finance", "associated": True}, {"namespace": "sales", "associated": True}]
    assert ok(executor, "get_associated_namespaces", policy_name="daily-compaction", only_associated=True) == {"policy": "daily-compaction", "namespaces": [{"namespace": "sales", "associated": True}], "count": 1}
    tables = ok(executor, "get_associated_tables", policy_name="daily-compaction")
    assert tables["namespaces"] == [{"namespace": "finance", "tables": [{"name": "ledger", "associated": False}]}, {"namespace": "sales", "tables": [{"name": "customers", "associated": True}, {"name": "orders", "associated": True}]}] and tables["table_count"] == 3
    assert ok(executor, "get_associated_tables", policy_name="daily-compaction", only_associated=True)["namespaces"] == [{"namespace": "sales", "tables": [{"name": "customers", "associated": True}, {"name": "orders", "associated": True}]}]
    overview = ok(executor, "get_association_overview")
    assert overview["datahub_crn"] == PROD and [d["namespace"] for d in overview["direct"]] == ["finance", "sales"] and overview["direct"][1]["status"] == "WARNING"
    assert overview["direct"][1]["tables"][1] == {"name": "orders", "status": "SUCCESS", "policies": ["daily-compaction"], "last_execution": "2026-10-26T08:56:40Z"}
    assert overview["catalog_wide"] == [{"catalog": "spark_catalog", "status": "SUCCESS", "namespaces": [{"namespace": "finance", "status": "SUCCESS", "policies": ["weekly-expire-snapshots"]}, {"namespace": "sales", "status": "SUCCESS", "policies": ["weekly-expire-snapshots"]}]}]
    tasks = ok(executor, "list_tasks", namespace="sales")
    assert [(t["table"], t["status"]) for t in tasks["tasks"]] == [("orders", "SUBMITTED"), ("orders", "COMPLETED"), ("customers", "COMPLETED"), ("customers", "FAILED")] and tasks["count"] == 4 and "next_page_token" not in tasks
    assert tasks["tasks"][1] == {"id": "6b1a0e2c-0000-4000-8000-000000000001", "status": "COMPLETED", "policy": "daily-compaction", "catalog": "spark_catalog", "namespace": "sales", "table": "orders", "created": "2026-10-26T08:56:40Z", "details": {"action": "rewrite_data_files", "rewrittenFiles": 42, "addedFiles": 3, "durationSeconds": 184}}
    assert tasks["tasks"][3]["details"]["error"] == "Snapshot 8812 is referenced by a branch"
    first = ok(executor, "list_tasks", namespace="sales", limit=3)
    assert first["count"] == 3 and first["next_page_token"] == "3"
    assert [t["status"] for t in ok(executor, "list_tasks", namespace="sales", limit=3, page_token="3")["tasks"]] == ["FAILED"]
    assert ok(executor, "list_tasks", namespace="finance") == {"namespace": "finance", "count": 0, "tasks": []}


@gateway
def test_the_signature_is_what_lets_a_call_through(executor):
    assert "rejected the API key" in error(executor, "wrong_key")
    assert "rejected the API key" in error(executor, "unsigned")


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_CDP", SECRET)
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    assert client.post("/api/connections", json={"name": "Bad", "base_url": MOCK, "protocol": "rest", "auth_mode": "cdp-apikey", "secret_ref": ""}).status_code == 422
    connection = client.post("/api/connections", json={"name": "CDP", "base_url": MOCK, "protocol": "rest", "auth_mode": "cdp-apikey", "secret_ref": "FACTORY_SECRET_CDP"}).json()
    assert SECRET not in client.get("/api/workspace").text and PRIVATE_KEY not in client.get("/api/workspace").text
    rest = client.post("/api/tools", json={"name": "rest_cdp", "description": "x", "connection_id": connection["id"], "method": "GET", "path": "/fixture/echo"})
    assert rest.status_code == 201  # the gateway cannot sign for REST tools, which the test run says
    outcome = client.post(f"/api/tools/{rest.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {}})
    assert outcome.status_code in (200, 400, 409, 422) and "Python pack tools only" in outcome.text, outcome.text
    tool = client.post("/api/tools", json={"name": "table_maintenance", "description": "Which policies maintain a table.", "kind": "python", "pack": PACK, "function": "get_table_policies", "connection_id": connection["id"], "config": {"datahub_crn": PROD}})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "CDP answered: 3 environments, 2 with Lakehouse Optimizer enabled"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"namespace": "sales", "table_name": "orders"}}}).json()
    assert result["success"], result
    assert [p["name"] for p in result["result"]["structuredContent"]["policies"]] == ["daily-compaction"]
    monkeypatch.setenv("FACTORY_SECRET_CDP", "no-colon")
    broken = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"namespace": "sales", "table_name": "orders"}}}).json()
    assert not broken.get("success") and "ACCESS_KEY_ID:PRIVATE_KEY" in json.dumps(broken), broken
