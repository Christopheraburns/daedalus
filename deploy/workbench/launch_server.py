"""Cloudera Python application script; controller supervises the gateway."""
import os
from pathlib import Path
import signal
import subprocess

root = Path(__file__).resolve().parents[2]
python = os.getenv("MCP_FACTORY_PYTHON", "/opt/mcp-factory/venv/bin/python")
os.environ["CDSW_APP_PORT"]  # Required; never silently bind a default Workbench port.
if not os.getenv("FACTORY_SERVER_ID"):
    raise RuntimeError("Set FACTORY_SERVER_ID to the dedicated server workspace ID before launching this application")
environment = {**os.environ, "PYTHONPATH": str(root / "services")}
process = subprocess.Popen([python, "-m", "factory.controller"], cwd=root, env=environment, start_new_session=True)
try:
    signal.signal(signal.SIGTERM, lambda *_: os.killpg(process.pid, signal.SIGTERM))
    code = process.wait()
finally:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
if code:
    raise RuntimeError(f"Server exited with status {code}")
