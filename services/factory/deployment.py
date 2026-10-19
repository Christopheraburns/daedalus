"""Deployment providers for dedicated Workbench Server applications.

    manual         records a reviewable intent and does nothing else (default)
    cloudera-ai    creates and manages the Server application through the Cloudera AI
                   Workbench API v2 (/api/v2/projects/{id}/applications), as a Builder
                   running inside the same project
    cloudera-bridge  calls a customer-supplied deployment bridge (legacy integration point)

The cloudera-ai provider was written from the API v2 application contract
(name, subdomain, script, runtime_identifier, environment, cpu, memory,
bypass_authentication) and the cmlapi status values; it is exercised here against
a fake and must be verified against the target Workbench release.
"""
import json
import os
import re
from urllib.request import Request, urlopen

import httpx

TRANSPORT = None  # tests inject an httpx.MockTransport here
STATUS = {"APPLICATION_RUNNING": "running", "APPLICATION_STARTING": "provisioning", "APPLICATION_STOPPING": "stopping",
    "APPLICATION_STOPPED": "stopped", "APPLICATION_FAILED": "failed", "APPLICATION_UNKNOWN": "unknown"}


def application_name(server_name, server_id):
    safe = "".join(c.lower() if c.isalnum() else "-" for c in server_name).strip("-")[:56] or "mcp-server"
    return f"{safe}-{server_id.split('-')[0]}"


def subdomain(name):
    # Subdomains are DNS labels: lowercase alphanumerics and hyphens, no leading/trailing hyphen.
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")[:63]


def manifest(server_id, release_id, server_name, settings):
    name = application_name(server_name, server_id)
    environment = {"FACTORY_SERVER_ID": server_id, "FACTORY_DEPLOYED_RELEASE_ID": release_id}
    if settings.cai_domain:
        environment["FACTORY_PUBLIC_MCP_URL"] = f"https://{subdomain(name)}.{settings.cai_domain}/mcp"
    return {"name": name, "kind": "daedalus-mcp-server", "server_id": server_id, "release_id": release_id, "subdomain": subdomain(name),
        "runtime_image": settings.cai_runtime_identifier, "entrypoint": "mcp_server_app.py", "environment": environment}


class ClouderaAI:
    """Thin client for the Workbench API v2 application endpoints."""

    def __init__(self, settings):
        missing = [name for name, value in (("FACTORY_CAI_API_URL (or CDSW_DOMAIN)", settings.cai_api_url), ("FACTORY_CAI_API_KEY (or CDSW_APIV2_KEY)", settings.cai_api_key),
            ("FACTORY_CAI_PROJECT_ID (or CDSW_PROJECT_ID)", settings.cai_project_id), ("FACTORY_CAI_RUNTIME_IDENTIFIER (or MCP_FACTORY_RUNTIME_IMAGE)", settings.cai_runtime_identifier)) if not value]
        if missing:
            raise ValueError("Configure " + ", ".join(missing) + " for the cloudera-ai deployment provider")
        self.settings = settings
        self.base = settings.cai_api_url.rstrip("/") + f"/api/v2/projects/{settings.cai_project_id}/applications"
        self.client = httpx.Client(headers={"Authorization": f"Bearer {settings.cai_api_key}", "Content-Type": "application/json"}, timeout=30, trust_env=False, transport=TRANSPORT)

    def request(self, method, path="", **kwargs):
        response = self.client.request(method, self.base + path, **kwargs)
        if response.status_code >= 400:
            raise ValueError(f"Cloudera AI API returned {response.status_code} for {method} applications{path}: {response.text[:300]}")
        return response.json() if response.content else {}

    def find(self, name):
        for application in self.request("GET").get("applications", []):
            if application.get("name") == name:
                return application
        return None

    def body(self, document):
        s = self.settings
        return {"name": document["name"], "description": f"Daedalus MCP server {document['server_id']} release {document['release_id']}", "subdomain": document["subdomain"],
            "script": document["entrypoint"], "runtime_identifier": document["runtime_image"], "environment": document["environment"],
            "cpu": s.cai_cpu, "memory": s.cai_memory, "bypass_authentication": s.cai_bypass_auth}

    def deploy(self, document):
        existing = self.find(document["name"])
        if existing:
            application = self.request("PATCH", f"/{existing['id']}", json=self.body(document))
            self.request("POST", f"/{existing['id']}:restart")
            return application or existing
        return self.request("POST", json=self.body(document))

    def status(self, application_id):
        return self.request("GET", f"/{application_id}")

    def stop(self, application_id):
        self.request("POST", f"/{application_id}:stop")

    def delete(self, application_id):
        self.request("DELETE", f"/{application_id}")


