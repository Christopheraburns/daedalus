"""Run during image build and in a Workbench session, without network services."""

import importlib
import json
import os
import subprocess
import sys
from importlib.metadata import version


def main():
    assert sys.version_info[:2] == (3, 12), sys.version
    assert sys.prefix == "/opt/mcp-factory/venv", sys.prefix
    assert os.getuid() == 8536, "Run as the Cloudera cdsw user"
    modules = (
        "fastapi", "uvicorn", "pydantic", "pydantic_settings", "httpx",
        "yaml", "jsonschema", "sqlalchemy", "alembic", "psycopg",
        "jwt", "cryptography", "mcp", "pytest", "pytest_asyncio",
        "opentelemetry.sdk", "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    )
    for module in modules:
        importlib.import_module(module)

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    commands = {
        "agentgateway": ["agentgateway", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "ruff": ["/opt/mcp-factory/venv/bin/ruff", "--version"],
    }
    result = {"python": sys.version.split()[0], "mcp_sdk": version("mcp")}
    for name, command in commands.items():
        result[name] = subprocess.check_output(command, text=True, timeout=30).strip()
    print(json.dumps({"runtime_smoke_check": "passed", "versions": result}, indent=2))


if __name__ == "__main__":
    main()
