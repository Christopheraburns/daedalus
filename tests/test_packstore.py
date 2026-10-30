"""Seed packs, project packs in the registry, the inspection cache and the legacy file import."""
import os

import pytest

from factory import packs, packstore
from factory.db import Pack, PackInspection

MOCK = "http://mock-api:8080"
gateway = pytest.mark.skipif(not os.path.exists("/opt/mcp-factory/bin/agentgateway"), reason="agentgateway binary required")
ADMIN_ONLY = {"Authorization": "Bearer " + os.environ["FACTORY_AUTHOR_TOKEN"]}


def names(client):
    return [p["name"] for p in client.get("/api/packs").json()]


def test_seed_packs_ship_disabled_and_the_catalog_lists_only_what_is_enabled(registry):
    client, _, _ = registry
    assert "webhdfs_admin" in packs.seed_names() and "webhdfs_admin" not in names(client)
    seeds = client.get("/api/packs/seeds").json()
    seed = next(s for s in seeds["seeds"] if s["name"] == "webhdfs_admin")
    assert seed == {**seed, "enabled": False, "configured_by": "default", "protocol": "webhdfs", "tools": 26, "shadowed": False, "seed_updated": False, "error": None}
    assert client.get("/api/packs/webhdfs_admin").status_code == 404
    assert client.put("/api/packs/webhdfs_admin/enabled", headers=ADMIN_ONLY, json={"enabled": True}).status_code == 403
    assert client.put("/api/packs/nope/enabled", json={"enabled": True}).status_code == 404
    enabled = client.put("/api/packs/webhdfs_admin/enabled", json={"enabled": True})
    assert enabled.status_code == 200 and next(s for s in enabled.json()["seeds"] if s["name"] == "webhdfs_admin")["configured_by"] == "setting"
    assert names(client) == ["demo", "hdfs", "rest", "s3", "webhdfs_admin"]
    info = client.get("/api/packs/webhdfs_admin").json()
    assert info["origin"] == "seed" and info["editable"] and info["enabled"] and len(info["tools"]) == 26 and {t["function"] for t in info["tools"]} >= {"get_content_summary", "set_owner", "create_snapshot", "append", "concat"}
    assert "def get_content_summary" in info["source"]
    assert client.put("/api/packs/webhdfs_admin/enabled", json={"enabled": False}).status_code == 200
    assert "webhdfs_admin" not in names(client)


def test_the_environment_enables_seeds_and_a_stored_toggle_overrides_it(registry):
    client, sessions, settings = registry
    settings.packs_enabled.append("webhdfs_admin")
    assert "webhdfs_admin" in names(client)
    assert next(s for s in client.get("/api/packs/seeds").json()["seeds"] if s["name"] == "webhdfs_admin")["configured_by"] == "environment"
    assert client.put("/api/packs/webhdfs_admin/enabled", json={"enabled": False}).status_code == 200
    assert "webhdfs_admin" not in names(client)  # the registry wins over the environment, and survives a restart


def test_inspection_runs_once_per_distinct_source(registry, monkeypatch):
    client, sessions, settings = registry
    calls = []
    original = packs.inspect_source
    monkeypatch.setattr(packs, "inspect_source", lambda name, source: calls.append(name) or original(name, source))
    settings.packs_enabled.append("webhdfs_admin")
    for _ in range(3):
        client.get("/api/packs"); client.get("/api/packs/seeds"); client.get("/api/packs/webhdfs_admin")
    assert calls == ["webhdfs_admin"]
    with sessions() as session:
        assert session.get(PackInspection, packs.digest_of(packs.seed_source("webhdfs_admin"))) is not None


PROJECT = '''"""A project pack."""
from factory.packs import ToolContext, pack_tool


@pack_tool(effect="read")
def shout(ctx: ToolContext, text: str) -> dict:
    """Upper-case the text."""
    return {"text": text.upper()}
'''


