import os

MOCK = "http://mock-api:8080"
PACK = '''"""Exported project pack."""
from factory.packs import ToolContext, pack_tool


@pack_tool(effect="read")
def shout(ctx: ToolContext, text: str) -> dict:
    """Upper-case the text."""
    return {"text": text.upper()}
'''


def build_source(client, monkeypatch, tmp_path):
    monkeypatch.setenv("FACTORY_PACKS_DIR", str(tmp_path / "packs"))
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture APIs"}).status_code == 201
    assert client.put("/api/packs/loud", json={"source": PACK}).status_code == 200
    rest = client.post("/api/connections", json={"name": "Inventory", "base_url": MOCK, "auth_mode": "static", "secret_ref": "FACTORY_SECRET_INVENTORY"}).json()
    upstream = client.post("/api/connections", json={"name": "Upstream", "base_url": f"{MOCK}/upstream/mcp", "protocol": "mcp"}).json()
    assert client.post(f"/api/connections/{upstream['id']}/check", headers={"If-Match": "1"}).json()["discovered"]
    tools = [
        client.post("/api/tools", json={"name": "get_item", "description": "Look up an item.", "connection_id": rest["id"], "path": "/inventory/items/{item_id}",
            "parameters": [{"name": "item_id", "location": "path", "required": True, "type": "string"}]}).json(),
        client.post("/api/tools", json={"name": "echo", "description": "Echo.", "kind": "python", "pack": "demo", "function": "echo"}).json(),
        client.post("/api/tools", json={"name": "shout", "description": "Shout.", "kind": "python", "pack": "loud", "function": "shout"}).json(),
        client.post("/api/tools", json={"name": "add", "description": "Add numbers.", "kind": "mcp", "connection_id": upstream["id"], "upstream_tool": "add"}).json(),
    ]
    assert all("id" in t for t in tools), tools
    revision = client.get("/api/workspace").json()["layout"]["revision"]
    assert client.put("/api/layout", headers={"If-Match": str(revision)}, json={"positions": {tools[0]["id"]: {"x": 100, "y": 50}, rest["id"]: {"x": 400, "y": 60}}}).status_code == 200
    return rest, upstream, tools


def comparable(document):
    return {k: v for k, v in document.items() if k not in {"exported_at", "source", "server"}}


def test_export_and_import_round_trip(registry, monkeypatch, tmp_path):
    client, _, _ = registry
    rest, upstream, tools = build_source(client, monkeypatch, tmp_path)
    viewer = {"Authorization": "Bearer " + os.environ["FACTORY_VIEWER_TOKEN"]}
    exported = client.get("/api/export", headers=viewer)
    assert exported.status_code == 200 and 'filename="my-mcp-server.daedalus.json"' in exported.headers["content-disposition"]
    document = exported.json()
    assert document["format"] == "daedalus-server/v1"
    assert [c["ref"] for c in document["connections"]] == ["c1", "c2"] and sorted(t["spec"]["name"] for t in document["tools"]) == ["add", "echo", "get_item", "shout"]
    assert document["required_secrets"] == ["FACTORY_SECRET_INVENTORY"]
    assert set(document["packs"]) == {"loud"} and "def shout" in document["packs"]["loud"]
    text = exported.text
    assert rest["id"] not in text and tools[0]["id"] not in text  # no record IDs leak into the file
    assert any(t["spec"]["kind"] == "mcp" and t["spec"]["input_schema"]["required"] == ["a", "b"] for t in document["tools"])
    assert any(c["discovered"] for c in document["connections"])
    # Viewers and authors cannot import: it creates connections, origins and code.
    author = {"Authorization": "Bearer " + os.environ["FACTORY_AUTHOR_TOKEN"]}
    assert client.post("/api/servers/import", headers=author, json={"document": document}).status_code == 403
    imported = client.post("/api/servers/import", json={"document": document, "name": "Imported copy"})
    assert imported.status_code == 201, imported.text
    result = imported.json()
    assert result["tools"] == 4 and result["connections"] == 2 and result["packs_written"] == []  # same code already here
    assert result["required_secrets"] == ["FACTORY_SECRET_INVENTORY"] and result["missing_secrets"] == ["FACTORY_SECRET_INVENTORY"]
    copy_id = result["server"]["id"]
    workspace = client.get(f"/api/workspace?server_id={copy_id}").json()
    assert workspace["server"]["name"] == "Imported copy"
    assert sorted(t["name"] for t in workspace["tools"]) == ["add", "echo", "get_item", "shout"]
    assert not any(t["tested"] for t in workspace["tools"])  # test evidence never travels
    assert {c["id"] for c in workspace["connections"]}.isdisjoint({rest["id"], upstream["id"]})
    assert MOCK in workspace["allowed_api_origins"]
    moved = next(t for t in workspace["tools"] if t["name"] == "get_item")
    assert workspace["layout"]["positions"][moved["id"]] == {"x": 100, "y": 50}
    assert next(c for c in workspace["connections"] if c["protocol"] == "mcp")["discovered"]
    again = client.get(f"/api/export?server_id={copy_id}").json()
    assert comparable(again) == comparable(document)
    # The imported tools work: an MCP tool runs against the same upstream.
    add = next(t for t in workspace["tools"] if t["name"] == "add")
    outcome = client.post(f"/api/tools/{add['id']}/test?server_id={copy_id}", headers={"If-Match": "1"}, json={"arguments": {"body": {"a": 2, "b": 2}}}).json()
    assert outcome["success"], outcome


def test_import_protects_existing_packs_and_rejects_bad_files(registry, monkeypatch, tmp_path):
    client, _, _ = registry
    build_source(client, monkeypatch, tmp_path)
    document = client.get("/api/export").json()
    changed = {**document, "packs": {"loud": PACK.replace("text.upper()", "text.upper() + '!'")}}
    conflict = client.post("/api/servers/import", json={"document": changed})
    assert conflict.status_code == 409 and "loud" in conflict.json()["detail"]
    replaced = client.post("/api/servers/import", json={"document": changed, "replace_packs": True})
    assert replaced.status_code == 201 and replaced.json()["packs_written"] == ["loud"]
    assert "+ '!'" in client.get("/api/packs/loud").json()["source"]
    assert client.post("/api/servers/import", json={"document": {"format": "something-else"}}).status_code == 422
    broken = {**document, "tools": [{**document["tools"][0], "spec": {**document["tools"][0]["spec"], "connection_id": "c9"}}]}
    assert "refers to a connection" in client.post("/api/servers/import", json={"document": broken}).json()["detail"]
    builtin = {**document, "packs": {"demo": PACK}}
    assert "built-in pack" in client.post("/api/servers/import", json={"document": builtin}).json()["detail"]
    servers_before = len(client.get("/api/servers").json())
    unknown = {**document, "packs": {}, "tools": [{"ref": "t1", "spec": {**next(x for x in document["tools"] if x["spec"]["name"] == "shout")["spec"], "pack": "nowhere"}}], "layout": {}}
    assert client.post("/api/servers/import", json={"document": unknown}).status_code == 422
    assert len(client.get("/api/servers").json()) == servers_before  # a failed import leaves nothing behind
