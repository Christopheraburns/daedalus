"""A Cloudera AI Workbench application per MCP server, through the Workbench API v2.

Written from the API v2 application contract (name, subdomain, script, runtime_identifier, environment,
cpu, memory, bypass_authentication) and the cmlapi status values, and verified against a Workbench: the
update call takes the environment as a JSON string, and :restart/:stop need a JSON body.
"""
import json
import os

import httpx

from . import Provider
from ..deployment import subdomain

TRANSPORT = None  # tests inject an httpx.MockTransport here
STATUS = {"APPLICATION_RUNNING": "running", "APPLICATION_STARTING": "provisioning", "APPLICATION_STOPPING": "stopping",
    "APPLICATION_STOPPED": "stopped", "APPLICATION_FAILED": "failed", "APPLICATION_UNKNOWN": "unknown"}


def application_name(server_name, server_id):
    safe = "".join(c.lower() if c.isalnum() else "-" for c in server_name).strip("-")[:56] or "mcp-server"
    return f"{safe}-{server_id.split('-')[0]}"


def subdomain(name):
    # Subdomains are DNS labels: lowercase alphanumerics and hyphens, no leading/trailing hyphen.
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")[:63]


def server_script(settings):
    """mcp_server_app.py as a path from the Workbench project root (FACTORY_CAI_HOME), wherever the repository sits."""
    if settings.cai_script:
        return settings.cai_script
    script = (Path(__file__).resolve().parents[2] / "mcp_server_app.py")
    try:
        return script.relative_to(Path(settings.cai_home or Path.home()).resolve()).as_posix()
    except ValueError:
        return "mcp_server_app.py"


def valid_application_name(name):
    return bool(re.fullmatch(r"[a-z][a-z0-9-]{1,61}[a-z0-9]", name or ""))


def manifest(server_id, release_id, server_name, settings, name=None):
    name = name or application_name(server_name, server_id)
    environment = {"FACTORY_SERVER_ID": server_id, "FACTORY_DEPLOYED_RELEASE_ID": release_id}
    if settings.cai_domain:
        environment["FACTORY_PUBLIC_MCP_URL"] = f"https://{subdomain(name)}.{settings.cai_domain}/mcp"
    return {"name": name, "kind": "daedalus-mcp-server", "server_id": server_id, "release_id": release_id, "subdomain": subdomain(name),
        "runtime_image": settings.cai_runtime_identifier, "entrypoint": server_script(settings), "environment": environment}


class ClouderaAI:
    """Thin client for the Workbench API v2 application endpoints."""

    def __init__(self, settings):
        missing = [name for name, value in (("FACTORY_CAI_API_URL", settings.cai_api_url), ("FACTORY_CAI_API_KEY", settings.cai_api_key),
            ("FACTORY_CAI_PROJECT_ID", settings.cai_project_id)) if not value]
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

    def runtime_identifier(self):
        """The runtime image for the Server application: configured explicitly, or the runtime this Builder
        runs on, found in the Workbench runtime catalog by the ML_RUNTIME_* metadata every runtime carries."""
        if self.settings.cai_runtime_identifier:
            return self.settings.cai_runtime_identifier
        own = {key: os.getenv(f"ML_RUNTIME_{key.upper()}", "") for key in ("edition", "full_version", "editor", "kernel")}
        if not own["edition"]:
            raise ValueError("Set FACTORY_CAI_RUNTIME_IDENTIFIER to the Server runtime's image (as listed in the Runtime Catalog); this runtime does not advertise ML_RUNTIME_EDITION")
        url = self.settings.cai_api_url.rstrip("/") + "/api/v2/runtimes"
        response = self.client.get(url, params={"search_filter": json.dumps({"edition": own["edition"]}), "page_size": 100})
        if response.status_code >= 400:
            raise ValueError(f"Cloudera AI API returned {response.status_code} for GET runtimes: {response.text[:300]}")
        candidates = [r for r in response.json().get("runtimes", []) if r.get("edition") == own["edition"] and r.get("image_identifier")]
        exact = [r for r in candidates if all(not own[k] or not r.get(k) or r.get(k) == own[k] for k in ("full_version", "editor", "kernel"))]
        if not exact:
            raise ValueError(f"No runtime in the Runtime Catalog matches this Builder's runtime ({own['edition']} {own['full_version']}); register it or set FACTORY_CAI_RUNTIME_IDENTIFIER")
        return exact[0]["image_identifier"]

    def applications(self):
        return self.request("GET").get("applications", [])

    def find(self, name):
        return next((a for a in self.applications() if a.get("name") == name), None)

    def serving(self, server_id):
        """The project's application already running a Server for this MCP server (FACTORY_SERVER_ID), if any,
        whether Deploy made it or someone created it by hand."""
        return next((a for a in self.applications() if environment_of(a).get("FACTORY_SERVER_ID") == server_id), None)

    def body(self, document):
        s = self.settings
        return {"name": document["name"], "description": f"Daedalus MCP server {document['server_id']} release {document['release_id']}", "subdomain": document["subdomain"],
            "script": document["entrypoint"], "runtime_identifier": document["runtime_image"], "environment": document["environment"],
            "cpu": s.cai_cpu, "memory": s.cai_memory, "bypass_authentication": s.cai_bypass_auth}

    def get_application(self, application_id):
        response = self.client.get(f"{self.base}/{application_id}")
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise ValueError(f"Cloudera AI API returned {response.status_code} for GET applications/{application_id}: {response.text[:300]}")
        return response.json()

    def deploy(self, document, application_id=None):
        """Create the Server application, or update the one that already serves this MCP server. Only one
        Server may run per MCP server, so an application found by its FACTORY_SERVER_ID is adopted rather than
        duplicated, keeping its name, subdomain and any variables someone added to it."""
        document = {**document, "runtime_image": self.runtime_identifier()}
        existing = (self.get_application(application_id) if application_id else None) or self.serving(document["server_id"]) or self.find(document["name"])
        if existing:
            adopted = existing.get("id") != application_id and existing.get("name") != document["name"]
            document = {**document, "name": existing.get("name") or document["name"], "subdomain": existing.get("subdomain") or document["subdomain"],
                "environment": {**environment_of(existing), **document["environment"]}}
            # The update call takes the Application resource, whose environment is a JSON-encoded string
            # (verified against Workbench: an object is rejected with "cannot unmarshal object into ... string").
            update = {**self.body(document), "environment": json.dumps(document["environment"])}
            application = self.request("PATCH", f"/{existing['id']}", json=update) or existing
            # Workbench answers 404 to :restart and :stop without a JSON body (verified); send an empty one.
            self.request("POST", f"/{existing['id']}:restart", json={})
            return {**application, "_adopted": adopted}
        return self.request("POST", json=self.body(document))

    def status(self, application_id):
        return self.request("GET", f"/{application_id}")

    def stop(self, application_id):
        self.request("POST", f"/{application_id}:stop", json={})

    def delete(self, application_id):
        self.request("DELETE", f"/{application_id}")


