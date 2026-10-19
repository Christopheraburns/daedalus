import json

import httpx
import pytest

from factory import deployment
from factory.db import Release, Server
from factory.settings import SERVER_ID


class FakeWorkbench:
    """Enough of the Cloudera AI API v2 application endpoints to drive the provider."""

    def __init__(self):
        self.applications = {}
        self.calls = []
        self.next_id = 1

    def handler(self, request: httpx.Request):
        self.calls.append((request.method, request.url.path, request.headers.get("authorization")))
        if request.headers.get("authorization") != "Bearer api-key-123":
            return httpx.Response(401, json={"message": "unauthorized"})
        if request.url.path == "/api/v2/runtimes":
            wanted = json.loads(request.url.params["search_filter"])["edition"]
            catalog = [{"image_identifier": "registry/other:1", "edition": "Standard", "full_version": "2026.08.1"},
                {"image_identifier": "registry/mcp-factory-runtime:0.1.1", "edition": "MCP Factory Development", "full_version": "0.1.1", "editor": "PBJ Workbench", "kernel": "Python 3.12"},
                {"image_identifier": "registry/mcp-factory-runtime:0.1.2", "edition": "MCP Factory Development", "full_version": "0.1.2", "editor": "PBJ Workbench", "kernel": "Python 3.12"}]
            return httpx.Response(200, json={"runtimes": [r for r in catalog if r["edition"] == wanted]})
        parts = request.url.path.split("/applications")
        assert parts[0] == "/api/v2/projects/proj-1"
        tail = parts[1]
        if request.method == "GET" and tail == "":
            return httpx.Response(200, json={"applications": list(self.applications.values())})
        if request.method == "POST" and tail == "":
            body = json.loads(request.content)
            assert body["subdomain"] == body["name"] and body["script"] == "mcp_server_app.py" and body["runtime_identifier"] == "registry/mcp-factory-runtime:0.1.2"
            assert body["environment"]["FACTORY_SERVER_ID"] == SERVER_ID and body["cpu"] == 1 and body["memory"] == 2 and body["bypass_authentication"] is True
            application = {"id": f"app-{self.next_id}", "status": "APPLICATION_STARTING", "creator": {"username": "cburns"}, "updated_at": "2026-10-13T00:00:00Z", **body, "environment": json.dumps(body["environment"])}
            self.next_id += 1
            self.applications[application["id"]] = application
            return httpx.Response(200, json=application)
        application_id = tail.lstrip("/").split(":")[0]
        application = self.applications.get(application_id)
        if application is None:
            return httpx.Response(404, json={"message": "not found"})
        if request.method == "GET":
            return httpx.Response(200, json=application)
        if request.method == "PATCH":
            body = json.loads(request.content)
            if not isinstance(body.get("environment", ""), str):  # what the real API answered
                return httpx.Response(400, json={"error": "json: cannot unmarshal object into Go value of type string", "code": 3})
            application.update({**body, "environment": body.get("environment") or application["environment"]})
            return httpx.Response(200, json=application)
        if request.method == "POST" and tail.endswith((":restart", ":stop")) and not request.content:
            return httpx.Response(404, json={"error": "Not Found", "code": 5})  # what the real API answered without a body
        if request.method == "POST" and tail.endswith(":restart"):
            application["status"] = "APPLICATION_RUNNING"
            return httpx.Response(200, json={})
        if request.method == "POST" and tail.endswith(":stop"):
            application["status"] = "APPLICATION_STOPPED"
            return httpx.Response(200, json={})
        if request.method == "DELETE":
            del self.applications[application_id]
            return httpx.Response(200, json={})
        return httpx.Response(400, json={"message": "unsupported"})


@pytest.fixture
def workbench(monkeypatch):
    fake = FakeWorkbench()
    monkeypatch.setattr(deployment, "TRANSPORT", httpx.MockTransport(fake.handler))
    monkeypatch.setenv("FACTORY_DEPLOYMENT_PROVIDER", "cloudera-ai")
    monkeypatch.setenv("CDSW_DOMAIN", "ml-abc.example.cloudera.site")
    monkeypatch.setenv("CDSW_APIV2_KEY", "api-key-123")
    monkeypatch.setenv("CDSW_PROJECT_ID", "proj-1")
    monkeypatch.setenv("MCP_FACTORY_RUNTIME_IMAGE", "registry/mcp-factory-runtime:0.1.2")
    monkeypatch.setenv("FACTORY_CAI_BYPASS_AUTH", "true")
    return fake


def builder(registry):
    """A Builder whose settings see the provider variables set after the registry fixture."""
    from fastapi.testclient import TestClient
    from factory.api import create_app
    from factory.settings import Settings
    client = TestClient(create_app(Settings()))
    client.headers["Authorization"] = registry[0].headers["Authorization"]
    return client


def activate_release(sessions):
    with sessions.begin() as session:
        server = session.get(Server, SERVER_ID)
        release = Release(server_id=SERVER_ID, bundle={"tools": [], "connections": {}, "targets": [], "python_tools": [], "pack_sources": {}}, checksum="0" * 64, status="active", created_by="test")
        session.add(release)
        session.flush()
        server.active_release_id = release.id
        server.revision += 1
        return release.id


