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
    # Manual mode creates nothing, says so, and hands over what to enter in Workbench.
    assert deployed.json()["message"].startswith("Manual mode: no application was created")
    manifest = deployed.json()["metrics"]["manifest"]
    assert manifest["entrypoint"] == "mcp_server_app.py" and manifest["environment"]["FACTORY_SERVER_ID"] and manifest["environment"]["FACTORY_DEPLOYED_RELEASE_ID"]
    assert deployed.json()["application_name"].startswith("my-mcp-server-")
    stopped = client.post("/api/deployments/stop", json={"revision": workspace["server"]["revision"]})
    assert stopped.status_code == 200 and stopped.json()["status"] == "stopped"


def test_the_server_listing_names_servers_and_shows_who_serves_them(registry):
    import os
    from sqlalchemy import text
    from factory.db import database
    client, _, settings = registry
    other = client.post("/api/servers", json={"name": "Customer support MCP"}).json()
    client.post("/api/tools", json={"name": "echo", "description": "Echo.", "kind": "python", "pack": "demo", "function": "echo"})
    listing = {s["name"]: s for s in client.get("/api/servers").json()}
    assert set(listing) == {"My MCP server", "Customer support MCP"}
    assert listing["My MCP server"]["tools"] == 1 and listing["Customer support MCP"]["tools"] == 0
    assert listing["My MCP server"]["owner"] is None and listing["My MCP server"]["runtime"]["online"] is False
    engine, _ = database(os.environ["DATABASE_URL"], "daedalus-server 85d30f87 on pod-a")
    with engine.connect() as owner:
        owner.scalar(text("SELECT pg_try_advisory_lock(hashtext(current_schema()), hashtext(:s))"), {"s": settings.server_id})
        held = {s["name"]: s for s in client.get("/api/servers").json()}
        assert held["My MCP server"]["owner"]["process"] == "daedalus-server 85d30f87 on pod-a" and held["My MCP server"]["owner"]["since"]
        assert held["Customer support MCP"]["owner"] is None
    engine.dispose()
    assert other["id"] in {s["id"] for s in listing.values()}


def test_deleting_a_server_removes_everything_and_refuses_while_it_is_served(registry):
    import os
    from sqlalchemy import select, text
    from factory.db import Audit, Connection, Tool, database
    client, sessions, settings = registry
    viewer = {"Authorization": "Bearer " + os.environ["FACTORY_VIEWER_TOKEN"]}
    author = {"Authorization": "Bearer " + os.environ["FACTORY_AUTHOR_TOKEN"]}
    assert client.delete(f"/api/servers/{settings.server_id}", headers={"If-Match": "1"}).status_code == 409  # default workspace
    doomed = client.post("/api/servers", json={"name": "Doomed"}).json()
    connection = client.post(f"/api/connections?server_id={doomed['id']}", json={"name": "API", "base_url": "http://mock-api:8080"}).json()
    client.post(f"/api/tools?server_id={doomed['id']}", json={"name": "echo", "description": "Echo.", "kind": "python", "pack": "demo", "function": "echo"})
    revision = next(s for s in client.get("/api/servers").json() if s["id"] == doomed["id"])["revision"]
    assert client.delete(f"/api/servers/{doomed['id']}", headers={**viewer, "If-Match": str(revision)}).status_code == 403
    assert client.delete(f"/api/servers/{doomed['id']}", headers={**author, "If-Match": str(revision)}).status_code == 403
    assert client.delete(f"/api/servers/{doomed['id']}", headers={"If-Match": "999"}).status_code == 409
    # A process serving it blocks the deletion and is named.
    engine, _ = database(os.environ["DATABASE_URL"], "daedalus-server doomed on pod-z")
    with engine.connect() as owner:
        owner.scalar(text("SELECT pg_try_advisory_lock(hashtext(current_schema()), hashtext(:s))"), {"s": doomed["id"]})
        blocked = client.delete(f"/api/servers/{doomed['id']}", headers={"If-Match": str(revision)})
        assert blocked.status_code == 409 and "pod-z" in blocked.json()["detail"]
    engine.dispose()
    assert client.delete(f"/api/servers/{doomed['id']}", headers={"If-Match": str(revision)}).status_code == 204
    assert doomed["id"] not in {s["id"] for s in client.get("/api/servers").json()}
    with sessions() as session:
        assert not list(session.scalars(select(Tool).where(Tool.server_id == doomed["id"])))
        assert session.get(Connection, connection["id"]) is None
        event = session.scalar(select(Audit).where(Audit.action == "server.delete"))
        assert event.details["name"] == "Doomed" and event.details["tools"] == 1 and event.details["connections"] == 1
