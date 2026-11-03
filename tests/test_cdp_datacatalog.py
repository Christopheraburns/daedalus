"""The cdp_datacatalog seed pack against the control plane fake: Data Shares, fine-grained access status and profiler tag
suggestions, signed with a CDP API key."""
import base64
import os

import httpx
import pytest

from factory import packs, packstore
from factory.compiler import compile_bundle
from factory.contracts import ToolSpec
from factory.gateway import KEY_HEADER, USER_HEADER, start_executor, stop_process

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
MOCK = "http://mock-api:8080"
PACK = "cdp_datacatalog"
SOURCE = packs.seed_source(PACK)
INFO = packstore.described(PACK, "seed", SOURCE, packs.inspect_source(PACK, SOURCE))
FUNCTIONS = [t["function"] for t in INFO["tools"]]
SECRET = "e6a3f9c1-daedalus-test-key:" + base64.b64encode(bytes(range(32))).decode()
DATALAKE = "crn:cdp:datalake:us-west-1:tenant:datalake:prod-dl"
ENV = "crn:cdp:environments:us-west-1:tenant:environment:prod"
SCOPE = {"datalake_crn": DATALAKE, "environment_crn": ENV}
BASE = {"base_url": MOCK, "protocol": "rest", "proxy_principal": "", "keytab_ref": "", "doas_parameter": "doAs"}
CONNECTIONS = {"cdp": {**BASE, "name": "CDP", "auth_mode": "cdp-apikey", "secret_ref": "FACTORY_SECRET_CDP"}, "anonymous": {**BASE, "name": "CDP unsigned", "auth_mode": "none", "secret_ref": ""}}


def dc_tool(name, function, connection="cdp", config=None):
    spec = ToolSpec(name=name, description=f"{function} on CDP", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=SCOPE if config is None else config).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_CDP"] = SECRET
    tools = [dc_tool(f, f) for f in FUNCTIONS]
    tools += [dc_tool("no_scope", "list_data_shares", config={}), dc_tool("lake_only", "list_data_shares", config={"datalake_crn": DATALAKE}), dc_tool("unsigned", "list_data_shares", "anonymous"),
        dc_tool("tiny", "list_data_shares", config={**SCOPE, "page_size": 2}), dc_tool("bad_prefix", "list_data_shares", config={**SCOPE, "prefix": "/nowhere"})]
    bundle = compile_bundle(tools, CONNECTIONS, [MOCK], packstore.lookup({PACK: INFO}), {PACK: SOURCE})
    running = start_executor(bundle, tmp_path_factory.mktemp("executor"))
    try:
        yield running
    finally:
        stop_process(running.process)
        os.environ.pop("FACTORY_SECRET_CDP", None)


def call(executor, tool, **arguments):
    response = httpx.post(f"http://127.0.0.1:{executor.port}/tools/{tool}", headers={KEY_HEADER: executor.key, USER_HEADER: "alice"}, json=arguments, timeout=30)
    return response.status_code, response.json()


