"""Cloudera Python application script; serves the built UI and management API."""
import collections
import os
from pathlib import Path
import signal
import subprocess
import threading

root = Path(__file__).resolve().parents[2]
python = os.getenv("MCP_FACTORY_PYTHON", "/opt/mcp-factory/venv/bin/python")


def supervise(command, name, log_name, stop_timeout):
    """Run the child, relay its output into the Workbench application log and a file in project
    storage, and on failure raise with the last lines so the cause is visible without a terminal."""
    log_dir = Path(os.getenv("FACTORY_LOG_DIR", Path.home() / ".daedalus" / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{log_name}.log"
    if log_path.exists():
        log_path.replace(log_dir / f"{log_name}.previous.log")
    tail = collections.deque(maxlen=40)
    environment = {**os.environ, "PYTHONPATH": str(root / "services"), "PYTHONUNBUFFERED": "1"}
    process = subprocess.Popen(command, cwd=root, env=environment, start_new_session=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)

    def relay():
        with log_path.open("w") as log:
            for line in process.stdout:
                tail.append(line.rstrip())
                log.write(line)
                log.flush()
                print(line, end="", flush=True)

    reader = threading.Thread(target=relay, daemon=True)
    reader.start()
    try:
        signal.signal(signal.SIGTERM, lambda *_: os.killpg(process.pid, signal.SIGTERM))
        code = process.wait()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=stop_timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        reader.join(timeout=5)
    if code:
        raise RuntimeError(f"{name} exited with status {code}. Last output (full log: {log_path}):\n" + "\n".join(tail))


port = os.environ["CDSW_APP_PORT"]
if not (root / "apps/builder-ui/dist/index.html").is_file():
    raise RuntimeError("Build the UI first: cd apps/builder-ui && npm ci && npm run build")
supervise([python, "-m", "uvicorn", "factory.api:create_app", "--factory", "--host", os.getenv("FACTORY_BUILDER_BIND", "127.0.0.1"), "--port", port, "--no-access-log"], "Builder", "builder", 15)
