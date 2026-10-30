"""No platform: Deploy records what to create and the operator creates it by hand."""
from . import Provider

MESSAGE = ("Manual mode: no application was created. Create it with the values below, or set FACTORY_DEPLOYMENT_PROVIDER "
    "to docker, kubernetes or cloudera-ai on the Builder so Deploy creates and manages it.")
RECORDED = "Recorded locally; in manual mode, manage the server where it runs yourself."


class Manual(Provider):
    name = "manual"
    label = "Manual"

    def deploy(self, document, deployment):
        manifest = {key: document[key] for key in ("name", "subdomain", "entrypoint", "runtime_image", "image", "environment")}
        return self.result("ready_to_deploy", document["name"], MESSAGE, metrics={"manifest": manifest})

    def refresh(self, deployment):
        return {"status": deployment["status"], "message": RECORDED, "metrics": deployment.get("metrics", {})}

    def stop(self, deployment):
        return {"status": "stopped", "message": RECORDED, "metrics": deployment.get("metrics", {})}

    def delete(self, deployment):
        return {"status": "not_deployed", "message": RECORDED, "metrics": deployment.get("metrics", {})}