def ok(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status == 200, payload
    return payload


def error(executor, tool, **arguments):
    status, payload = call(executor, tool, **arguments)
    assert status >= 400 and "error" in payload, payload
    return payload["error"]


def test_the_seed_declares_four_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 4
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_data_shares(executor):
    shares = ok(executor, "list_data_shares")
    assert [s["name"] for s in shares["shares"]] == ["Customer 360", "Supplier spend", "Marketing campaigns"] and shares["count"] == 3 and "next_page_token" not in shares
    assert shares["shares"][0] == {"id": "ds-001", "name": "Customer 360", "shared": True, "created": "2026-03-03T10:00:00Z", "created_by": "alice", "keywords": ["customer", "crm"], "expires": "2027-03-03T00:00:00Z"}
    assert shares["shares"][2] == {"id": "ds-003", "name": "Marketing campaigns", "shared": True, "created": "2026-09-15T12:00:00Z", "created_by": "alice", "keywords": ["marketing"]}
    assert [s["id"] for s in ok(executor, "list_data_shares", name="spend")["shares"]] == ["ds-002"]
    first = ok(executor, "tiny", limit=50)
    assert [s["id"] for s in first["shares"]] == ["ds-001", "ds-002"] and first["next_page_token"] == "2"
    assert [s["id"] for s in ok(executor, "tiny", page_token="2")["shares"]] == ["ds-003"]
    assert ok(executor, "list_data_shares", name="nothing") == {"count": 0, "shares": []}
    detail = ok(executor, "get_data_share", data_share_id="ds-001")
    assert detail["summary"] == "Customer master with masked contact details" and detail["terms_of_use"] == "Internal partner use only" and detail["tags"] == ["PII"] and detail["updated"] == "2026-10-01T09:30:00Z"
    assert detail["assets"] == [{"resource_id": "res-1", "guid": "tbl-customers", "database": "sales", "table": "customers", "columns": ["customer_id", "name", "email"], "created": "2026-03-03T10:00:00Z", "created_by": "alice", "updated": "2026-03-03T10:00:00Z", "updated_by": "alice"}]
    assert detail["external_users"] == [{"id": 7, "username": "acme-analyst", "company": "Acme", "client_id": "client-acme", "permissions": ["READ"], "shared_on": "2026-03-04T00:00:00Z", "valid_till": "2027-03-03T00:00:00Z"}]
    supplier = ok(executor, "get_data_share", data_share_id="ds-002")
    assert supplier["shared"] is False and supplier["external_users"] == [] and "terms_of_use" not in supplier and supplier["assets"][0]["table"] == "suppliers"
    assert "not found" in error(executor, "get_data_share", data_share_id="ds-999")
    assert "datalake_crn or set it" in error(executor, "no_scope")
    assert "environment_crn or set it" in error(executor, "lake_only")
    assert "must be a CRN" in error(executor, "list_data_shares", datalake_crn="prod-dl")
    assert "was not found" in error(executor, "list_data_shares", datalake_crn="crn:cdp:datalake:us-west-1:tenant:datalake:gone")
    assert "rejected the API key" in error(executor, "unsigned")
    assert "check the base URL" in error(executor, "bad_prefix")


@gateway
def test_fgac_status_and_suggested_tags(executor):
    status = ok(executor, "get_fgac_status", tables="sales.customers, finance.suppliers,hr.people")
    assert status["count"] == 3 and status["protected"] == 1
    assert status["assets"][0] == {"database": "sales", "table": "customers", "fine_grained_access": True, "status": {"fgacEnabled": True, "policies": ["pii-mask-email", "row-filter-region"]}}
    assert status["assets"][1]["fine_grained_access"] is False and status["assets"][2]["status"]["message"] == "Table not found in Ranger"
    assert "database.table" in error(executor, "get_fgac_status", tables="customers")
    assert "at least one" in error(executor, "get_fgac_status", tables=" , ")
    tags = ok(executor, "get_suggested_tags")
    assert tags["count"] == 3 and tags["tags"] == ["dp_email", "dp_iban", "dp_name"] and tags["suggestions"][0] == {"qualified_name": "sales.customers@cm", "tags": ["dp_name", "dp_email"]}
    assert [s["qualified_name"] for s in ok(executor, "get_suggested_tags", table="sales.customers@cm")["suggestions"]] == ["sales.customers@cm", "sales.customers.email@cm"]
    assert ok(executor, "get_suggested_tags", column="finance.suppliers.iban@cm")["suggestions"] == [{"qualified_name": "finance.suppliers.iban@cm", "tags": ["dp_iban"]}]
    assert [s["qualified_name"] for s in ok(executor, "get_suggested_tags", profiled_since="2026-10-01")["suggestions"]] == ["sales.customers@cm", "sales.customers.email@cm"]
    assert "ISO date" in error(executor, "get_suggested_tags", profiled_since="October")
    assert ok(executor, "get_suggested_tags", table="hr.people@cm") == {"suggestions": [], "count": 0, "tags": []}


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_CDP", SECRET)
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "CDP", "base_url": MOCK, "protocol": "rest", "auth_mode": "cdp-apikey", "secret_ref": "FACTORY_SECRET_CDP"}).json()
    tool = client.post("/api/tools", json={"name": "shared_data", "description": "What the Data Lake shares.", "kind": "python", "pack": PACK, "function": "list_data_shares", "connection_id": connection["id"], "config": SCOPE})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"].startswith("CDP accepted the API key for the Data Catalog service")
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"name": "customer"}}}).json()
    assert result["success"], result
    assert [s["id"] for s in result["result"]["structuredContent"]["shares"]] == ["ds-001"]
    monkeypatch.setenv("FACTORY_SECRET_CDP", "e6a3f9c1-daedalus-test-key:" + base64.b64encode(bytes(32)).decode())
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert not checked["probe_summary"]["success"] and "rejected the API key" in checked["probe_summary"]["message"], checked
