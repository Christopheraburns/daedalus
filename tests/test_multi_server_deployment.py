from conftest import add_tool, spec
from factory.compiler import compile_bundle, digest, fingerprint
from factory.db import Connection, Release, Server, Tool, new_id
from factory.settings import SERVER_ID


def test_server_workspaces_are_isolated_and_deployment_intent_is_recorded(registry):
    client, _, _ = registry
    created = client.post("/api/servers", json={"name": "Support MCP"})
    assert created.status_code == 201, created.text
    server_id = created.json()["id"]
    support = client.get("/api/workspace", params={"server_id": server_id}).json()
    assert support["server"]["name"] == "Support MCP"
    assert support["connections"] == [] and support["deployment"]["status"] == "not_deployed"
    tool, _ = add_tool(client, name="inventory_default")
    assert client.get("/api/workspace", params={"server_id": server_id}).json()["tools"] == []
    connection = client.post("/api/connections", params={"server_id": server_id}, json={"name": "Support", "base_url": "http://mock-api:8080"}).json()
    other = client.post("/api/tools", params={"server_id": server_id}, json={"name": "support_ticket", "description": "Get a support ticket.", "connection_id": connection["id"], "method": "GET", "path": "/tickets/{ticket_id}", "effect": "read", "parameters": [{"name": "ticket_id", "location": "path", "type": "string", "required": True, "description": "Ticket"}], "body_schema": None})
    assert other.status_code == 201
    assert client.patch(f"/api/tools/{tool['id']}", params={"server_id": server_id}, headers={"If-Match": "1"}, json={**spec(tool), "description": "No"}).status_code == 404


def test_manual_deployment_requires_active_release_and_records_a_manifest_intent(registry):
    client, sessions, settings = registry
    workspace = client.get("/api/workspace").json()
    assert client.post("/api/deployments", json={"revision": workspace["server"]["revision"]}).status_code == 422
    tool, connection = add_tool(client, name="deployable_inventory")
    with sessions.begin() as session:
        server = session.get(Server, SERVER_ID)
        db_tool = session.get(Tool, tool["id"])
        db_connection = session.get(Connection, connection["id"])
        bundle = compile_bundle([{"id": db_tool.id, "revision": db_tool.revision, "spec": db_tool.spec, "fingerprint": fingerprint(db_tool.spec, db_connection.spec)}], {db_connection.id: db_connection.spec}, settings.allowed_origins)
        release = Release(id=new_id(), server_id=SERVER_ID, bundle=bundle, checksum=digest(bundle), status="active", created_by="test")
        session.add(release); server.active_release_id = release.id; server.revision += 1
    workspace = client.get("/api/workspace").json()
    deployed = client.post("/api/deployments", json={"revision": workspace["server"]["revision"]})
    assert deployed.status_code == 200, deployed.text
    assert deployed.json()["status"] == "ready_to_deploy"
    assert deployed.json()["application_name"].startswith("my-mcp-server-")
    stopped = client.post("/api/deployments/stop", json={"revision": workspace["server"]["revision"]})
    assert stopped.status_code == 200 and stopped.json()["status"] == "stopped"
