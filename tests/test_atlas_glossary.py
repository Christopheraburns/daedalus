"""The atlas_glossary seed pack against the Atlas fake: glossaries, categories, terms, relations and assigned entities,
through a service account and through a forwarded caller token (assigned entities follow the caller's view)."""
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
PACK = "atlas_glossary"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {
    "admin": {**BASE, "name": "Atlas", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"},
    "knox": {**BASE, "name": "Atlas via Knox", "auth_mode": "forward-token", "secret_ref": ""},
}
KNOX = {"prefix": "/gateway/cdp-proxy-api/atlas/api/atlas/v2"}


def glossary_tool(name, function, connection="admin", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Atlas", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_ATLAS"] = "admin:admin-secret"
    tools = [glossary_tool(f, f) for f in FUNCTIONS] + [glossary_tool(f"knox_{f}", f, "knox", KNOX) for f in ("get_term", "get_term_assigned_entities", "list_glossaries")]
    tools += [glossary_tool("tiny", "list_glossary_term_names", "admin", {"page_size": 2}), glossary_tool("bad_prefix", "list_glossaries", "admin", {"prefix": "/nowhere"})]
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


def names(items):
    return [i["name"] for i in items]


def test_the_seed_declares_thirteen_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 13
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_glossaries(executor):
    listing = ok(executor, "list_glossaries")
    assert names(listing["glossaries"]) == ["Business", "Regulatory"] and listing["count"] == 2 and not listing["truncated"]
    business = listing["glossaries"][0]
    assert business["guid"] == "gl-business" and business["language"] == "en" and names(business["terms"]) == ["Customer", "Order", "Invoice", "Bill", "Payroll"]
    assert business["categories"] == [{"guid": "cat-sales", "name": "Sales"}, {"guid": "cat-customer-mgmt", "name": "Customer Management", "parent_guid": "cat-sales"}, {"guid": "cat-finance", "name": "Finance"}]
    assert names(ok(executor, "list_glossaries", name_contains="reg")["glossaries"]) == ["Regulatory"]
    assert ok(executor, "get_glossary", guid="gl-regulatory")["terms"] == [{"guid": "term-pii", "name": "PII", "status": "active"}]
    assert "not found" in error(executor, "get_glossary", guid="gl-nope")
    detailed = ok(executor, "get_glossary_detailed", guid="gl-business")
    assert names(detailed["categories"]) == ["Sales", "Customer Management", "Finance"] and detailed["terms"][0]["short_description"] == "A person or organisation that buys from us"
    assert detailed["terms"][0]["assigned_entities"][0]["qualified_name"] == "sales.customers@cm"
    categories = ok(executor, "list_glossary_categories", glossary_guid="gl-business")
    assert names(categories["categories"]) == ["Sales", "Customer Management", "Finance"]
    sales = categories["categories"][0]
    assert sales["children"] == [{"guid": "cat-customer-mgmt", "name": "Customer Management", "parent_guid": "cat-sales"}] and names(sales["terms"]) == ["Order"] and "parent" not in sales
    assert categories["categories"][1]["parent"] == {"guid": "cat-sales", "name": "Sales"}
    assert ok(executor, "list_glossary_category_names", glossary_guid="gl-business")["categories"][2] == {"guid": "cat-finance", "name": "Finance"}
    terms = ok(executor, "list_glossary_terms", glossary_guid="gl-business")
    assert names(terms["terms"]) == ["Customer", "Order", "Invoice", "Bill", "Payroll"] and terms["terms"][2]["abbreviation"] == "INV" and terms["terms"][4]["classifications"] == ["Confidential"]
    assert ok(executor, "list_glossary_term_names", glossary_guid="gl-regulatory") == {"terms": [{"guid": "term-pii", "name": "PII", "status": "active"}], "count": 1, "offset": 0, "truncated": False}
    first = ok(executor, "tiny", glossary_guid="gl-business", limit=50)
    assert names(first["terms"]) == ["Customer", "Order"] and first["truncated"]
    rest = ok(executor, "tiny", glossary_guid="gl-business", offset=4)
    assert names(rest["terms"]) == ["Payroll"] and not rest["truncated"]
    assert "zero or positive" in error(executor, "list_glossary_terms", glossary_guid="gl-business", offset=-1)
    assert "check the prefix" in error(executor, "bad_prefix")


@gateway
def test_categories_and_terms(executor):
    category = ok(executor, "get_category", guid="cat-customer-mgmt")
    assert category == {"guid": "cat-customer-mgmt", "name": "Customer Management", "qualified_name": "Sales.Customer Management@Business", "glossary_guid": "gl-business", "short_description": "Knowing our customers", "parent": {"guid": "cat-sales", "name": "Sales"}, "terms": [{"guid": "term-customer", "name": "Customer", "status": "active"}]}
    assert ok(executor, "get_related_categories", guid="cat-sales") == {"guid": "cat-sales", "parent": [], "children": [{"guid": "cat-customer-mgmt", "name": "Customer Management", "parent_guid": "cat-sales"}]}
    assert ok(executor, "get_related_categories", guid="cat-customer-mgmt")["parent"] == [{"guid": "cat-sales", "name": "Sales"}]
    assert names(ok(executor, "list_category_terms", guid="cat-finance")["terms"]) == ["Invoice", "Bill", "Payroll"]
    assert "not found" in error(executor, "get_category", guid="cat-nope")
    customer = ok(executor, "get_term", guid="term-customer")
    assert customer["qualified_name"] == "Customer@Business" and customer["glossary_guid"] == "gl-business" and customer["examples"] == ["customers table", "customer_id column"]
    assert customer["categories"] == [{"guid": "cat-customer-mgmt", "name": "Customer Management", "parent_guid": "cat-sales"}]
    assert customer["assigned_entities"] == [{"guid": "tbl-customers", "type": "hive_table", "name": "customers", "qualified_name": "sales.customers@cm", "status": "active"}]
    assert customer["related"] == {"seeAlso": [{"guid": "term-order", "name": "Order", "status": "active"}]}
    invoice = ok(executor, "get_related_terms", guid="term-invoice")
    assert invoice == {"guid": "term-invoice", "related": {"seeAlso": [{"guid": "term-order", "name": "Order", "status": "active"}], "synonyms": [{"guid": "term-bill", "name": "Bill", "status": "active"}]}}
    assert ok(executor, "get_related_terms", guid="term-payroll") == {"guid": "term-payroll", "related": {}}
    pii = ok(executor, "get_term_assigned_entities", guid="term-pii")
    assert pii["term_guid"] == "term-pii" and names(pii["entities"]) == ["customers", "email", "payroll", "salary"] and pii["count"] == 4
    assert ok(executor, "get_term_assigned_entities", guid="term-order") == {"term_guid": "term-order", "entities": [], "count": 0, "offset": 0, "truncated": False}
    assert "not found" in error(executor, "get_term", guid="term-nope")


@gateway
def test_a_forwarded_token_sees_the_glossary_but_only_the_callers_assets(executor):
    alice, bob = jwt_for("alice"), jwt_for("bob")
    assert "credentials" in error(executor, "knox_list_glossaries")
    assert names(ok(executor, "knox_list_glossaries", caller="alice", token=alice)["glossaries"]) == ["Business", "Regulatory"]
    assert names(ok(executor, "knox_get_term_assigned_entities", caller="alice", token=alice, guid="term-pii")["entities"]) == ["customers", "email"]
    assert names(ok(executor, "knox_get_term_assigned_entities", caller="bob", token=bob, guid="term-pii")["entities"]) == ["payroll", "salary"]
    payroll = ok(executor, "knox_get_term", caller="alice", token=alice, guid="term-payroll")
    assert payroll["short_description"] == "Salaries paid to staff" and "assigned_entities" not in payroll  # the term is public, the table is not hers


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_ATLAS", "admin:admin-secret")
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Atlas", "base_url": MOCK, "protocol": "rest", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"}).json()
    tool = client.post("/api/tools", json={"name": "define_term", "description": "What a business term means.", "kind": "python", "pack": PACK, "function": "get_term", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Atlas answered: 2 glossar(ies): Business, Regulatory"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"guid": "term-customer"}}}).json()
    assert result["success"], result
    assert result["result"]["structuredContent"]["name"] == "Customer"
