"""One container per MCP server through the Docker Engine API (unix socket or tcp).

The Builder needs the Docker socket mounted (or FACTORY_DOCKER_HOST=tcp://...) and FACTORY_SERVER_IMAGE set to
the Daedalus image. Containers cannot be reconfigured in place, so a redeploy recreates the container under the
same name; the registry, not the container, holds every release, so nothing is lost.
"""
import json
from urllib.parse import urlsplit

import httpx

from . import SERVER_PORT, Provider, server_environment

TRANSPORT = None  # tests inject an httpx.MockTransport here
LABEL_SERVER, LABEL_RELEASE, LABEL_MANAGED = "daedalus.server-id", "daedalus.release-id", "daedalus.managed-by"
STATES = {"running": "running", "created": "provisioning", "restarting": "provisioning", "removing": "stopping", "paused": "stopped"}
STOP_CODES = {0, 130, 137, 143}  # clean exit, or ended by SIGINT/SIGKILL/SIGTERM: a stop, not a crash


class Docker(Provider):
    name = "docker"
    label = "Docker"
    manages = True
    target = "container"

    def configuration_error(self):
        if not self.settings.server_image:
            return "Set FACTORY_SERVER_IMAGE to the Daedalus image that Server containers run"
        return None

    def client(self):
        host = self.settings.docker_host
        if host.startswith("unix://"):
            return httpx.Client(base_url="http://docker", transport=TRANSPORT or httpx.HTTPTransport(uds=host[len("unix://"):]), timeout=60, trust_env=False)
        parts = urlsplit(host.replace("tcp://", "http://", 1))
        return httpx.Client(base_url=f"{parts.scheme}://{parts.netloc}", transport=TRANSPORT, timeout=60, trust_env=False)

    def api(self, method, path, allow_missing=False, **kwargs):
        try:
            with self.client() as client:
                response = client.request(method, path, **kwargs)
        except PermissionError as exc:
            raise ValueError(f"The Builder may not use the Docker socket at {self.settings.docker_host}: permission denied. Run the Builder container with the socket's group "
                "(docker compose: group_add with the socket's gid) or point FACTORY_DOCKER_HOST at a TCP endpoint") from exc
        except (FileNotFoundError, httpx.ConnectError) as exc:
            raise ValueError(f"Docker is not reachable at {self.settings.docker_host}: {exc}. Mount /var/run/docker.sock into the Builder or set FACTORY_DOCKER_HOST") from exc
        if response.status_code == 404 and allow_missing:
            return None
        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text)
            except ValueError:
                detail = response.text
            raise ValueError(f"Docker returned {response.status_code} for {method} {path.split('?')[0]}: {str(detail)[:300]}")
        return response.json() if response.content and response.status_code != 204 else {}

    def inspect(self, container_id):
        return self.api("GET", f"/containers/{container_id}/json", allow_missing=True) if container_id else None

    def find(self, server_id, name):
        """The container already serving this MCP server (by label), else the one with this name."""
        for filters in ({"label": [f"{LABEL_SERVER}={server_id}"]}, {"name": [f"^/{name}$"]}):
            found = self.api("GET", "/containers/json", params={"all": "true", "filters": json.dumps(filters)})
            if found:
                return self.inspect(found[0]["Id"])
        return None

    def deploy(self, document, deployment):
        self.ready()
        s = self.settings
        existing = self.inspect(deployment.get("application_id")) or self.find(document["server_id"], document["name"])
        name = existing["Name"].lstrip("/") if existing else document["name"]
        adopted = bool(existing) and existing["Id"] != deployment.get("application_id")
        environment = server_environment(document)
        if "FACTORY_PUBLIC_MCP_URL" not in environment:
            known = self.endpoint(name, host=s.docker_host_name) or (None if s.docker_publish else f"http://{name}:{SERVER_PORT}/mcp")
            if known:
                environment["FACTORY_PUBLIC_MCP_URL"] = known
        host_config = {"RestartPolicy": {"Name": "unless-stopped"}}
        if s.docker_network:
            host_config["NetworkMode"] = s.docker_network
        if s.docker_publish:
            # Keep the host port a previous container of this server had, so the endpoint stays stable.
            previous = (existing or {}).get("NetworkSettings", {}).get("Ports", {}).get(f"{SERVER_PORT}/tcp") or [{}]
            host_config["PortBindings"] = {f"{SERVER_PORT}/tcp": [{"HostPort": previous[0].get("HostPort", "")}]}
        if existing:
            self.api("DELETE", f"/containers/{existing['Id']}", allow_missing=True, params={"force": "true", "v": "true"})
        body = {"Image": s.server_image, "Cmd": ["server"], "Env": [f"{k}={v}" for k, v in sorted(environment.items())],
            "Labels": {LABEL_SERVER: document["server_id"], LABEL_RELEASE: document["release_id"], LABEL_MANAGED: "daedalus"},
            "ExposedPorts": {f"{SERVER_PORT}/tcp": {}}, "HostConfig": host_config}
        try:
            created = self.api("POST", "/containers/create", params={"name": name}, json=body)
        except ValueError as exc:
            if "404" in str(exc):
                raise ValueError(f"Docker has no image {s.server_image}; build or pull it on the Docker host first") from exc
            raise
        self.api("POST", f"/containers/{created['Id']}/start")
        return self.describe(self.inspect(created["Id"]), name, adopted)

    def describe(self, info, name, adopted=False):
        state = info.get("State", {})
        status = STATES.get(state.get("Status"), "stopped" if state.get("ExitCode", 0) in STOP_CODES and state.get("Status") != "dead" else "failed")
        bindings = (info.get("NetworkSettings") or {}).get("Ports", {}).get(f"{SERVER_PORT}/tcp") or []
        host_port = next((b.get("HostPort") for b in bindings if b.get("HostPort")), None)
        endpoint = self.endpoint(name, port=host_port or SERVER_PORT, host=self.settings.docker_host_name) or (
            f"http://{self.settings.docker_host_name}:{host_port}/mcp" if host_port else f"http://{name}:{SERVER_PORT}/mcp")
        detail = f" (exit code {state.get('ExitCode')})" if state.get("Status") == "exited" else (f": {state['Error']}" if state.get("Error") else "")
        message = ("Adopted the container that already served this server; " if adopted else "") + f"Container {name} {state.get('Status', 'unknown')}{detail}"
        metrics = {"container_id": info.get("Id", "")[:12], "image": (info.get("Config") or {}).get("Image"), "network": self.settings.docker_network or "default",
            "host_port": host_port, "started_at": state.get("StartedAt")}
        return self.result(status, name, message, info.get("Id"), endpoint, metrics)

    def refresh(self, deployment):
        info = self.inspect(deployment.get("application_id"))
        if info is None:
            return {"status": "not_deployed", "message": "Container no longer exists", "metrics": {}}
        return self.describe(info, deployment.get("application_name") or info["Name"].lstrip("/"))

    def stop(self, deployment):
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its container")
        self.api("POST", f"/containers/{deployment['application_id']}/stop", params={"t": "20"}, allow_missing=True)
        return self.refresh(deployment)

    def delete(self, deployment):
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its container")
        self.api("DELETE", f"/containers/{deployment['application_id']}", allow_missing=True, params={"force": "true", "v": "true"})
        return {"status": "not_deployed", "message": "Container deleted", "metrics": {}}
