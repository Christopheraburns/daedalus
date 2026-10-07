import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from factory.api import create_app
from factory.db import Base, Deployment, Layout, Server, database
from factory.settings import SERVER_ID, Settings


@pytest.fixture
def registry(monkeypatch):
    """A unique PostgreSQL schema per test; never clears the development registry."""
    original_url = os.environ["DATABASE_URL"]
    monkeypatch.setenv("FACTORY_AUTH_MODE", "development-token")
    admin = create_engine(original_url)
    schema = "test_" + uuid.uuid4().hex
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    test_url = original_url + f"?options=-csearch_path%3D{schema}"
    monkeypatch.setenv("DATABASE_URL", test_url)
    settings = Settings()
    engine, sessions = database(test_url)
    Base.metadata.create_all(engine)
    with sessions.begin() as session:
        session.add(Server(id=SERVER_ID))
        session.flush()
        session.add(Layout(server_id=SERVER_ID))
        session.add(Deployment(server_id=SERVER_ID))
    try:
        with TestClient(create_app(settings)) as client:
            client.headers["Authorization"] = "Bearer " + os.environ["FACTORY_ADMINISTRATOR_TOKEN"]
            yield client, sessions, settings
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def add_tool(client, name="get_item", method="GET", path="/inventory/items/{item_id}"):
    response = client.post("/api/connections", json={"name": "Inventory", "base_url": "http://mock-api:8080"})
    assert response.status_code == 201, response.text
    connection = response.json()
    response = client.post("/api/tools", json={"name": name, "description": "Look up current inventory.", "connection_id": connection["id"], "method": method, "path": path,
        "effect": "write" if method == "POST" else "read", "parameters": [{"name": "item_id", "location": "path", "required": True, "type": "string"}] if "{" in path else [],
        "body_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"], "additionalProperties": False} if method == "POST" else None})
    assert response.status_code == 201, response.text
    return response.json(), connection


def spec(tool):
    return {k: v for k, v in tool.items() if k not in {"id", "revision", "validated", "tested", "test_summary", "published"}}
