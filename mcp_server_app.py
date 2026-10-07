"""Cloudera AI Workbench Application entrypoint for a generated MCP Server."""
from pathlib import Path
import runpy


def project_root():
    current = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    for candidate in (current, *current.parents):
        if (candidate / "deploy" / "workbench" / "launch_server.py").is_file():
            return candidate
    raise RuntimeError("Run mcp_server_app.py from the Daedalus project root")


runpy.run_path(str(project_root() / "deploy" / "workbench" / "launch_server.py"), run_name="__main__")
