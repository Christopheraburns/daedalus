"""Cloudera AI Workbench Application entrypoint for a generated MCP Server."""
from pathlib import Path
import runpy


runpy.run_path(str(Path(__file__).parent / "deploy" / "workbench" / "launch_server.py"), run_name="__main__")
