"""The atlas_discovery seed pack against the Atlas fake: direct and Knox prefixes, Basic and forwarded credentials
(Atlas filters by identity), and an Atlas without the newer search endpoints."""
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
PACK = "atlas_discovery"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "admin": {**BASE, "name": "Atlas", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"},
    "knox": {**BASE, "name": "Atlas via Knox", "auth_mode": "forward-token", "secret_ref": ""},
}
KNOX = {"prefix": "/gateway/cdp-proxy-api/atlas/api/atlas/v2"}
OLD = {"prefix": "/atlas-1/api/atlas/v2"}


def atlas_tool(name, function, connection="admin", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Atlas", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_ATLAS"] = "admin:admin-secret"
    tools = [atlas_tool(f, f) for f in FUNCTIONS]
    tools += [atlas_tool(f"knox_{f}", f, "knox", KNOX) for f in FUNCTIONS]
    tools += [atlas_tool(f"old_{f}", f, "admin", OLD) for f in ("search_basic", "quick_search", "search_relations", "get_related_entities", "suggest")]
    tools += [atlas_tool("small_pages", "search_basic", "admin", {"page_size": 2}), atlas_tool("with_deleted", "search_basic", "admin", {"include_deleted": True}), atlas_tool("bad_prefix", "search_basic", "admin", {"prefix": "/nowhere"})]
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


def names(result):
    return sorted(e["name"] for e in result["entities"])


def test_the_seed_declares_thirteen_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 13
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_searches(executor):
    tables = ok(executor, "search_basic", type_name="hive_table")
    assert names(tables) == ["customers", "order_summary", "orders", "payroll"] and tables["count"] == 4 and not tables["truncated"] and tables["approximate_total"] == 4
    customers = next(e for e in tables["entities"] if e["name"] == "customers")
    assert customers == {"guid": "tbl-customers", "type": "hive_table", "name": "customers", "qualified_name": "sales.customers@cm", "owner": "alice", "description": "Customer master data", "status": "active", "classifications": ["PII"], "terms": ["Customer"]}
    assert names(ok(executor, "search_basic", classification="PII")) == ["customers", "email", "payroll", "salary"]
    assert names(ok(executor, "search_basic", query="payroll")) == ["payroll", "salary"]
    assert names(ok(executor, "search_basic", type_name="hive_table", include_deleted=True)) == ["customers", "order_summary", "orders", "orders_2019", "payroll"]
    assert names(ok(executor, "with_deleted", type_name="hive_table")) == ["customers", "order_summary", "orders", "orders_2019", "payroll"]
    assert "Give a query" in error(executor, "search_basic")
    assert "ASCENDING or DESCENDING" in error(executor, "search_basic", type_name="hive_table", sort_by="name", sort_order="up")
    first = ok(executor, "small_pages", type_name="hive_table", limit=50)
    assert first["count"] == 2 and first["truncated"] and first["approximate_total"] == 4
    rest = ok(executor, "small_pages", type_name="hive_table", offset=2)
    assert rest["count"] == 2 and not rest["truncated"]
    filtered = ok(executor, "search_with_filters", type_name="hive_table", filters="owner = alice, name like orders*", attributes="tableType")
    assert names(filtered) == ["orders"] and filtered["entities"][0]["attributes"] == {"tableType": "MANAGED_TABLE"}
    assert names(ok(executor, "search_with_filters", type_name="hive_table", term="Customer")) == ["customers"]
    assert names(ok(executor, "search_with_filters", type_name="hive_table", filters=json.dumps({"condition": "OR", "criterion": [{"attributeName": "owner", "operator": "eq", "attributeValue": "bob"}, {"attributeName": "name", "operator": "startsWith", "attributeValue": "cust"}]}))) == ["customers", "payroll"]
    assert "attribute operator value" in error(executor, "search_with_filters", type_name="hive_table", filters="owner")
    dsl = ok(executor, "search_dsl", query="hive_table where owner = 'alice' select name, qualifiedName")
    assert dsl["columns"] == ["name", "qualifiedName"] and sorted(dsl["rows"]) == [["customers", "sales.customers@cm"], ["order_summary", "sales.order_summary@cm"], ["orders", "sales.orders@cm"]] and dsl["count"] == 3 and dsl["query"].startswith("hive_table")
    assert names(ok(executor, "search_dsl", query="hive_table isa PII")) == ["customers", "payroll"]
    assert names(ok(executor, "search_dsl", query="where name like 'ord*'", type_name="hive_table")) == ["order_summary", "orders"]
    assert "Invalid DSL" in error(executor, "search_dsl", query="select * from nowhere;")
    assert "Give a DSL query" in error(executor, "search_dsl", query="  ")
    assert names(ok(executor, "search_full_text", query="ledger")) == ["finance"]
    assert names(ok(executor, "search_full_text", query="archived")) == []
    assert names(ok(executor, "search_full_text", query="archived", include_deleted=True)) == ["orders_2019"]
    quick = ok(executor, "quick_search", query="sales")
    assert names(quick) == ["customers", "email", "load_orders", "order_summary", "orders", "sales", "summarise_orders"] and quick["by_type"] == {"hive_db": 1, "hive_table": 3, "hive_column": 1, "hive_process": 2}
    assert names(ok(executor, "quick_search", query="sales", type_name="hive_table")) == ["customers", "order_summary", "orders"]
    assert names(ok(executor, "search_by_attribute", attribute="qualifiedName", value_prefix="finance.")) == ["payroll", "salary"]
    assert names(ok(executor, "search_by_attribute", attribute="owner", value_prefix="ali", type_name="hive_db")) == ["sales"]
    assert "without slashes" in error(executor, "search_by_attribute", attribute=" ", value_prefix="x")


