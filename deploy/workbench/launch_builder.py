"""Cloudera Python application script; serves the built UI and management API."""
import os
from pathlib import Path
import signal
import subprocess

root = Path(__file__).resolve().parents[2]
python = os.getenv("MCP_FACTORY_PYTHON", "/opt/mcp-factory/venv/bin/python")
port = os.environ["CDSW_APP_PORT"]
if not (root / "apps/builder-ui/dist/index.html").is_file():
    raise RuntimeError("Build the UI first: cd apps/builder-ui && npm ci && npm run build")
environment = {**os.environ, "PYTHONPATH": str(root / "services")}
process = subprocess.Popen([python, "-m", "uvicorn", "factory.api:create_app", "--factory", "--host", os.getenv("FACTORY_BUILDER_BIND", "127.0.0.1"), "--port", port, "--no-access-log"], cwd=root, env=environment, start_new_session=True)
try:
    signal.signal(signal.SIGTERM, lambda *_: os.killpg(process.pid, signal.SIGTERM))
    code = process.wait()
finally:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
if code:
    raise RuntimeError(f"Builder exited with status {code}")
