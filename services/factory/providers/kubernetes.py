"""One Deployment and Service per MCP server through the Kubernetes API.

Runs in-cluster by default (service account token, CA and namespace from the pod), or against
FACTORY_K8S_API_URL with FACTORY_K8S_TOKEN. The Builder's service account needs get/list/create/patch/delete
on deployments (apps) and services in its namespace; see deploy/kubernetes/builder.yaml.
"""
import json
from pathlib import Path

import httpx

from . import SERVER_PORT, Provider, server_environment

TRANSPORT = None  # tests inject an httpx.MockTransport here
SERVICE_ACCOUNT = Path("/var/run/secrets/kubernetes.io/serviceaccount")
LABELS = {"app.kubernetes.io/managed-by": "daedalus", "app.kubernetes.io/component": "mcp-server"}
LABEL_SERVER = "daedalus.io/server-id"


def read(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""


class Kubernetes(Provider):
    name = "kubernetes"
    label = "Kubernetes"
    manages = True
    target = "deployment"

    @property
    def namespace(self):
        return self.settings.k8s_namespace or read(SERVICE_ACCOUNT / "namespace") or "default"

    @property
    def token(self):
        return self.settings.k8s_token or read(SERVICE_ACCOUNT / "token")

    def configuration_error(self):
        if not self.settings.server_image:
            return "Set FACTORY_SERVER_IMAGE to the Daedalus image that Server pods run"
        if not self.token:
            return "Set FACTORY_K8S_TOKEN, or run the Builder in a pod with a service account"
        return None

    def endpoint_pattern(self):
        return self.settings.endpoint_template or f"http://{{name}}.{self.namespace}.svc:{SERVER_PORT}/mcp"

    def client(self):
        s = self.settings
        verify = False if s.k8s_insecure else (s.k8s_ca_file or (str(SERVICE_ACCOUNT / "ca.crt") if (SERVICE_ACCOUNT / "ca.crt").is_file() else True))
        return httpx.Client(base_url=(s.k8s_api_url or "https://kubernetes.default.svc").rstrip("/"), headers={"Authorization": f"Bearer {self.token}"},
            verify=verify, transport=TRANSPORT, timeout=60, trust_env=False)

    def api(self, method, path, allow_missing=False, **kwargs):
        with self.client() as client:
            response = client.request(method, path, **kwargs)
        if response.status_code == 404 and allow_missing:
            return None
        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text)
            except ValueError:
                detail = response.text
            raise ValueError(f"Kubernetes returned {response.status_code} for {method} {path.split('?')[0]}: {str(detail)[:300]}")
        return response.json() if response.content else {}

    def deployments(self):
        return f"/apis/apps/v1/namespaces/{self.namespace}/deployments"

    def services(self):
        return f"/api/v1/namespaces/{self.namespace}/services"

    def get_deployment(self, name):
        return self.api("GET", f"{self.deployments()}/{name}", allow_missing=True) if name else None

    def find(self, server_id):
        found = self.api("GET", self.deployments(), params={"labelSelector": f"{LABEL_SERVER}={server_id}"}).get("items", [])
        return found[0] if found else None

    def bodies(self, name, document):
        s = self.settings
        labels = {**LABELS, LABEL_SERVER: document["server_id"], "app.kubernetes.io/name": name}
        environment = server_environment(document)
        environment.setdefault("FACTORY_PUBLIC_MCP_URL", self.endpoint(name, namespace=self.namespace))
        container = {"name": "server", "image": s.server_image, "args": ["server"], "ports": [{"name": "mcp", "containerPort": SERVER_PORT}],
            "env": [{"name": k, "value": v} for k, v in sorted(environment.items())],
            "readinessProbe": {"tcpSocket": {"port": SERVER_PORT}, "periodSeconds": 5, "failureThreshold": 24},
            "resources": {"requests": {"cpu": s.k8s_cpu, "memory": s.k8s_memory}, "limits": {"cpu": s.k8s_cpu, "memory": s.k8s_memory}},
            "securityContext": {"runAsNonRoot": True, "allowPrivilegeEscalation": False}}
        pod = {"metadata": {"labels": labels, "annotations": {"daedalus.io/release-id": document["release_id"]}},
            "spec": {"containers": [container], **({"imagePullSecrets": [{"name": s.k8s_image_pull_secret}]} if s.k8s_image_pull_secret else {})}}
        deployment = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": name, "namespace": self.namespace, "labels": labels},
            "spec": {"replicas": 1, "strategy": {"type": "Recreate"}, "selector": {"matchLabels": {"app.kubernetes.io/name": name}}, "template": pod}}
        service = {"apiVersion": "v1", "kind": "Service", "metadata": {"name": name, "namespace": self.namespace, "labels": labels},
            "spec": {"selector": {"app.kubernetes.io/name": name}, "ports": [{"name": "mcp", "port": SERVER_PORT, "targetPort": SERVER_PORT}]}}
        return deployment, service

    def deploy(self, document, deployment):
        self.ready()
        existing = self.get_deployment(deployment.get("application_id")) or self.find(document["server_id"])
        name = existing["metadata"]["name"] if existing else document["name"]
        adopted = bool(existing) and name != deployment.get("application_id")
        body, service = self.bodies(name, document)
        if existing:
            self.api("PATCH", f"{self.deployments()}/{name}", content=json.dumps(body), headers={"Content-Type": "application/merge-patch+json"})
        else:
            self.api("POST", self.deployments(), json=body)
        if self.api("GET", f"{self.services()}/{name}", allow_missing=True) is None:
            self.api("POST", self.services(), json=service)
        return self.describe(self.get_deployment(name), adopted)

    def describe(self, item, adopted=False):
        name = item["metadata"]["name"]
        spec, status = item.get("spec", {}), item.get("status", {})
        desired, ready = spec.get("replicas", 1), status.get("readyReplicas", 0)
        conditions = {c.get("type"): c for c in status.get("conditions", [])}
        progressing = conditions.get("Progressing", {})
        if desired == 0:
            state = "stopped"
        elif ready >= desired:
            state = "running"
        elif progressing.get("status") == "False" and progressing.get("reason") == "ProgressDeadlineExceeded":
            state = "failed"
        else:
            state = "provisioning"
        detail = f"; {progressing['message']}" if state == "failed" and progressing.get("message") else ""
        message = ("Adopted the Deployment that already served this server; " if adopted else "") + f"Deployment {name}: {ready}/{desired} ready{detail}"
        image = next((c.get("image") for c in spec.get("template", {}).get("spec", {}).get("containers", [])), None)
        metrics = {"namespace": self.namespace, "image": image, "ready_replicas": ready, "replicas": desired, "generation": status.get("observedGeneration")}
        return self.result(state, name, message, name, self.endpoint(name, namespace=self.namespace), metrics)

    def refresh(self, deployment):
        item = self.get_deployment(deployment.get("application_id"))
        if item is None:
            return {"status": "not_deployed", "message": "Deployment no longer exists", "metrics": {}}
        return self.describe(item)

    def stop(self, deployment):
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its Deployment")
        self.api("PATCH", f"{self.deployments()}/{deployment['application_id']}", content=json.dumps({"spec": {"replicas": 0}}), headers={"Content-Type": "application/merge-patch+json"})
        return self.refresh(deployment)

    def delete(self, deployment):
        if not deployment.get("application_id"):
            raise ValueError("Deploy the server before managing its Deployment")
        name = deployment["application_id"]
        self.api("DELETE", f"{self.deployments()}/{name}", allow_missing=True, json={"propagationPolicy": "Foreground"})
        self.api("DELETE", f"{self.services()}/{name}", allow_missing=True)
        return {"status": "not_deployed", "message": "Deployment and Service deleted", "metrics": {}}
