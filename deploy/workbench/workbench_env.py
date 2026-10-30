"""What Cloudera AI Workbench gives an application, expressed as the FACTORY_* variables the services read.

The services know nothing about Workbench. This module is the one place that does: the launchers merge
its result into the child's environment. Explicit FACTORY_* values always win over derived ones.
"""
import os
from pathlib import Path
from urllib.parse import quote


def environment(environ=None):
    environ = os.environ if environ is None else environ
    derived = {}
    # Workbench assigns the port an application must listen on.
    if environ.get("CDSW_APP_PORT"):
        derived["FACTORY_GATEWAY_PORT"] = environ["CDSW_APP_PORT"]
        derived["FACTORY_BUILDER_PORT"] = environ["CDSW_APP_PORT"]
    # Workbench's ingress reaches the pod on loopback; nothing else should be exposed.
    derived["FACTORY_BUILDER_BIND"] = "127.0.0.1"
    derived["FACTORY_GATEWAY_BIND"] = "127.0.0.1"
    # The registry hosted by deploy/workbench/launch_postgres.py publishes its address in project storage.
    if not environ.get("DATABASE_URL") and environ.get("FACTORY_PG_PASSWORD"):
        host_file = Path(environ.get("FACTORY_PG_HOST_FILE") or Path(environ.get("HOME", str(Path.home()))) / ".daedalus" / "postgres-host")
        if host_file.is_file():
            derived["DATABASE_URL"] = f"postgresql+psycopg://factory:{quote(environ['FACTORY_PG_PASSWORD'], safe='')}@{host_file.read_text().strip()}/factory"
    # The cloudera-ai deployment provider talks to the Workbench that runs the Builder.
    for target, source in (("FACTORY_CAI_DOMAIN", "CDSW_DOMAIN"), ("FACTORY_CAI_API_KEY", "CDSW_APIV2_KEY"), ("FACTORY_CAI_PROJECT_ID", "CDSW_PROJECT_ID"),
            ("FACTORY_CAI_RUNTIME_IDENTIFIER", "MCP_FACTORY_RUNTIME_IMAGE"), ("FACTORY_CAI_HOME", "CDSW_HOME")):
        if environ.get(source):
            derived[target] = environ[source]
    if "FACTORY_CAI_HOME" not in derived and environ.get("HOME"):
        derived["FACTORY_CAI_HOME"] = environ["HOME"]
    return {**derived, **{k: v for k, v in environ.items() if k in derived}}  # explicit values win
