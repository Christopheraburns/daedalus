"""Deployment providers: how a published MCP server becomes a running Server somewhere.

A provider turns a deployment *document* (the manifest: name, server, release, environment, image) into a
running Server and reports on it afterwards. Every result is a dict with the keys the registry stores:
status, provider, application_name, application_id, endpoint, message, metrics.

  manual           records intent and shows the operator what to create by hand (default)
  docker           a container per MCP server through the Docker Engine API
  kubernetes       a Deployment and Service per MCP server through the Kubernetes API
  cloudera-ai      a Cloudera AI Workbench application through the Workbench API v2
  cloudera-bridge  a customer-supplied bridge service (legacy integration point)

The services never import a platform SDK: each provider speaks its platform's HTTP API with httpx, and tests
inject an httpx.MockTransport through the module-level TRANSPORT of the provider they exercise.
"""
import os

# What a Server needs from the Builder's own environment when a provider starts one elsewhere.
PASS_THROUGH = ("DATABASE_URL", "FACTORY_MCP_TOKEN", "FACTORY_AUTH_MODE", "FACTORY_ALLOWED_API_ORIGINS",
    "FACTORY_JWT_ISSUER", "FACTORY_JWT_AUDIENCE", "FACTORY_JWT_JWKS_FILE", "FACTORY_LOG_DIR", "FACTORY_LOCK_WAIT")
SERVER_PORT = 8081


def server_environment(document, environ=None):
    """Environment for a Server the provider starts: the Builder's registry, tokens and secrets, plus the document's own."""
    environ = os.environ if environ is None else environ
    environment = {key: value for key, value in environ.items() if key in PASS_THROUGH or key.startswith("FACTORY_SECRET_")}
    environment.update(document["environment"])
    environment.setdefault("FACTORY_GATEWAY_BIND", "0.0.0.0")
    environment["FACTORY_GATEWAY_PORT"] = str(SERVER_PORT)
    return environment


class Provider:
    name = ""
    label = ""
    manages = False          # Deploy creates or updates something the provider can later stop and delete
    target = "none"          # what it creates: none | container | deployment | application
    name_fixed = False       # the platform ties something immutable (a subdomain) to the name

    def __init__(self, settings):
        self.settings = settings

    def info(self):
        """Facts the Builder shows next to Deploy; wording is the UI's, so these are values, not sentences."""
        return {"name": self.name, "label": self.label, "manages": self.manages, "target": self.target,
            "endpoint_pattern": self.endpoint_pattern(), "name_fixed_after_create": self.name_fixed, "configuration_error": self.configuration_error()}

    def configuration_error(self):
        return None

    def endpoint_pattern(self):
        """A template with {name} (and {port}, {host}, {namespace}) for the endpoint a deployment will get, or None."""
        return self.settings.endpoint_template or None

    def endpoint(self, name, port=SERVER_PORT, host="localhost", namespace=""):
        template = self.endpoint_pattern()
        return template.format(name=name, port=port, host=host, namespace=namespace) if template else None

    def ready(self):
        problem = self.configuration_error()
        if problem:
            raise ValueError(problem)

    def deploy(self, document, deployment):
        raise NotImplementedError

    def refresh(self, deployment):
        raise NotImplementedError

    def stop(self, deployment):
        raise NotImplementedError

    def delete(self, deployment):
        raise NotImplementedError

    def result(self, status, name, message, application_id=None, endpoint=None, metrics=None):
        return {"status": status, "provider": self.name, "application_name": name, "application_id": application_id, "endpoint": endpoint,
            "message": message, "metrics": metrics or {}}


def registry():
    from .cloudera_ai import ClouderaAIProvider
    from .cloudera_bridge import ClouderaBridge
    from .docker import Docker
    from .kubernetes import Kubernetes
    from .manual import Manual
    return {p.name: p for p in (Manual, Docker, Kubernetes, ClouderaAIProvider, ClouderaBridge)}


MANAGED = frozenset({"docker", "kubernetes", "cloudera-ai", "cloudera-bridge"})


def provider(settings, name=None):
    name = name or settings.deployment_provider
    classes = registry()
    if name not in classes:
        raise ValueError(f"FACTORY_DEPLOYMENT_PROVIDER must be one of {', '.join(sorted(classes))}; got {name!r}")
    return classes[name](settings)