def describe(application, settings, name):
    status = STATUS.get(application.get("status", ""), "provisioning")
    endpoint = f"https://{application.get('subdomain') or subdomain(name)}.{settings.cai_domain}/mcp" if settings.cai_domain else None
    return {"status": status, "provider": "cloudera-ai", "application_name": name, "application_id": application.get("id"), "endpoint": endpoint,
        "message": f"Workbench application {application.get('status', 'created')}", "metrics": {"creator": (application.get("creator") or {}).get("username"), "updated_at": application.get("updated_at")}}


def deploy_server(server_id, release_id, server_name, settings):
    document = manifest(server_id, release_id, server_name, settings)
    if settings.deployment_provider == "manual":
        # Nothing is created; the Builder shows these values so an operator can create the application by hand.
        return {"status": "ready_to_deploy", "provider": "manual", "application_name": document["name"], "message": "Manual mode: no application was created. Create it with the values below, or set FACTORY_DEPLOYMENT_PROVIDER=cloudera-ai on the Builder application so Deploy creates it.",
            "metrics": {"manifest": {key: document[key] for key in ("name", "subdomain", "entrypoint", "runtime_image", "environment")}}}
    if settings.deployment_provider == "cloudera-ai":
        return describe(ClouderaAI(settings).deploy(document), settings, document["name"])
    if settings.deployment_provider != "cloudera-bridge":
        raise ValueError("FACTORY_DEPLOYMENT_PROVIDER must be manual, cloudera-ai or cloudera-bridge")
    if not (settings.cloudera_api_base_url and settings.cloudera_project_id and settings.cloudera_api_token):
        raise ValueError("Configure FACTORY_CLOUDERA_API_BASE_URL, FACTORY_CLOUDERA_PROJECT_ID, and FACTORY_CLOUDERA_API_TOKEN")
    body = json.dumps({"project_id": settings.cloudera_project_id, "application": document}).encode()
    request = Request(settings.cloudera_api_base_url.rstrip("/") + "/v1/daedalus/applications", data=body,
        headers={"Authorization": "Bearer " + settings.cloudera_api_token, "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    return {"status": result.get("status", "provisioning"), "provider": "cloudera-bridge", "application_name": document["name"],
        "application_id": result.get("id"), "endpoint": result.get("endpoint"), "message": result.get("message")}


def deployment_action(action, deployment, settings):
    if settings.deployment_provider == "manual":
        statuses = {"stop": "stopped", "delete": "not_deployed", "refresh": deployment["status"]}
        return {"status": statuses[action], "message": "Recorded locally; in manual mode, manage the application in Workbench yourself.", "metrics": deployment.get("metrics", {})}
    if settings.deployment_provider == "cloudera-ai":
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its application")
        api = ClouderaAI(settings)
        if action == "delete":
            api.delete(deployment["application_id"])
            return {"status": "not_deployed", "message": "Workbench application deleted", "metrics": {}}
        if action == "stop":
            api.stop(deployment["application_id"])
        return describe(api.status(deployment["application_id"]), settings, deployment.get("application_name") or "mcp-server")
    if settings.deployment_provider != "cloudera-bridge" or not deployment.get("application_id"):
        raise ValueError("A provisioned Cloudera bridge application is required")
    body = json.dumps({"action": action}).encode()
    request = Request(settings.cloudera_api_base_url.rstrip("/") + "/v1/daedalus/applications/" + deployment["application_id"], data=body,
        headers={"Authorization": "Bearer " + settings.cloudera_api_token, "Content-Type": "application/json"}, method="PATCH")
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    return {"status": result.get("status", deployment["status"]), "message": result.get("message"), "metrics": result.get("metrics", {})}