@gateway
def test_relationships_saved_searches_and_suggestions(executor):
    relations = ok(executor, "search_relations", relationship_type="hive_table_columns")
    assert relations["count"] == 2 and relations["relations"][0] == {"guid": "rel-4", "type": "hive_table_columns", "status": "active", "from": {"guid": "tbl-customers", "type": "hive_table", "qualified_name": "sales.customers@cm"}, "to": {"guid": "col-email", "type": "hive_column", "qualified_name": "sales.customers.email@cm"}}
    assert ok(executor, "search_relations")["approximate_total"] == 11
    columns = ok(executor, "get_related_entities", guid="tbl-payroll", relation="columns")
    assert names(columns) == ["salary"] and columns["relation"] == "columns"
    assert names(ok(executor, "get_related_entities", guid="db-sales", relation="tables")) == ["customers", "order_summary", "orders"]
    assert names(ok(executor, "get_related_entities", guid="tbl-customers", relation="meanings")) == ["Customer"]
    assert names(ok(executor, "get_related_entities", guid="term-customer", relation="assignedEntities")) == ["customers"]
    assert "not found" in error(executor, "get_related_entities", guid="nope", relation="columns")
    saved = ok(executor, "list_saved_searches")
    assert saved == {"saved_searches": [{"guid": "ss-1", "name": "PII tables", "owner": "admin", "kind": "basic", "type": "hive_table", "classification": "PII"}], "total": 1}
    assert ok(executor, "list_saved_searches", user="alice")["saved_searches"][0] == {"guid": "ss-2", "name": "my sales tables", "owner": "alice", "kind": "dsl", "query": "hive_table where owner = 'alice'"}
    assert ok(executor, "list_saved_searches", kind="dsl")["total"] == 0
    assert "basic or dsl" in error(executor, "list_saved_searches", kind="sql")
    assert ok(executor, "get_saved_search", name="PII tables")["classification"] == "PII"
    assert "not found" in error(executor, "get_saved_search", name="nope")
    assert names(ok(executor, "run_saved_search", name="PII tables")) == ["customers", "payroll"]
    assert names(ok(executor, "run_saved_search", name="my sales tables", user="alice")) == ["customers", "order_summary", "orders"]
    assert names(ok(executor, "run_saved_search_by_guid", guid="ss-1")) == ["customers", "payroll"]
    assert ok(executor, "suggest", prefix="ord") == {"prefix": "ord", "field": "name", "suggestions": ["order_summary", "orders"]}
    assert ok(executor, "suggest", prefix="sales.", field="qualifiedName")["suggestions"] == ["sales.customers.email@cm", "sales.customers@cm", "sales.etl.load_orders@cm", "sales.etl.summarise_orders@cm", "sales.order_summary@cm", "sales.orders@cm"]
    assert "Give the start" in error(executor, "suggest", prefix="")


@gateway
def test_a_forwarded_token_through_knox_gets_the_callers_own_view(executor):
    assert "credentials" in error(executor, "knox_search_basic", type_name="hive_table")  # no token forwarded
    alice, bob = jwt_for("alice"), jwt_for("bob")
    assert names(ok(executor, "knox_search_basic", caller="alice", token=alice, type_name="hive_table")) == ["customers", "order_summary", "orders"]
    assert names(ok(executor, "knox_search_basic", caller="bob", token=bob, type_name="hive_table")) == ["payroll"]
    assert names(ok(executor, "knox_search_basic", caller="carol", token=jwt_for("carol"), classification="PII")) == []
    assert ok(executor, "knox_quick_search", caller="alice", token=alice, query="PII")["by_type"] == {"hive_table": 1, "hive_column": 1}
    assert ok(executor, "knox_search_relations", caller="alice", token=alice)["count"] == 9  # only edges whose both ends she may see
    assert ok(executor, "knox_list_saved_searches", caller="alice", token=alice)["saved_searches"][0]["name"] == "my sales tables"
    assert "not authorized" in error(executor, "knox_list_saved_searches", caller="alice", token=alice, user="admin")
    assert names(ok(executor, "knox_run_saved_search", caller="alice", token=alice, name="my sales tables")) == ["customers", "order_summary", "orders"]
    assert "not authorized" in error(executor, "knox_run_saved_search_by_guid", caller="alice", token=alice, guid="ss-1")
    assert ok(executor, "knox_suggest", caller="bob", token=bob, prefix="s")["suggestions"] == ["salary", "shared"]


@gateway
def test_an_old_atlas_explains_itself(executor):
    assert names(ok(executor, "old_search_basic", type_name="hive_db")) == ["finance", "sales"]
    assert "does not offer quick search" in error(executor, "old_quick_search", query="sales")
    assert "does not offer relationship search" in error(executor, "old_search_relations")
    assert "does not offer related-entity search" in error(executor, "old_get_related_entities", guid="db-sales", relation="tables")
    assert "does not offer suggestions" in error(executor, "old_suggest", prefix="o")
    assert "check the prefix" in error(executor, "bad_prefix", type_name="hive_db")


@gateway
def test_the_builder_checks_an_atlas_connection_with_the_packs_own_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_ATLAS", "admin:admin-secret")
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Atlas", "base_url": MOCK, "protocol": "rest", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"}).json()
    tool = client.post("/api/tools", json={"name": "find_data", "description": "Search the catalogue.", "kind": "python", "pack": PACK, "function": "search_basic", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Atlas answered: 1 saved search(es) for this identity; offers quick search, relationship search and suggestions"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"classification": "PII", "type_name": "hive_table"}}}).json()
    assert result["success"], result
    assert sorted(e["name"] for e in result["result"]["structuredContent"]["entities"]) == ["customers", "payroll"]
