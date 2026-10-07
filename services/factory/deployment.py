"""Deployment-provider boundary for dedicated Workbench Server applications.

The manual provider is deliberately the default: it records a deployable intent
without attempting to guess a customer's Cloudera control-plane endpoint. The
Cloudera provider calls a configured, versioned deployment bridge, allowing the
platform-specific API contract to be installed and qualified per environment.
"""
import json
import os
from urllib.request import Request, urlopen


def application_name(server_name, server_id):
    safe = "".join(c.lower() if c.isalnum() else "-" for c in server_name).strip("-")[:56] or "mcp-server"
    return f"{safe}-{server_id.split('-')[0]}"


def manifest(server_id, release_id, server_name, settings):
    return {"name": application_name(server_name, server_id), "kind": "daedalus-mcp-server", "server_id": server_id,
        "release_id": release_id, "runtime_image": os.getenv("MCP_FACTORY_RUNTIME_IMAGE", "christopheraburns/mcp-factory-runtime:0.1.1"),
        "entrypoint": "deploy/workbench/launch_server.py", "environment": {"FACTORY_SERVER_ID": server_id, "FACTORY_DEPLOYED_RELEASE_ID": release_id}}


def deploy_server(server_id, release_id, server_name, settings):
    document = manifest(server_id, release_id, server_name, settings)
    if settings.deployment_provider == "manual":
        return {"status": "ready_to_deploy", "provider": "manual", "application_name": document["name"],
            "message": "Deployment manifest is ready. Configure the Workbench deployment bridge to provision this application."}
    if settings.deployment_provider != "cloudera-bridge":
        raise ValueError("FACTORY_DEPLOYMENT_PROVIDER must be manual or cloudera-bridge")
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
        return {"status": statuses[action], "message": "Recorded locally; use the Workbench deployment bridge to apply this action.", "metrics": deployment.get("metrics", {})}
    if settings.deployment_provider != "cloudera-bridge" or not deployment.get("application_id"):
        raise ValueError("A provisioned Cloudera bridge application is required")
    body = json.dumps({"action": action}).encode()
    request = Request(settings.cloudera_api_base_url.rstrip("/") + "/v1/daedalus/applications/" + deployment["application_id"], data=body,
        headers={"Authorization": "Bearer " + settings.cloudera_api_token, "Content-Type": "application/json"}, method="PATCH")
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    return {"status": result.get("status", deployment["status"]), "message": result.get("message"), "metrics": result.get("metrics", {})}