def environment_of(application):
    """An application's environment variables; the API returns them as a JSON string (as an object on create)."""
    value = application.get("environment") or {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            value = {}
    return value if isinstance(value, dict) else {}


def describe(application, settings, name):
    status = STATUS.get(application.get("status", ""), "provisioning")
    name = application.get("name") or name
    endpoint = f"https://{application.get('subdomain') or subdomain(name)}.{settings.cai_domain}/mcp" if settings.cai_domain else None
    message = f"Adopted {name}, which already served this server; Workbench application {application.get('status', 'updated')}" if application.get("_adopted") else f"Workbench application {application.get('status', 'created')}"
    return {"status": status, "provider": "cloudera-ai", "application_name": name, "application_id": application.get("id"), "endpoint": endpoint,
        "message": message, "metrics": {"creator": (application.get("creator") or {}).get("username"), "updated_at": application.get("updated_at")}}




class ClouderaAIProvider(Provider):
    name = "cloudera-ai"
    label = "Cloudera AI Workbench"
    manages = True
    target = "application"
    name_fixed = True  # Workbench ties the application's subdomain to its name

    def configuration_error(self):
        s = self.settings
        missing = [n for n, v in (("FACTORY_CAI_API_URL", s.cai_api_url), ("FACTORY_CAI_API_KEY", s.cai_api_key), ("FACTORY_CAI_PROJECT_ID", s.cai_project_id)) if not v]
        return "Configure " + ", ".join(missing) + " for the cloudera-ai deployment provider" if missing else None

    def endpoint_pattern(self):
        return self.settings.endpoint_template or (f"https://{{name}}.{self.settings.cai_domain}/mcp" if self.settings.cai_domain else None)

    def deploy(self, document, deployment):
        self.ready()
        return describe(ClouderaAI(self.settings).deploy(document, deployment.get("application_id")), self.settings, document["name"])

    def api(self, deployment):
        self.ready()
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its application")
        return ClouderaAI(self.settings)

    def refresh(self, deployment):
        api = self.api(deployment)
        return describe(api.status(deployment["application_id"]), self.settings, deployment.get("application_name") or "mcp-server")

    def stop(self, deployment):
        api = self.api(deployment)
        api.stop(deployment["application_id"])
        return describe(api.status(deployment["application_id"]), self.settings, deployment.get("application_name") or "mcp-server")

    def delete(self, deployment):
        self.api(deployment).delete(deployment["application_id"])
        return {"status": "not_deployed", "message": "Workbench application deleted", "metrics": {}}
