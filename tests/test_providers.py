"""The docker and kubernetes deployment providers, driven through the API against fakes of each platform's HTTP API."""
import json

import httpx
import pytest

from factory.providers import docker, kubernetes
from test_deploy import activate_release, builder

IMAGE = "daedalus:test"


class FakeDocker:
    """Enough of the Docker Engine API for the provider: list, create, start, inspect, stop, remove."""

    def __init__(self):
        self.containers, self.calls, self.next_port = {}, [], 32768
        self.images = {IMAGE}

    def handler(self, request: httpx.Request):
        path, method = request.url.path, request.method
        self.calls.append((method, path))
        if method == "GET" and path == "/containers/json":
            filters = json.loads(request.url.params.get("filters", "{}"))
            items = list(self.containers.values())
            if "label" in filters:
                key, value = filters["label"][0].split("=", 1)
                items = [c for c in items if c["Config"]["Labels"].get(key) == value]
            if "name" in filters:
                items = [c for c in items if c["Name"] == filters["name"][0].strip("^$")]
            return httpx.Response(200, json=[{"Id": c["Id"], "Names": [c["Name"]], "Labels": c["Config"]["Labels"]} for c in items])
        if method == "POST" and path == "/containers/create":
            body = json.loads(request.content)
            if body["Image"] not in self.images:
                return httpx.Response(404, json={"message": f"No such image: {body['Image']}"})
            name = request.url.params["name"]
            if any(c["Name"] == "/" + name for c in self.containers.values()):
                return httpx.Response(409, json={"message": f"Conflict. The container name /{name} is already in use"})
            wanted = body["HostConfig"].get("PortBindings", {}).get("8081/tcp", [{}])[0].get("HostPort") or str(self.next_port)
            self.next_port += 1
            cid = f"c{len(self.calls):04d}" + "0" * 56
            self.containers[cid] = {"Id": cid, "Name": "/" + name, "Config": {"Image": body["Image"], "Env": body["Env"], "Labels": body["Labels"], "Cmd": body["Cmd"]},
                "HostConfig": body["HostConfig"], "State": {"Status": "created", "ExitCode": 0, "StartedAt": ""}, "NetworkSettings": {"Ports": {"8081/tcp": [{"HostIp": "0.0.0.0", "HostPort": wanted}]}}}
            return httpx.Response(201, json={"Id": cid, "Warnings": []})
        cid = path.split("/")[2]
        container = self.containers.get(cid)
        if container is None:
            return httpx.Response(404, json={"message": f"No such container: {cid}"})
        if method == "GET" and path.endswith("/json"):
            return httpx.Response(200, json=container)
        if method == "POST" and path.endswith("/start"):
            container["State"].update(Status="running", StartedAt="2026-10-29T12:00:00Z")
            return httpx.Response(204)
        if method == "POST" and path.endswith("/stop"):
            container["State"].update(Status="exited", ExitCode=143)  # what docker stop leaves behind: ended by SIGTERM
            return httpx.Response(204)
        if method == "DELETE":
            del self.containers[cid]
            return httpx.Response(204)
        return httpx.Response(400, json={"message": "unsupported"})


@pytest.fixture
def engine(monkeypatch):
    fake = FakeDocker()
    monkeypatch.setattr(docker, "TRANSPORT", httpx.MockTransport(fake.handler))
    monkeypatch.setenv("FACTORY_DEPLOYMENT_PROVIDER", "docker")
    monkeypatch.setenv("FACTORY_SERVER_IMAGE", IMAGE)
    monkeypatch.setenv("FACTORY_DOCKER_NETWORK", "daedalus_default")
    monkeypatch.setenv("FACTORY_SECRET_INVENTORY", "s3cret")
    return fake


def revision(client):
    return client.get("/api/workspace").json()["server"]["revision"]


