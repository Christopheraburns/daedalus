"""The atlas_types seed pack against the Atlas fake: type names, full definitions, one type of any category, an entity
type with its inherited attributes, a classification with its applicability; through a service account, a forwarded
caller token and an Atlas without business metadata."""
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
PACK = "atlas_types"
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


def types_tool(name, function, connection="admin", config=None):
    spec = ToolSpec(name=name, description=f"{function} on Atlas", kind="python", pack=PACK, function=function, connection_id=connection, effect="read", config=config or {}).model_dump()
    return {"id": name, "revision": 1, "spec": spec}


def jwt_for(subject):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


@pytest.fixture(scope="module")
def executor(tmp_path_factory):
    os.environ["FACTORY_SECRET_ATLAS"] = "admin:admin-secret"
    tools = [types_tool(f, f) for f in FUNCTIONS] + [types_tool(f"knox_{f}", f, "knox", KNOX) for f in ("list_type_names", "get_entity_type")]
    tools += [types_tool(f"old_{f}", f, "admin", OLD) for f in ("list_type_names", "list_type_definitions", "get_type_definition")]
    tools += [types_tool("tiny", "list_type_names", "admin", {"page_size": 4}), types_tool("bad_prefix", "list_type_names", "admin", {"prefix": "/nowhere"})]
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


def test_the_seed_declares_five_read_tools():
    assert INFO["error"] is None and INFO["protocol"] == "rest" and len(INFO["tools"]) == 5
    assert all(t["effect"] == "read" for t in INFO["tools"]) and INFO["probe"]["function"] == "probe"


@gateway
def test_type_names_and_definitions(executor):
    listing = ok(executor, "list_type_names")
    assert listing["count"] == 19 and not listing["truncated"]
    assert listing["types"][0] == {"name": "Governance", "category": "business_metadata", "guid": "type-governance"}
    assert names(ok(executor, "list_type_names", category="classification")["types"]) == ["Confidential", "Curated", "PII"]
    assert names(ok(executor, "list_type_names", service_type="hdfs")["types"]) == ["hdfs_path"]
    assert names(ok(executor, "list_type_names", name_contains="HIVE_T")["types"]) == ["hive_table", "hive_table_columns", "hive_table_db"]
    assert "one of" in error(executor, "list_type_names", category="tag")
    first = ok(executor, "tiny", limit=50)
    assert names(first["types"]) == ["Governance", "Confidential", "Curated", "PII"] and first["truncated"]
    rest = ok(executor, "tiny", offset=16)
    assert names(rest["types"]) == ["hive_table_db", "process_dataset_outputs", "hive_order"] and not rest["truncated"]
    assert "zero or positive" in error(executor, "list_type_names", offset=-1)
    assert "check the prefix" in error(executor, "bad_prefix")

    everything = ok(executor, "list_type_definitions", limit=100)
    assert everything["total"] == 19 and everything["by_category"] == {"entity": 9, "classification": 3, "enum": 1, "struct": 1, "relationship": 4, "business_metadata": 1}
    assert everything["count"] == 19 and names(everything["types"])[:3] == ["Referenceable", "Asset", "DataSet"]
    datasets = ok(executor, "list_type_definitions", super_type="DataSet")
    assert names(datasets["types"]) == ["hive_table", "hive_column", "hdfs_path"] and datasets["by_category"] == {"entity": 3}
    hive = ok(executor, "list_type_definitions", service_type="hive", category="relationship")
    assert names(hive["types"]) == ["hive_table_db", "hive_table_columns"] and hive["types"][1]["ends"] == [{"type": "hive_table", "name": "columns", "cardinality": "SET", "container": True}, {"type": "hive_column", "name": "table", "cardinality": "SINGLE"}]
    paged = ok(executor, "list_type_definitions", limit=2, offset=8)
    assert names(paged["types"]) == ["hdfs_path", "PII"] and paged["truncated"] and paged["total"] == 19

    enum = ok(executor, "get_type_definition", name="hive_principal_type")
    assert enum == {"name": "hive_principal_type", "category": "enum", "guid": "type-hive-principal-type", "description": "Who owns a Hive object", "service_type": "hive", "version": "1.0",
        "values": [{"value": "USER", "ordinal": 1}, {"value": "ROLE", "ordinal": 2}, {"value": "GROUP", "ordinal": 3}], "default": "USER"}
    struct = ok(executor, "get_type_definition", name="hive_order")
    assert struct["category"] == "struct" and struct["attributes"] == [{"name": "col", "type": "string", "optional": False}, {"name": "order", "type": "int", "optional": False}]
    governance = ok(executor, "get_type_definition", name="Governance")
    assert governance["category"] == "business_metadata" and governance["attributes"][0] == {"name": "steward", "type": "string", "optional": True, "applicable_entity_types": '["hive_table","hdfs_path"]', "max_length": "50"}
    relationship = ok(executor, "get_type_definition", name="dataset_process_inputs")
    assert relationship["relationship_category"] == "AGGREGATION" and relationship["propagate_tags"] == "NONE" and names(relationship["ends"]) == ["inputs", "inputToProcesses"]
    assert "was invalid" in error(executor, "get_type_definition", name="hive_view")
    assert "without slashes" in error(executor, "get_type_definition", name="a/b")


