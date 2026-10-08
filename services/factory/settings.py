import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
SERVER_ID = "85d30f87-b285-4d17-a89e-84bac6ac37bc"
MODERN = "2026-07-28"
LEGACY = "2025-11-25"


def database_url():
    """DATABASE_URL, else the project PostgreSQL published by deploy/workbench/launch_postgres.py."""
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host_file = Path(os.getenv("FACTORY_PG_HOST_FILE", Path.home() / ".daedalus/postgres-host"))
    if not host_file.is_file() or not os.getenv("FACTORY_PG_PASSWORD"):
        raise RuntimeError("Set DATABASE_URL, or start the PostgreSQL application and set FACTORY_PG_PASSWORD")
    return f"postgresql+psycopg://factory:{quote(os.environ['FACTORY_PG_PASSWORD'], safe='')}@{host_file.read_text().strip()}/factory"


@dataclass
class Settings:
    database_url: str = field(default_factory=database_url)
    auth_mode: str = field(default_factory=lambda: os.getenv("FACTORY_AUTH_MODE", ""))
    allowed_origins: list[str] = field(default_factory=lambda: os.getenv("FACTORY_ALLOWED_API_ORIGINS", "").split(","))
    browser_origins: list[str] = field(default_factory=lambda: os.getenv("FACTORY_BROWSER_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","))
    gateway_token: str = field(default_factory=lambda: os.environ["FACTORY_MCP_TOKEN"])
    gateway_binary: str = field(default_factory=lambda: os.getenv("FACTORY_GATEWAY_BINARY", "/opt/mcp-factory/bin/agentgateway"))
    gateway_host: str = field(default_factory=lambda: os.getenv("FACTORY_GATEWAY_BIND", "127.0.0.1"))
    gateway_port: int = field(default_factory=lambda: int(os.getenv("CDSW_APP_PORT", os.getenv("FACTORY_GATEWAY_PORT", "8081"))))
    state_dir: Path = field(default_factory=lambda: Path(os.getenv("FACTORY_STATE_DIR", "/tmp/daedalus-server")))
    public_mcp_url: str = field(default_factory=lambda: os.getenv("FACTORY_PUBLIC_MCP_URL", "http://localhost:8081/mcp"))
    ui_dir: Path = field(default_factory=lambda: ROOT / "apps/builder-ui/dist")
    server_id: str = field(default_factory=lambda: os.getenv("FACTORY_SERVER_ID", SERVER_ID))
    deployed_release_id: str = field(default_factory=lambda: os.getenv("FACTORY_DEPLOYED_RELEASE_ID", ""))
    deployment_provider: str = field(default_factory=lambda: os.getenv("FACTORY_DEPLOYMENT_PROVIDER", "manual"))
    cloudera_api_base_url: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_API_BASE_URL", ""))
    cloudera_project_id: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_PROJECT_ID", ""))
    cloudera_api_token: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_API_TOKEN", ""))

    def __post_init__(self):
        if self.auth_mode not in {"development-token", "development-open"}:
            raise ValueError("Set FACTORY_AUTH_MODE to development-token or development-open for this evaluation build; production identity integration is not yet implemented")
        if len(self.gateway_token) < 32:
            raise ValueError("FACTORY_MCP_TOKEN must have at least 32 characters")
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("Use PostgreSQL with the psycopg driver")

    def identities(self):
        if self.auth_mode == "development-open":
            return []
        identities = []
        for role in ("administrator", "author", "publisher", "viewer"):
            token = os.getenv(f"FACTORY_{role.upper()}_TOKEN", "")
            if token:
                if len(token) < 32:
                    raise ValueError(f"{role} token must have at least 32 characters")
                identities.append((token, role))
        if not identities:
            raise ValueError("Configure at least one management token")
        if len({token for token, _ in identities}) != len(identities):
            raise ValueError("Management role tokens must be distinct")
        return identities