def test_docker_provider_runs_a_container_per_server_and_manages_it(registry, engine):
    _, sessions, _ = registry
    client = builder(registry)
    info = client.get("/api/workspace").json()["deployment_provider"]
    assert info["name"] == "docker" and info["manages"] and info["target"] == "container" and info["configuration_error"] is None
    release = activate_release(sessions)
    deployed = client.post("/api/deployments", json={"revision": revision(client), "application_name": "files-mcp"}).json()
    assert deployed["status"] == "running", deployed
    assert deployed["application_name"] == "files-mcp" and deployed["endpoint"] == "http://localhost:32768/mcp" and deployed["deployed_release_id"] == release
    assert deployed["metrics"]["network"] == "daedalus_default" and deployed["metrics"]["image"] == IMAGE
    container = engine.containers[deployed["application_id"]]
    env = dict(e.split("=", 1) for e in container["Config"]["Env"])
    assert env["FACTORY_SERVER_ID"] and env["FACTORY_DEPLOYED_RELEASE_ID"] == release and env["DATABASE_URL"] and env["FACTORY_MCP_TOKEN"]
    assert env["FACTORY_GATEWAY_BIND"] == "0.0.0.0" and env["FACTORY_SECRET_INVENTORY"] == "s3cret" and container["Config"]["Cmd"] == ["server"]
    assert container["Config"]["Labels"]["daedalus.server-id"] == env["FACTORY_SERVER_ID"] and container["HostConfig"]["NetworkMode"] == "daedalus_default"
    # A redeploy recreates the container under the same name and keeps its host port, so the endpoint is stable.
    again = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert again["application_id"] != deployed["application_id"] and again["endpoint"] == deployed["endpoint"] and len(engine.containers) == 1
    stopped = client.post("/api/deployments/stop", json={"revision": revision(client)}).json()
    assert stopped["status"] == "stopped" and "exited" in stopped["message"]
    assert client.get("/api/deployments/live").json()["status"] == "stopped"
    engine.containers[again["application_id"]]["State"].update(Status="exited", ExitCode=1)  # a crash, unlike a stop
    assert client.get("/api/deployments/live").json()["status"] == "failed"
    deleted = client.post("/api/deployments/delete", json={"revision": revision(client)}).json()
    assert deleted["status"] == "not_deployed" and engine.containers == {}
    assert client.get("/api/deployments/live").json()["status"] == "not_deployed"


def test_docker_provider_adopts_a_container_that_serves_the_server_and_reports_missing_images(registry, engine, monkeypatch):
    _, sessions, _ = registry
    client = builder(registry)
    activate_release(sessions)
    first = client.post("/api/deployments", json={"revision": revision(client)}).json()
    # Forget the container ID, as a fresh registry would: Deploy finds it again by its server label.
    with sessions.begin() as session:
        from factory.db import Deployment
        session.query(Deployment).first().application_id = None
    adopted = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert adopted["status"] == "running" and adopted["message"].startswith("Adopted the container") and adopted["application_name"] == first["application_name"]
    engine.images.clear()
    failed = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert failed["status"] == "failed" and "no image daedalus:test" in failed["message"]
    monkeypatch.delenv("FACTORY_SERVER_IMAGE")
    client = builder(registry)
    assert "FACTORY_SERVER_IMAGE" in client.get("/api/workspace").json()["deployment_provider"]["configuration_error"]
    assert "FACTORY_SERVER_IMAGE" in client.post("/api/deployments", json={"revision": revision(client)}).json()["message"]