def test_cloudera_ai_provider_creates_updates_and_manages_the_application(registry, workbench):
    _, sessions, _ = registry
    client = builder(registry)
    assert client.post("/api/deployments", json={"revision": client.get("/api/workspace").json()["server"]["revision"]}).status_code == 422  # no active release yet
    first = activate_release(sessions)
    revision = client.get("/api/workspace").json()["server"]["revision"]
    created = client.post("/api/deployments", json={"revision": revision}).json()
    assert created["status"] == "provisioning", created["message"]
    assert created["application_id"] == "app-1" and created["provider"] == "cloudera-ai"
    assert created["endpoint"] == "https://my-mcp-server-85d30f87.ml-abc.example.cloudera.site/mcp"
    assert json.loads(workbench.applications["app-1"]["environment"])["FACTORY_DEPLOYED_RELEASE_ID"] == first
    assert json.loads(workbench.applications["app-1"]["environment"])["FACTORY_PUBLIC_MCP_URL"] == created["endpoint"]
    # Refresh reads the live status; the Workbench moved it to running.
    workbench.applications["app-1"]["status"] = "APPLICATION_RUNNING"
    revision = client.get("/api/workspace").json()["server"]["revision"]
    refreshed = client.post("/api/deployments/refresh", json={"revision": revision}).json()
    assert refreshed["status"] == "running" and refreshed["metrics"]["creator"] == "cburns"
    # Deploying a newer release updates the same application in place and restarts it.
    second = activate_release(sessions)
    revision = client.get("/api/workspace").json()["server"]["revision"]
    updated = client.post("/api/deployments", json={"revision": revision}).json()
    assert updated["application_id"] == "app-1" and updated["status"] == "running" and updated["deployed_release_id"] == second
    assert json.loads(workbench.applications["app-1"]["environment"])["FACTORY_DEPLOYED_RELEASE_ID"] == second
    assert ("POST", "/api/v2/projects/proj-1/applications/app-1:restart", "Bearer api-key-123") in workbench.calls
    revision = client.get("/api/workspace").json()["server"]["revision"]
    assert client.post("/api/deployments/stop", json={"revision": revision}).json()["status"] == "stopped"
    revision = client.get("/api/workspace").json()["server"]["revision"]
    assert client.post("/api/deployments/delete", json={"revision": revision}).json()["status"] == "not_deployed"
    assert workbench.applications == {}
    # The API key never reaches the Builder's responses or audit trail.
    assert "api-key-123" not in client.get("/api/workspace").text and "api-key-123" not in client.get("/api/audit").text


def test_cloudera_ai_provider_reports_configuration_and_api_errors(registry, workbench, monkeypatch):
    _, sessions, _ = registry
    monkeypatch.setenv("CDSW_APIV2_KEY", "wrong-key")
    client = builder(registry)
    activate_release(sessions)
    revision = client.get("/api/workspace").json()["server"]["revision"]
    failed = client.post("/api/deployments", json={"revision": revision}).json()
    assert failed["status"] == "failed" and "401" in failed["message"] and "wrong-key" not in failed["message"]
    monkeypatch.delenv("CDSW_PROJECT_ID")
    client = builder(registry)
    revision = client.get("/api/workspace").json()["server"]["revision"]
    assert "FACTORY_CAI_PROJECT_ID" in client.post("/api/deployments", json={"revision": revision}).json()["message"]


def test_cloudera_ai_provider_uses_the_builders_own_runtime_from_the_catalog(registry, workbench, monkeypatch):
    _, sessions, _ = registry
    monkeypatch.delenv("MCP_FACTORY_RUNTIME_IMAGE")
    for key, value in {"EDITION": "MCP Factory Development", "FULL_VERSION": "0.1.2", "EDITOR": "PBJ Workbench", "KERNEL": "Python 3.12"}.items():
        monkeypatch.setenv(f"ML_RUNTIME_{key}", value)
    client = builder(registry)
    activate_release(sessions)
    created = client.post("/api/deployments", json={"revision": client.get("/api/workspace").json()["server"]["revision"]}).json()
    assert created["status"] == "provisioning", created["message"]
    assert workbench.applications["app-1"]["runtime_identifier"] == "registry/mcp-factory-runtime:0.1.2"
    # A runtime missing from the catalog is reported with what to do.
    monkeypatch.setenv("ML_RUNTIME_FULL_VERSION", "9.9.9")
    revision = client.get("/api/workspace").json()["server"]["revision"]
    failed = client.post("/api/deployments", json={"revision": revision}).json()
    assert failed["status"] == "failed" and "No runtime in the Runtime Catalog matches" in failed["message"]


