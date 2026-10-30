"""A customer-supplied deployment bridge (legacy integration point): POST to create, PATCH with an action."""
import json
from urllib.request import Request, urlopen

from . import Provider


class ClouderaBridge(Provider):
    name = "cloudera-bridge"
    label = "Cloudera bridge"
    manages = True
    target = "application"

    def configuration_error(self):
        s = self.settings
        if not (s.cloudera_api_base_url and s.cloudera_project_id and s.cloudera_api_token):
            return "Configure FACTORY_CLOUDERA_API_BASE_URL, FACTORY_CLOUDERA_PROJECT_ID, and FACTORY_CLOUDERA_API_TOKEN"
        return None

    def call(self, method, path, payload):
        s = self.settings
        request = Request(s.cloudera_api_base_url.rstrip("/") + path, data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + s.cloudera_api_token, "Content-Type": "application/json"}, method=method)
        with urlopen(request, timeout=20) as response:
            return json.load(response)

    def deploy(self, document, deployment):
        self.ready()
        result = self.call("POST", "/v1/daedalus/applications", {"project_id": self.settings.cloudera_project_id, "application": document})
        return self.result(result.get("status", "provisioning"), document["name"], result.get("message"), result.get("id"), result.get("endpoint"))

    def action(self, action, deployment):
        if not deployment.get("application_id"):
            raise ValueError("A provisioned Cloudera bridge application is required")
        result = self.call("PATCH", "/v1/daedalus/applications/" + deployment["application_id"], {"action": action})
        return {"status": result.get("status", deployment["status"]), "message": result.get("message"), "metrics": result.get("metrics", {})}

    def refresh(self, deployment):
        return self.action("refresh", deployment)

    def stop(self, deployment):
        return self.action("stop", deployment)

    def delete(self, deployment):
        return self.action("delete", deployment)