def test_deleting_a_server_removes_its_container(registry, engine):
    _, sessions, _ = registry
    client = builder(registry)
    created = client.post("/api/servers", json={"name": "Disposable"}).json()
    with sessions.begin() as session:
        from factory.db import Release, Server
        server = session.get(Server, created["id"])
        rel = Release(server_id=server.id, bundle={"tools": [], "connections": {}, "targets": [], "python_tools": [], "pack_sources": {}}, checksum="0" * 64, status="active", created_by="test")
        session.add(rel); session.flush(); server.active_release_id = rel.id; server.revision += 1
    rev = client.get("/api/workspace", params={"server_id": created["id"]}).json()["server"]["revision"]
    deployed = client.post("/api/deployments", params={"server_id": created["id"]}, json={"revision": rev}).json()
    assert deployed["status"] == "running" and len(engine.containers) == 1
    rev = client.get("/api/workspace", params={"server_id": created["id"]}).json()["server"]["revision"]
    assert client.delete(f"/api/servers/{created['id']}", headers={"If-Match": str(rev)}).status_code == 204
    assert engine.containers == {}


class FakeKubernetes:
    """Enough of the Kubernetes API for the provider: deployments and services in one namespace."""

    def __init__(self):
        self.deployments, self.services, self.calls = {}, {}, []

    def handler(self, request: httpx.Request):
        path, method = request.url.path, request.method
        self.calls.append((method, path))
        if request.headers.get("authorization") != "Bearer sa-token":
            return httpx.Response(401, json={"message": "Unauthorized"})
        for prefix, store in (("/apis/apps/v1/namespaces/mcp/deployments", self.deployments), ("/api/v1/namespaces/mcp/services", self.services)):
            if path == prefix:
                if method == "GET":
                    selector = request.url.params.get("labelSelector")
                    items = list(store.values())
                    if selector:
                        key, value = selector.split("=", 1)
                        items = [i for i in items if i["metadata"]["labels"].get(key) == value]
                    return httpx.Response(200, json={"items": items})
                if method == "POST":
                    body = json.loads(request.content)
                    if body["metadata"]["name"] in store:
                        return httpx.Response(409, json={"message": "already exists"})
                    if body["kind"] == "Deployment":
                        body["status"] = {"readyReplicas": 0, "replicas": 1, "observedGeneration": 1, "conditions": [{"type": "Progressing", "status": "True"}]}
                    store[body["metadata"]["name"]] = body
                    return httpx.Response(201, json=body)
            if path.startswith(prefix + "/"):
                name = path[len(prefix) + 1:]
                item = store.get(name)
                if item is None:
                    return httpx.Response(404, json={"message": f"{name} not found"})
                if method == "GET":
                    return httpx.Response(200, json=item)
                if method == "PATCH":
                    assert request.headers["content-type"] == "application/merge-patch+json"
                    body = json.loads(request.content)
                    if "spec" in body:
                        item["spec"] = {**item["spec"], **body["spec"]}
                        if body["spec"].get("replicas") == 0:
                            item["status"]["readyReplicas"] = 0
                    return httpx.Response(200, json=item)
                if method == "DELETE":
                    del store[name]
                    return httpx.Response(200, json={"status": "Success"})
        return httpx.Response(400, json={"message": f"unsupported {method} {path}"})

    def become_ready(self, name):
        self.deployments[name]["status"]["readyReplicas"] = 1


@pytest.fixture
def cluster(monkeypatch):
    fake = FakeKubernetes()
    monkeypatch.setattr(kubernetes, "TRANSPORT", httpx.MockTransport(fake.handler))
    for key, value in {"FACTORY_DEPLOYMENT_PROVIDER": "kubernetes", "FACTORY_SERVER_IMAGE": IMAGE, "FACTORY_K8S_API_URL": "https://kube.example",
            "FACTORY_K8S_TOKEN": "sa-token", "FACTORY_K8S_NAMESPACE": "mcp", "FACTORY_K8S_INSECURE": "true"}.items():
        monkeypatch.setenv(key, value)
    return fake


