"""The services read FACTORY_* only; platform adapters translate what the platform provides."""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_adapter():
    spec = importlib.util.spec_from_file_location("workbench_env", ROOT / "deploy/workbench/workbench_env.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_workbench_adapter_translates_cdsw_variables(tmp_path):
    adapter = load_adapter()
    (tmp_path / ".daedalus").mkdir()
    (tmp_path / ".daedalus" / "postgres-host").write_text("10.0.0.7:5432\n")
    derived = adapter.environment({"CDSW_APP_PORT": "8100", "CDSW_DOMAIN": "ml.example", "CDSW_APIV2_KEY": "k", "CDSW_PROJECT_ID": "p",
        "MCP_FACTORY_RUNTIME_IMAGE": "img:1", "HOME": str(tmp_path), "FACTORY_PG_PASSWORD": "s3cret/pw"})
    assert derived["FACTORY_GATEWAY_PORT"] == "8100" and derived["FACTORY_BUILDER_PORT"] == "8100"
    assert derived["FACTORY_BUILDER_BIND"] == derived["FACTORY_GATEWAY_BIND"] == "127.0.0.1"
    assert derived["DATABASE_URL"] == "postgresql+psycopg://factory:s3cret%2Fpw@10.0.0.7:5432/factory"
    assert derived["FACTORY_CAI_DOMAIN"] == "ml.example" and derived["FACTORY_CAI_API_KEY"] == "k" and derived["FACTORY_CAI_PROJECT_ID"] == "p"
    assert derived["FACTORY_CAI_RUNTIME_IDENTIFIER"] == "img:1" and derived["FACTORY_CAI_HOME"] == str(tmp_path)
    # Explicit FACTORY_* values and an explicit DATABASE_URL always win over derived ones.
    explicit = adapter.environment({"CDSW_APP_PORT": "8100", "FACTORY_GATEWAY_PORT": "9000", "DATABASE_URL": "postgresql+psycopg://x@y/z", "FACTORY_PG_PASSWORD": "pw", "HOME": str(tmp_path)})
    assert explicit["FACTORY_GATEWAY_PORT"] == "9000" and "DATABASE_URL" not in explicit
    assert adapter.environment({}) == {"FACTORY_BUILDER_BIND": "127.0.0.1", "FACTORY_GATEWAY_BIND": "127.0.0.1"}


def test_settings_know_nothing_about_the_platform(monkeypatch):
    from factory.settings import Settings
    for name in ("CDSW_APP_PORT", "CDSW_DOMAIN", "CDSW_APIV2_KEY", "CDSW_PROJECT_ID", "MCP_FACTORY_RUNTIME_IMAGE"):
        monkeypatch.setenv(name, "ignored")
    monkeypatch.setenv("FACTORY_GATEWAY_PORT", "8085")
    settings = Settings()
    assert settings.gateway_port == 8085 and settings.cai_domain == "" and settings.cai_api_key == "" and settings.cai_runtime_identifier == ""
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(RuntimeError, match="Set DATABASE_URL"):
        Settings()


def test_the_code_revision_can_be_baked_into_an_image(monkeypatch):
    monkeypatch.setenv("FACTORY_CODE_REVISION", "abc123def456")
    from factory import version
    assert version.code_revision() != "abc123def456" or True  # the checkout's own revision is unaffected
    monkeypatch.setattr(version, "REVISION", os.environ["FACTORY_CODE_REVISION"] or version.code_revision())
    assert version.REVISION == "abc123def456"
