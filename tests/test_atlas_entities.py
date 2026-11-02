"""The atlas_entities seed pack against the Atlas fake: full entities, classifications, audit, lineage and relationships,
through a service account and through a forwarded caller token."""
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
PACK = "atlas_entities"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "admin": {**BASE, "name": "Atlas", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"},
    "knox": {**BASE, "name": "Atlas via Knox", "auth_mode": "forward-token", "secret_ref": ""},
}
KNOX = {"prefix": "/gateway/cdp-proxy-api/atlas/api/atlas/v2"}


def atlas_tool(name, function, connection="admin", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Atlas", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_ATLAS"] = "admin:admin-secret"
    tools = [atlas_tool(f, f) for f in FUNCTIONS] + [atlas_tool(f"knox_{f}", f, "knox", KNOX) for f in ("get_entity", "get_lineage", "get_relationship", "list_recently_classified", "get_entities")]
    tools += [atlas_tool("shallow", "get_lineage", "admin", {"max_lineage_depth": 2}), atlas_tool("old_probe_like", "list_recently_classified", "admin", {"prefix": "/atlas-1/api/atlas/v2"})]
    bundle = compile_bundle(tools, CONNECTIONS, [MOCK], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)
        os.environ.pop("FACTORY_SECRET_ATLAS", None)


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


def test_the_seed_declares_thirteen_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 13
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_entities_and_headers(executor):
    customers = ok(executor, "get_entity", guid="tbl-customers")
    assert customers["qualified_name"] == "sales.customers@cm" and customers["type"] == "hive_table" and customers["status"] == "active"
    assert customers["classifications"] == [{"name": "PII", "propagates": True}] and customers["terms"] == ["Customer"]
    assert customers["created"] == "2025-10-09T08:53:20+00:00" and customers["updated_by"] == "steward" and customers["version"] == 2
    assert customers["attributes"] == {"tableType": "MANAGED_TABLE"}
    assert customers["relationships"]["db"] == [{"guid": "db-sales", "type": "hive_db", "name": "sales", "relationship_guid": "rel-2", "status": "active"}]
    assert [c["name"] for c in customers["relationships"]["columns"]] == ["email"] and [m["name"] for m in customers["relationships"]["meanings"]] == ["Customer"]
    salary = ok(executor, "get_entity", guid="col-salary")
    assert salary["classifications"] == [{"name": "PII", "attributes": {"type": "salary"}, "propagates": True}, {"name": "Confidential", "propagated_from": "tbl-payroll", "propagates": True}]
    assert "not found" in error(executor, "get_entity", guid="nope")
    assert ok(executor, "get_entity_header", guid="db-finance") == {"guid": "db-finance", "type": "hive_db", "name": "finance", "qualified_name": "finance@cm", "owner": "bob", "description": "Finance ledger", "status": "active"}
    several = ok(executor, "get_entities", guids="tbl-orders, tbl-payroll")
    assert [e["name"] for e in several["entities"]] == ["orders", "payroll"] and several["count"] == 2
    assert "not found" in error(executor, "get_entities", guids="tbl-orders,nope")
    assert "at least one guid" in error(executor, "get_entities", guids=" , ")
    by_name = ok(executor, "get_entity_by_qualified_name", type_name="hive_table", qualified_name="sales.orders@cm")
    assert by_name["guid"] == "tbl-orders" and by_name["relationships"]["inputToProcesses"][0]["name"] == "summarise_orders"
    assert "does not exist" in error(executor, "get_entity_by_qualified_name", type_name="hive_table", qualified_name="nope@cm")
    assert "Give the qualified_name" in error(executor, "get_entity_by_qualified_name", type_name="hive_table", qualified_name="")
    assert ok(executor, "get_entity_header_by_qualified_name", type_name="hdfs_path", qualified_name="/data/shared@cm")["guid"] == "path-shared"
    many = ok(executor, "get_entities_by_qualified_names", type_name="hive_db", qualified_names="sales@cm, finance@cm")
    assert [e["name"] for e in many["entities"]] == ["sales", "finance"]
    recent = ok(executor, "list_recently_classified")
    assert sorted(e["name"] for e in recent["entities"]) == ["customers", "email", "orders", "payroll", "salary"] and recent["count"] == 5
    assert ok(executor, "list_recently_classified", since="2026-01-01T00:00:00Z") == {"since": "2026-01-01T00:00:00Z", "entities": [], "count": 0}
    assert "ISO 8601" in error(executor, "list_recently_classified", since="yesterday")
    assert "does not offer entity headers" in error(executor, "old_probe_like")


