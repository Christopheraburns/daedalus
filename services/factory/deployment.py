"""Deployment: how a published MCP server becomes a running Server.

The manifest (`document`) is provider-neutral: a name, the server and release it serves, the environment
a Server needs, and the image or script that runs it. A provider (factory.providers) turns it into a
container, a Kubernetes Deployment, a Workbench application, or a note for an operator (manual).
FACTORY_DEPLOYMENT_PROVIDER selects the provider; see factory.providers for the list.
"""
import os
import re
from pathlib import Path


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
        "image": settings.server_image, "runtime_image": settings.cai_runtime_identifier, "entrypoint": server_script(settings), "environment": environment}


def provider(settings, name=None):
    from .providers import provider as select
    return select(settings, name)


def provider_info(settings):
    """What the Builder shows about the configured provider, including why it cannot deploy yet."""
    try:
        return provider(settings).info()
    except ValueError as exc:
        return {"name": settings.deployment_provider, "label": settings.deployment_provider, "manages": False, "target": "none",
            "endpoint_pattern": None, "name_fixed_after_create": False, "configuration_error": str(exc)}


def deploy_server(server_id, release_id, server_name, settings, application_name=None, application_id=None):
    document = manifest(server_id, release_id, server_name, settings, application_name)
    return provider(settings).deploy(document, {"application_id": application_id, "application_name": application_name})


def deployment_action(action, deployment, settings):
    """refresh, stop or delete, through the provider that made the deployment (it may differ from the current one)."""
    target = provider(settings, deployment.get("provider") or settings.deployment_provider)
    return {"refresh": target.refresh, "stop": target.stop, "delete": target.delete}[action](deployment)


# Kept for callers and tests that reach the Cloudera AI client through this module.
from .providers import MANAGED  # noqa: E402
from .providers.cloudera_ai import STATUS, ClouderaAI, describe, environment_of  # noqa: E402
