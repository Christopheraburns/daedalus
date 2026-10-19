import os
import subprocess
import sys
import time

import pytest
from sqlalchemy import text

from factory.db import database

gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")


@gateway
def test_a_second_server_process_waits_names_the_owner_and_then_gives_up(registry, monkeypatch, tmp_path):
    _, _, settings = registry
    monkeypatch.setenv("FACTORY_STATE_DIR", str(tmp_path / "state"))
    owner_engine, _ = database(os.environ["DATABASE_URL"], "daedalus-server 85d30f87 on first-pod")
    with owner_engine.connect() as first:
        assert first.scalar(text("SELECT pg_try_advisory_lock(hashtext(current_schema()), hashtext(:s))"), {"s": settings.server_id})
        started = time.monotonic()
        second = subprocess.run([sys.executable, "-m", "factory.controller"], env={**os.environ, "FACTORY_LOCK_WAIT": "3"}, capture_output=True, text=True, timeout=60)
        assert second.returncode == 1 and time.monotonic() - started >= 3
        output = second.stdout + second.stderr
        assert "waiting up to" in output
        assert "Another Server process owns MCP server" in output and "daedalus-server 85d30f87 on first-pod" in output and "connected since" in output
    owner_engine.dispose()