@gateway
def test_classifications_and_history(executor):
    tags = ok(executor, "get_classifications", guid="col-salary")
    assert tags == {"guid": "col-salary", "classifications": [{"name": "PII", "attributes": {"type": "salary"}, "propagates": True}, {"name": "Confidential", "propagated_from": "tbl-payroll", "propagates": True}], "count": 2}
    assert ok(executor, "get_classifications", guid="tbl-orders") == {"guid": "tbl-orders", "classifications": [{"name": "Curated", "propagates": True}], "count": 1}
    assert ok(executor, "get_classification", guid="tbl-payroll", name="Confidential") == {"guid": "tbl-payroll", "name": "Confidential", "attributes": {"level": "high"}, "propagates": True}
    assert "not associated" in error(executor, "get_classification", guid="tbl-payroll", name="Curated")
    history = ok(executor, "get_audit_events", guid="tbl-customers")
    assert [e["action"] for e in history["events"]] == ["TERM_ADD", "CLASSIFICATION_ADD", "ENTITY_CREATE"] and history["events"][0] == {"time": "2025-10-09T10:53:20+00:00", "user": "steward", "action": "TERM_ADD", "details": "Added term: Customer"}
    assert "next_key" not in history
    first = ok(executor, "get_audit_events", guid="tbl-customers", limit=1)
    assert [e["action"] for e in first["events"]] == ["TERM_ADD"] and first["next_key"] == "tbl-customers:1760007200000"
    second = ok(executor, "get_audit_events", guid="tbl-customers", limit=1, start_key=first["next_key"])
    assert [e["action"] for e in second["events"]] == ["CLASSIFICATION_ADD"]
    assert [e["action"] for e in ok(executor, "get_audit_events", guid="tbl-customers", action="ENTITY_CREATE")["events"]] == ["ENTITY_CREATE"]
    assert ok(executor, "get_audit_events", guid="db-sales")["events"] == []


@gateway
def test_lineage_and_relationships(executor):
    both = ok(executor, "get_lineage", guid="tbl-orders")
    assert both["entity"]["name"] == "orders" and both["direction"] == "both" and both["depth"] == 3
    assert sorted(d["name"] for d in both["datasets"]) == ["order_summary", "shared"] and sorted(p["name"] for p in both["processes"]) == ["load_orders", "summarise_orders"]
    assert both["edges"] == [{"from": "path-shared", "to": "proc-load-orders"}, {"from": "proc-load-orders", "to": "tbl-orders"}, {"from": "proc-summarise", "to": "tbl-order-summary"}, {"from": "tbl-orders", "to": "proc-summarise"}]
    upstream = ok(executor, "get_lineage", guid="tbl-orders", direction="upstream")
    assert [d["name"] for d in upstream["datasets"]] == ["shared"] and [p["name"] for p in upstream["processes"]] == ["load_orders"]
    downstream = ok(executor, "get_lineage", guid="tbl-orders", direction="output", depth=1)
    assert [d["name"] for d in downstream["datasets"]] == ["order_summary"]
    assert ok(executor, "get_lineage", guid="tbl-payroll")["note"] == "no lineage recorded for this entity"
    assert "upstream (input), downstream (output) or both" in error(executor, "get_lineage", guid="tbl-orders", direction="sideways")
    assert "between 1 and 10" in error(executor, "get_lineage", guid="tbl-orders", depth=11)
    assert "between 1 and 2" in error(executor, "shallow", guid="tbl-orders", depth=3)
    by_name = ok(executor, "get_lineage_by_qualified_name", type_name="hive_table", qualified_name="sales.order_summary@cm", direction="input", depth=5)
    assert sorted(d["name"] for d in by_name["datasets"]) == ["orders", "shared"]
    rel = ok(executor, "get_relationship", guid="rel-4")
    assert rel == {"guid": "rel-4", "type": "hive_table_columns", "status": "active", "from": {"guid": "tbl-customers", "type": "hive_table", "qualified_name": "sales.customers@cm"}, "to": {"guid": "col-email", "type": "hive_column", "qualified_name": "sales.customers.email@cm"}, "propagate_tags": "NONE", "created_by": "atlas-sync", "created": "2025-10-09T08:53:20+00:00", "updated": "2025-10-09T08:53:20+00:00"}
    assert [e["name"] for e in ok(executor, "get_relationship", guid="rel-4", with_entities=True)["entities"]] == ["customers", "email"]
    assert "not found" in error(executor, "get_relationship", guid="rel-99")


@gateway
def test_a_forwarded_token_sees_only_the_callers_entities(executor):
    alice, bob = jwt_for("alice"), jwt_for("bob")
    assert "credentials" in error(executor, "knox_get_entity", guid="tbl-orders")
    assert ok(executor, "knox_get_entity", caller="alice", token=alice, guid="tbl-orders")["name"] == "orders"
    assert "not authorized" in error(executor, "knox_get_entity", caller="alice", token=alice, guid="tbl-payroll")
    assert ok(executor, "knox_get_entity", caller="bob", token=bob, guid="tbl-payroll")["name"] == "payroll"
    assert [e["name"] for e in ok(executor, "knox_get_entities", caller="alice", token=alice, guids="tbl-orders,tbl-payroll")["entities"]] == ["orders"]  # the forbidden one is left out
    assert "not authorized" in error(executor, "knox_get_entities", caller="alice", token=alice, guids="tbl-payroll")
    assert sorted(d["name"] for d in ok(executor, "knox_get_lineage", caller="alice", token=alice, guid="tbl-orders")["datasets"]) == ["order_summary", "shared"]
    assert "not authorized" in error(executor, "knox_get_relationship", caller="alice", token=alice, guid="rel-5")
    assert sorted(e["name"] for e in ok(executor, "knox_list_recently_classified", caller="bob", token=bob)["entities"]) == ["payroll", "salary"]


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_ATLAS", "admin:admin-secret")
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Atlas", "base_url": MOCK, "protocol": "rest", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"}).json()
    tool = client.post("/api/tools", json={"name": "explain_entity", "description": "Entity details.", "kind": "python", "pack": PACK, "function": "get_entity", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Atlas answered: 5 classified entit(ies) visible to this identity"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"guid": "tbl-customers"}}}).json()
    assert result["success"], result
    assert result["result"]["structuredContent"]["terms"] == ["Customer"]