def test_kubernetes_provider_creates_a_deployment_and_service_per_server(registry, cluster):
    _, sessions, _ = registry
    client = builder(registry)
    info = client.get("/api/workspace").json()["deployment_provider"]
    assert info == {"name": "kubernetes", "label": "Kubernetes", "manages": True, "target": "deployment", "endpoint_pattern": "http://{name}.mcp.svc:8081/mcp",
        "name_fixed_after_create": False, "configuration_error": None}
    release = activate_release(sessions)
    deployed = client.post("/api/deployments", json={"revision": revision(client), "application_name": "files-mcp"}).json()
    assert deployed["status"] == "provisioning" and deployed["endpoint"] == "http://files-mcp.mcp.svc:8081/mcp" and deployed["message"] == "Deployment files-mcp: 0/1 ready"
    body = cluster.deployments["files-mcp"]
    container = body["spec"]["template"]["spec"]["containers"][0]
    env = {e["name"]: e["value"] for e in container["env"]}
    assert container["image"] == IMAGE and container["args"] == ["server"] and env["FACTORY_DEPLOYED_RELEASE_ID"] == release and env["DATABASE_URL"]
    assert env["FACTORY_PUBLIC_MCP_URL"] == "http://files-mcp.mcp.svc:8081/mcp" and body["metadata"]["labels"]["daedalus.io/server-id"] == env["FACTORY_SERVER_ID"]
    assert cluster.services["files-mcp"]["spec"]["ports"][0]["port"] == 8081 and container["resources"]["limits"] == {"cpu": "500m", "memory": "1Gi"}
    cluster.become_ready("files-mcp")
    live = client.get("/api/deployments/live").json()
    assert live["status"] == "running" and live["deployed_release_id"] == release
    # Redeploy patches the same Deployment; stop scales it to zero; delete removes both objects.
    again = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert again["application_id"] == "files-mcp" and ("PATCH", "/apis/apps/v1/namespaces/mcp/deployments/files-mcp") in cluster.calls
    stopped = client.post("/api/deployments/stop", json={"revision": revision(client)}).json()
    assert stopped["status"] == "stopped" and cluster.deployments["files-mcp"]["spec"]["replicas"] == 0
    deleted = client.post("/api/deployments/delete", json={"revision": revision(client)}).json()
    assert deleted["status"] == "not_deployed" and cluster.deployments == {} and cluster.services == {}


def test_kubernetes_provider_uses_the_endpoint_template_and_reports_auth_errors(registry, cluster, monkeypatch):
    _, sessions, _ = registry
    monkeypatch.setenv("FACTORY_ENDPOINT_TEMPLATE", "https://{name}.mcp.example.com/mcp")
    client = builder(registry)
    activate_release(sessions)
    deployed = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert deployed["endpoint"] == f"https://{deployed['application_name']}.mcp.example.com/mcp"
    monkeypatch.setenv("FACTORY_K8S_TOKEN", "wrong")
    client = builder(registry)
    failed = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert failed["status"] == "failed" and "401" in failed["message"] and "wrong" not in failed["message"]


def test_an_unknown_provider_is_reported_not_crashed(registry, monkeypatch):
    monkeypatch.setenv("FACTORY_DEPLOYMENT_PROVIDER", "heroku")
    client = builder(registry)
    info = client.get("/api/workspace").json()["deployment_provider"]
    assert info["name"] == "heroku" and "must be one of" in info["configuration_error"]


def test_docker_socket_problems_are_explained(registry, engine, monkeypatch):
    _, sessions, _ = registry
    def denied(request):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(docker, "TRANSPORT", httpx.MockTransport(denied))
    client = builder(registry)
    activate_release(sessions)
    failed = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert failed["status"] == "failed" and failed["message"].startswith("The Builder may not use the Docker socket at unix:///var/run/docker.sock: permission denied")
    monkeypatch.setattr(docker, "TRANSPORT", httpx.MockTransport(lambda request: (_ for _ in ()).throw(httpx.ConnectError("connection refused"))))
    failed = client.post("/api/deployments", json={"revision": revision(client)}).json()
    assert "Docker is not reachable at unix:///var/run/docker.sock" in failed["message"]