def test_project_packs_live_in_the_registry_not_on_disk(registry, monkeypatch, tmp_path):
    client, sessions, settings = registry
    monkeypatch.setenv("FACTORY_PACKS_DIR", str(tmp_path / "packs"))
    saved = client.put("/api/packs/loud", json={"source": PROJECT})
    assert saved.status_code == 200 and saved.json()["origin"] == "project" and saved.json()["revision"] == 1
    assert not (tmp_path / "packs").exists()  # nothing written to project storage
    with sessions() as session:
        row = session.get(Pack, "loud")
        assert row.source.strip() == PROJECT.strip() and row.digest == packs.digest_of(row.source) and row.forked_from_digest is None
    again = client.put("/api/packs/loud", json={"source": PROJECT.replace("upper", "lower")})
    assert again.json()["revision"] == 2
    assert client.delete("/api/packs/loud").status_code == 204
    assert client.get("/api/packs/loud").status_code == 404


def test_legacy_pack_files_are_imported_once(registry, monkeypatch, tmp_path):
    client, sessions, settings = registry
    directory = tmp_path / "daedalus-packs"; directory.mkdir()
    (directory / "legacy.py").write_text(PROJECT)
    (directory / "broken.py").write_text("def nope(:\n")
    (directory / "demo.py").write_text(PROJECT)  # a built-in name is never imported
    monkeypatch.setenv("FACTORY_PACKS_DIR", str(directory))
    messages = []
    with sessions.begin() as session:
        assert packstore.import_legacy_files(session, settings, log=messages.append) == ["legacy"]
    assert any("broken.py" in m for m in messages)
    assert names(client)[-1] == "legacy" and client.get("/api/packs/legacy").json()["origin"] == "project"
    with sessions.begin() as session:
        assert packstore.import_legacy_files(session, settings, log=messages.append) == []


@gateway
def test_an_enabled_seed_serves_tools_and_editing_it_forks_a_project_copy(registry):
    client, sessions, settings = registry
    assert client.put("/api/packs/webhdfs_admin/enabled", json={"enabled": True}).status_code == 200
    assert client.post("/api/policies/origins", json={"origin": MOCK, "description": "Fixture"}).status_code == 201
    connection = client.post("/api/connections", json={"name": "HDFS", "base_url": MOCK, "protocol": "webhdfs"}).json()
    tool = client.post("/api/tools", json={"name": "summary", "description": "Space used.", "kind": "python", "pack": "webhdfs_admin", "function": "get_content_summary", "connection_id": connection["id"]})
    assert tool.status_code == 201, tool.text
    tool = tool.json()
    result = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"path": "/data"}}}).json()
    assert result["success"], result
    assert result["result"]["structuredContent"]["files"] == 1 and result["result"]["structuredContent"]["bytes"] > 0
    # A seed in use cannot be switched off; the release snapshots its source like any other pack.
    assert client.put("/api/packs/webhdfs_admin/enabled", json={"enabled": False}).status_code == 409
    preview = client.get("/api/releases/preview").json()
    assert preview["problems"] == [], preview
    published = client.post("/api/releases", json={"revision": preview["revision"]})
    assert published.status_code == 202, published.text
    with sessions() as session:
        from factory.db import Release
        release = session.get(Release, published.json()["id"])
        assert release.bundle["pack_sources"] == {"webhdfs_admin": packs.seed_source("webhdfs_admin")}
    # Editing the seed forks it: a project pack shadows the seed, and the tool must be tested again.
    forked = client.put("/api/packs/webhdfs_admin", json={"source": packs.seed_source("webhdfs_admin").replace('"files": summary.get("fileCount", 0)', '"files": summary.get("fileCount", 0) + 100')})
    assert forked.status_code == 200, forked.text
    assert forked.json()["origin"] == "project" and forked.json()["forked_from_seed"] and forked.json()["seed_updated"] is False
    assert names(client) == ["demo", "hdfs", "rest", "s3", "webhdfs_admin"]
    seed = next(s for s in client.get("/api/packs/seeds").json()["seeds"] if s["name"] == "webhdfs_admin")
    assert seed["shadowed"] and seed["enabled"]
    assert not client.get("/api/workspace").json()["tools"][0]["tested"]
    retest = client.post(f"/api/tools/{tool['id']}/test", headers={"If-Match": "1"}, json={"arguments": {"body": {"path": "/data"}}}).json()
    assert retest["result"]["structuredContent"]["files"] == 101
    # Deleting the project copy falls back to the seed, even while tools use the pack.
    assert client.delete("/api/packs/webhdfs_admin").status_code == 204
    assert client.get("/api/packs/webhdfs_admin").json()["origin"] == "seed"
    assert not client.get("/api/workspace").json()["tools"][0]["tested"]