def test_live_status_follows_the_application_without_a_revision(registry, workbench):
    _, sessions, _ = registry
    client = builder(registry)
    release = activate_release(sessions)
    created = client.post("/api/deployments", json={"revision": client.get("/api/workspace").json()["server"]["revision"]}).json()
    assert created["status"] == "provisioning" and created["deployed_release_id"] is None
    viewer = {"Authorization": "Bearer " + __import__("os").environ["FACTORY_VIEWER_TOKEN"]}
    assert client.get("/api/deployments/live", headers=viewer).json()["status"] == "provisioning"  # unchanged: nothing recorded
    workbench.applications["app-1"]["status"] = "APPLICATION_RUNNING"
    live = client.get("/api/deployments/live", headers=viewer).json()
    assert live["status"] == "running" and live["deployed_release_id"] == release
    client.get("/api/deployments/live")
    from sqlalchemy import select
    from factory.db import Audit
    with sessions() as session:
        changes = list(session.scalars(select(Audit).where(Audit.action == "deployment.status")))
    assert len(changes) == 1 and changes[0].details["status"] == "running" and changes[0].actor == "deployment-monitor"


def test_the_server_script_is_a_path_from_the_project_root(monkeypatch):
    from factory.settings import Settings
    monkeypatch.setenv("CDSW_HOME", "/")  # in the test container the repository is /workspace, so "workspace/" is its folder
    assert deployment.server_script(Settings()) == "workspace/mcp_server_app.py"
    monkeypatch.setenv("CDSW_HOME", "/workspace")
    assert deployment.server_script(Settings()) == "mcp_server_app.py"
    monkeypatch.setenv("FACTORY_CAI_SCRIPT", "custom/start.py")
    assert deployment.server_script(Settings()) == "custom/start.py"


def test_builder_health_reports_the_code_revision(registry):
    client, _, _ = registry
    body = client.get("/healthz").json()
    assert body["status"] == "ok" and body["revision"] and body["revision"] != ""


def test_the_first_deploy_chooses_the_name_and_later_deploys_follow_the_application_id(registry, workbench):
    client, sessions, _ = registry
    client = builder(registry)
    activate_release(sessions)
    rev = lambda: client.get("/api/workspace").json()["server"]["revision"]
    assert client.post("/api/deployments", json={"revision": rev(), "application_name": "Helios_MCP"}).status_code == 422
    other = client.post("/api/servers", json={"name": "Other"}).json()
    with sessions.begin() as session:
        from factory.db import Deployment
        from sqlalchemy import select
        session.scalar(select(Deployment).where(Deployment.server_id == other["id"])).application_name = "taken-name"
    assert client.post("/api/deployments", json={"revision": rev(), "application_name": "taken-name"}).status_code == 409
    created = client.post("/api/deployments", json={"revision": rev(), "application_name": "helios-mcp"}).json()
    assert created["application_name"] == "helios-mcp" and workbench.applications["app-1"]["subdomain"] == "helios-mcp"
    assert created["endpoint"] == "https://helios-mcp.ml-abc.example.cloudera.site/mcp"
    assert client.post("/api/deployments", json={"revision": rev(), "application_name": "renamed"}).status_code == 409
    # Later deploys update the same application by ID, even if it was renamed in Workbench meanwhile.
    workbench.applications["app-1"]["name"] = "renamed-in-workbench"
    again = client.post("/api/deployments", json={"revision": rev()}).json()
    assert again["application_id"] == "app-1" and list(workbench.applications) == ["app-1"]
    # A failed deploy keeps the application it knows about.
    original = workbench.handler
    workbench.handler = lambda request: httpx.Response(500, json={"error": "boom"}) if request.method == "PATCH" else original(request)
    deployment.TRANSPORT = httpx.MockTransport(workbench.handler)
    failed = client.post("/api/deployments", json={"revision": rev()}).json()
    # Workbench is the truth for the application's name: the rename there was kept, and survives the failure.
    assert failed["status"] == "failed" and failed["application_id"] == "app-1" and failed["application_name"] == "renamed-in-workbench"


def test_deploy_adopts_an_application_that_already_serves_the_server(registry, workbench):
    """An application someone created by hand for this server ID is updated, never duplicated."""
    _, sessions, _ = registry
    client = builder(registry)
    workbench.applications["manual-1"] = {"id": "manual-1", "name": "MCP-Factory-Server", "subdomain": "mcp-factory-server", "status": "APPLICATION_RUNNING",
        "script": "daedalus/mcp_server_app.py", "environment": json.dumps({"FACTORY_SERVER_ID": SERVER_ID, "FACTORY_MCP_TOKEN": "kept-by-the-user"})}
    release = activate_release(sessions)
    result = client.post("/api/deployments", json={"revision": client.get("/api/workspace").json()["server"]["revision"], "application_name": "my-mcp-server"}).json()
    assert list(workbench.applications) == ["manual-1"]  # nothing new was created
    assert result["application_id"] == "manual-1" and result["application_name"] == "MCP-Factory-Server"
    assert result["message"].startswith("Adopted MCP-Factory-Server, which already served this server")
    app = workbench.applications["manual-1"]
    env = json.loads(app["environment"])
    assert app["subdomain"] == "mcp-factory-server" and env["FACTORY_MCP_TOKEN"] == "kept-by-the-user" and env["FACTORY_DEPLOYED_RELEASE_ID"] == release
    assert result["endpoint"] == "https://mcp-factory-server.ml-abc.example.cloudera.site/mcp"
