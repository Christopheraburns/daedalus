"""Cloudera Python application script; hosts the registry PostgreSQL for this project."""
import http.server
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import threading
import time

app_port = int(os.environ["CDSW_APP_PORT"])
password = os.getenv("FACTORY_PG_PASSWORD", "")
if len(password) < 16:
    raise RuntimeError("Set FACTORY_PG_PASSWORD (at least 16 characters) as a project environment variable")
bin_dirs = [Path(os.environ["FACTORY_PG_BIN"])] if os.getenv("FACTORY_PG_BIN") else sorted(Path("/usr/lib/postgresql").glob("*/bin"))
if not bin_dirs or not (bin_dirs[-1] / "postgres").is_file():
    raise RuntimeError("PostgreSQL server binaries not found; select a runtime built from runtime/Dockerfile")
bin_dir = bin_dirs[-1]
# Only project storage survives a restart; other applications read host_file to find this pod.
state = Path(os.getenv("FACTORY_PG_STATE_DIR", Path.home() / ".daedalus"))
data = state / "postgres"
host_file = Path(os.getenv("FACTORY_PG_HOST_FILE", state / "postgres-host"))
port = os.getenv("FACTORY_PG_PORT", "5432")
address = os.getenv("CDSW_IP_ADDRESS") or socket.gethostbyname(socket.gethostname())
local = ["-h", "/tmp", "-p", port, "-U", "factory"]

if host_file.is_file():
    previous_host, _, previous_port = host_file.read_text().strip().rpartition(":")
    try:
        socket.create_connection((previous_host, int(previous_port)), timeout=3).close()
    except (OSError, ValueError):
        pass
    else:
        raise RuntimeError(f"PostgreSQL is already serving this data directory at {previous_host}:{previous_port}; stop that application first")
# The pod that wrote this is gone; its PID can collide with a live process in this pod.
(data / "postmaster.pid").unlink(missing_ok=True)

if not (data / "PG_VERSION").is_file():
    state.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w") as pwfile:
        pwfile.write(password)
        pwfile.flush()
        subprocess.run([bin_dir / "initdb", "-D", data, "-U", "factory", "-E", "UTF8", "--locale=C.UTF-8", "--auth-local=trust", "--auth-host=scram-sha-256", f"--pwfile={pwfile.name}"], check=True)
    with (data / "pg_hba.conf").open("a") as hba:
        hba.write("host all all 0.0.0.0/0 scram-sha-256\nhost all all ::/0 scram-sha-256\n")

process = subprocess.Popen([bin_dir / "postgres", "-D", data, "-c", "listen_addresses=*", "-c", f"port={port}", "-c", "unix_socket_directories=/tmp"], start_new_session=True)
try:
    # Fast shutdown: disconnect clients and checkpoint rather than wait for them.
    signal.signal(signal.SIGTERM, lambda *_: process.send_signal(signal.SIGINT))
    deadline = time.monotonic() + 120
    while subprocess.run([bin_dir / "pg_isready", "-q", *local, "-d", "postgres"]).returncode:
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("PostgreSQL did not become ready; see the server log above")
        time.sleep(1)
    exists = subprocess.run([bin_dir / "psql", *local, "-d", "postgres", "-tAc", "SELECT 1 FROM pg_database WHERE datname = 'factory'"], check=True, capture_output=True, text=True)
    if not exists.stdout.strip():
        subprocess.run([bin_dir / "createdb", *local, "factory"], check=True)
    host_file.write_text(f"{address}:{port}\n")

    class Health(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = f"Daedalus registry PostgreSQL is running at {address}:{port}\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    health = http.server.ThreadingHTTPServer((os.getenv("FACTORY_BUILDER_BIND", "127.0.0.1"), app_port), Health)
    threading.Thread(target=health.serve_forever, daemon=True).start()
    code = process.wait()
finally:
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    host_file.unlink(missing_ok=True)
if code:
    raise RuntimeError(f"PostgreSQL exited with status {code}")
