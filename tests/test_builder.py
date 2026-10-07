import os

import pytest

from conftest import add_tool, spec
from factory.compiler import compile_bundle, digest, validate_tool
from factory.contracts import ToolSpec


def test_authorization_and_origin(registry):
    client, _, _ = registry
    assert client.get("/api/workspace", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/workspace", headers={"Origin": "https://untrusted.example"}).status_code == 403
    viewer = {"Authorization": "Bearer " + os.environ["FACTORY_VIEWER_TOKEN"]}
    author = {"Authorization": "Bearer " + os.environ["FACTORY_AUTHOR_TOKEN"]}
    publisher = {"Authorization": "Bearer " + os.environ["FACTORY_PUBLISHER_TOKEN"]}
    assert client.get("/api/workspace", headers=viewer).status_code == 200
    assert client.post("/api/connections", headers=author, json={"name": "No", "base_url": "http://mock-api:8080"}).status_code == 403
    tool, _ = add_tool(client)
    assert client.post(f"/api/tools/{tool['id']}/test", headers={**viewer, "If-Match": "1"}, json={}).status_code == 403
    assert client.patch(f"/api/tools/{tool['id']}", headers={**publisher, "If-Match": "1"}, json=spec(tool)).status_code == 403
    assert client.post("/api/releases", headers=author, json={"revision": 3}).status_code == 403
    assert client.post("/api/connections", json={"name": "No", "base_url": "http://169.254.169.254"}).status_code == 422
    assert client.post("/api/connections", json={"name": "No", "base_url": "http://mock-api:8080@169.254.169.254"}).status_code == 422


def test_revisions_layout_and_draft_validation(registry):
    client, _, _ = registry
    tool, _ = add_tool(client)
    before = client.get("/api/workspace").json()
    response = client.put("/api/layout", headers={"If-Match": "1"}, json={"positions": {tool["id"]: {"x": 550, "y": 90}}})
    assert response.status_code == 200
    after = client.get("/api/workspace").json()
    assert before["server"]["revision"] == after["server"]["revision"]
    assert after["tools"][0]["revision"] == tool["revision"]
    assert after["layout"]["positions"][tool["id"]] == {"x": 550, "y": 90}
    assert client.put("/api/layout", headers={"If-Match": "1"}, json={"positions": {}}).status_code == 409
    assert client.patch(f"/api/tools/{tool['id']}", json=spec(tool)).status_code == 428
    changed = {**spec(tool), "description": "A revised description."}
    assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}, json=changed).status_code == 200
    assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}, json=changed).status_code == 409
    assert client.post("/api/tools", json=changed).status_code == 409
    invalid = {**changed, "path": "/missing/{parameter}"}
    assert client.patch(f"/api/tools/{tool['id']}", headers={"If-Match": "2"}, json=invalid).status_code == 200
    assert client.post(f"/api/tools/{tool['id']}/validate", headers={"If-Match": "3"}).status_code == 422
    assert client.get("/api/releases/preview").json()["problems"]


def test_compiler_is_deterministic_and_rejects_unsupported_mappings():
    conn = {"name": "Inventory", "base_url": "http://mock-api:8080", "auth_mode": "none"}
    one = ToolSpec(name="one", description="One", connection_id="c", path="/one").model_dump()
    two = ToolSpec(name="two", description="Two", connection_id="c", path="/two").model_dump()
    a = {"id": "a", "revision": 1, "spec": one}
    b = {"id": "b", "revision": 1, "spec": two}
    first = compile_bundle([a, b], {"c": conn}, [conn["base_url"]])
    second = compile_bundle([b, a], {"c": conn}, [conn["base_url"]])
    assert digest(first) == digest(second)
    assert set(first["targets"][0]["schema"]["paths"]) == {"/one", "/two"}
    hidden = compile_bundle([a, {**b, "spec": {**two, "enabled": False}}], {"c": conn}, [conn["base_url"]])
    assert set(hidden["targets"][0]["schema"]["paths"]) == {"/one"}
    for path in ["https://example.com", "//evil.example/path", "/a/../admin", "/a?redirect=http://evil.example", "/a/%2e%2e"]:
        with pytest.raises(ValueError):
            validate_tool({**one, "path": path}, conn, [conn["base_url"]])
    with pytest.raises(ValueError, match="Unsupported body schema"):
        validate_tool({**one, "method": "POST", "effect": "write", "body_schema": {"type": "object", "$ref": "https://evil.example/schema"}}, conn, [conn["base_url"]])
    for body in [{"type": "object", "properties": []}, {"type": "object", "required": "bad"}]:
        with pytest.raises(ValueError, match="Invalid body schema"):
            validate_tool({**one, "method": "POST", "effect": "write", "body_schema": body}, conn, [conn["base_url"]])


def test_write_confirmation_and_stale_test_evidence(registry):
    client, _, _ = registry
    tool, conn = add_tool(client, "create_ticket", "POST", "/tickets")
    endpoint = f"/api/tools/{tool['id']}/test"
    request = {"arguments": {"body": {"title": "Fixture test"}}}
    assert client.post(endpoint, headers={"If-Match": "1"}, json=request).status_code == 422
    result = client.post(endpoint, headers={"If-Match": "1"}, json={**request, "confirm_write": True})
    assert result.status_code == 200, result.text
    assert result.json()["success"], result.text
    assert client.get("/api/workspace").json()["tools"][0]["tested"]
    response = client.patch(f"/api/connections/{conn['id']}", headers={"If-Match": "1"}, json={"name": "Renamed", "base_url": conn["base_url"]})
    assert response.status_code == 200
    assert not client.get("/api/workspace").json()["tools"][0]["tested"]
    preview = client.get("/api/releases/preview").json()
    assert client.post("/api/releases", json={"revision": preview["revision"]}).status_code == 422


def test_request_size_and_audit_redaction(registry):
    client, _, _ = registry
    assert client.post("/api/connections", content='x' * (256 * 1024 + 1)).status_code == 413
    add_tool(client)
    response = client.get("/api/audit")
    assert response.status_code == 200
    assert {e['action'] for e in response.json()} >= {'tool.create', 'connection.create'}
    for key, value in os.environ.items():
        if key.startswith('FACTORY_') and key.endswith('_TOKEN'):
            assert value not in response.text


def test_openapi_preview_rejects_private_and_credentialed_urls(registry):
    client, _, _ = registry
    assert client.post('/api/openapi/preview', json={'url': 'http://169.254.169.254/openapi.json'}).status_code == 422
    assert client.post('/api/openapi/preview', json={'url': 'https://user:pass@example.com/openapi.json'}).status_code == 422


def test_author_can_remove_tool_and_connection(registry):
    client, _, _ = registry
    tool, connection = add_tool(client)
    assert client.delete(f"/api/connections/{connection['id']}", headers={"If-Match": "1"}).status_code == 409
    assert client.delete(f"/api/tools/{tool['id']}", headers={"If-Match": "1"}).status_code == 204
    assert client.delete(f"/api/connections/{connection['id']}", headers={"If-Match": "1"}).status_code == 204
    workspace = client.get("/api/workspace").json()
    assert not workspace["tools"]
    assert not workspace["connections"]