@gateway
def test_entity_and_classification_types(executor):
    table = ok(executor, "get_entity_type", name="hive_table")
    assert table["super_types"] == ["DataSet"] and table["all_super_types"] == ["Asset", "DataSet", "Referenceable"] and "sub_types" not in table
    own = [a for a in table["attributes"] if "inherited_from" not in a]
    assert names(own) == ["createTime", "lastAccessTime", "comment", "retention", "tableType", "temporary", "parameters"]
    assert {a["name"]: a["inherited_from"] for a in table["attributes"] if "inherited_from" in a} == {"name": "Asset", "description": "Asset", "owner": "Asset", "userDescription": "Asset", "qualifiedName": "Referenceable"}
    assert next(a for a in table["attributes"] if a["name"] == "qualifiedName") == {"name": "qualifiedName", "type": "string", "optional": False, "unique": True, "indexed": True, "inherited_from": "Referenceable"}
    assert next(a for a in table["attributes"] if a["name"] == "temporary")["default"] == "false"
    assert table["relationship_attributes"] == [{"name": "db", "type": "hive_db", "relationship": "hive_table_db", "optional": False}, {"name": "columns", "type": "array<hive_column>", "relationship": "hive_table_columns", "optional": True, "cardinality": "SET"}]
    assert table["dsl_hint"] == "hive_table where qualifiedName like '*...*' select name, qualifiedName, owner"
    bare = ok(executor, "get_entity_type", name="hive_table", include_inherited=False)
    assert names(bare["attributes"]) == names(own) and "all_super_types" not in bare and bare["dsl_hint"] == "hive_table where comment like '*...*' select comment"
    asset = ok(executor, "get_entity_type", name="Asset")
    assert asset["sub_types"] == ["DataSet", "Process", "hive_db"] and asset["all_super_types"] == ["Referenceable"] and names(asset["attributes"])[-1] == "qualifiedName"
    process = ok(executor, "get_entity_type", name="Process")
    assert next(a for a in process["attributes"] if a["name"] == "inputs") == {"name": "inputs", "type": "array<DataSet>", "optional": True, "cardinality": "SET"}
    assert "doesn't match ENTITY" in error(executor, "get_entity_type", name="PII")
    assert "was invalid" in error(executor, "get_entity_type", name="kafka_topic")

    pii = ok(executor, "get_classification_type", name="PII")
    assert pii == {"name": "PII", "category": "classification", "guid": "type-pii", "description": "Personally identifiable information", "version": "1.0", "attributes": [{"name": "type", "type": "string", "optional": True, "description": "What kind of personal data"}]}
    confidential = ok(executor, "get_classification_type", name="Confidential")
    assert confidential["entity_types"] == ["hive_table", "hdfs_path"] and confidential["attributes"][0]["default"] == "medium"
    assert "attributes" not in ok(executor, "get_classification_type", name="Curated")
    assert "doesn't match CLASSIFICATION" in error(executor, "get_classification_type", name="hive_table")


@gateway
def test_a_forwarded_token_and_an_older_atlas(executor):
    assert "credentials" in error(executor, "knox_list_type_names")
    assert ok(executor, "knox_list_type_names", caller="bob", token=jwt_for("bob"))["count"] == 19
    assert ok(executor, "knox_get_entity_type", caller="alice", token=jwt_for("alice"), name="hdfs_path")["all_super_types"] == ["Asset", "DataSet", "Referenceable"]
    old = ok(executor, "old_list_type_names")
    assert old["count"] == 18 and "Governance" not in names(old["types"])
    assert "business_metadata" not in ok(executor, "old_list_type_definitions", limit=100)["by_category"]
    assert "was invalid" in error(executor, "old_get_type_definition", name="Governance")


@gateway
def test_the_builder_checks_the_connection_with_the_packs_probe(registry, monkeypatch):
    client, _, _ = registry
    monkeypatch.setenv("FACTORY_SECRET_ATLAS", "admin:admin-secret")
    assert client.put(f"/api/packs/{PACK}/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "Atlas", "base_url": MOCK, "protocol": "rest", "auth_mode": "basic", "secret_ref": "FACTORY_SECRET_ATLAS"}).json()
    tool = client.post("/api/tools", json={"name": "describe_type", "description": "What an entity type carries.", "kind": "python", "pack": PACK, "function": "get_entity_type", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    connection = next(c for c in client.get("/api/workspace").json()["connections"] if c["id"] == connection["id"])
    checked = client.post(f"/api/connections/{connection['id']}/check", headers={"If-Match": str(connection["revision"])}).json()
    assert checked["probe_summary"]["success"] and checked["probe_summary"]["pack"] == PACK, checked
    assert checked["probe_summary"]["message"] == "Atlas answered: 19 types (1 business_metadata, 3 classification, 9 entity, 1 enum, 4 relationship, 1 struct)"
    result = client.post(f"/api/tools/{tool.json()['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"name": "hive_column"}}}).json()
    assert result["success"], result
    assert result["result"]["structuredContent"]["all_super_types"] == ["Asset", "DataSet", "Referenceable"]
