import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER_ID = "85d30f87-b285-4d17-a89e-84bac6ac37bc"
MODERN = "2026-07-28"
LEGACY = "2025-11-25"


def database_url():
    """The registry connection string. Platform adapters (deploy/workbench) derive it when the platform hides it."""
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    raise RuntimeError("Set DATABASE_URL (postgresql+psycopg://user:password@host:port/database)")


@dataclass
class Settings:
    database_url: str = field(default_factory=database_url)
    auth_mode: str = field(default_factory=lambda: os.getenv("FACTORY_AUTH_MODE", ""))
    allowed_origins: list[str] = field(default_factory=lambda: os.getenv("FACTORY_ALLOWED_API_ORIGINS", "").split(","))
    # Browsers send Origin without a trailing slash; tolerate one (and spaces) in the setting.
    browser_origins: list[str] = field(default_factory=lambda: [origin.strip().rstrip("/") for origin in os.getenv("FACTORY_BROWSER_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")])
    gateway_token: str = field(default_factory=lambda: os.environ["FACTORY_MCP_TOKEN"])
    gateway_binary: str = field(default_factory=lambda: os.getenv("FACTORY_GATEWAY_BINARY", "/opt/mcp-factory/bin/agentgateway"))
    gateway_host: str = field(default_factory=lambda: os.getenv("FACTORY_GATEWAY_BIND", "127.0.0.1"))
    gateway_port: int = field(default_factory=lambda: int(os.getenv("FACTORY_GATEWAY_PORT", "8081")))
    state_dir: Path = field(default_factory=lambda: Path(os.getenv("FACTORY_STATE_DIR", "/tmp/daedalus-server")))
    public_mcp_url: str = field(default_factory=lambda: os.getenv("FACTORY_PUBLIC_MCP_URL", "http://localhost:8081/mcp"))
    ui_dir: Path = field(default_factory=lambda: ROOT / "apps/builder-ui/dist")
    server_id: str = field(default_factory=lambda: os.getenv("FACTORY_SERVER_ID", SERVER_ID))
    deployed_release_id: str = field(default_factory=lambda: os.getenv("FACTORY_DEPLOYED_RELEASE_ID", ""))
    deployment_provider: str = field(default_factory=lambda: os.getenv("FACTORY_DEPLOYMENT_PROVIDER", "manual"))
    # Seed packs switched on for this installation; an administrator's toggle in the registry overrides this per pack.
    packs_enabled: list[str] = field(default_factory=lambda: [n.strip() for n in os.getenv("FACTORY_PACKS_ENABLED", "").split(",") if n.strip()])
    cloudera_api_base_url: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_API_BASE_URL", ""))
    cloudera_project_id: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_PROJECT_ID", ""))
    cloudera_api_token: str = field(default_factory=lambda: os.getenv("FACTORY_CLOUDERA_API_TOKEN", ""))
    # cloudera-ai deployment provider. Inside Workbench, deploy/workbench/workbench_env.py fills these from CDSW_*.
    cai_domain: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_DOMAIN", ""))
    cai_api_url: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_API_URL") or (f"https://{os.environ['FACTORY_CAI_DOMAIN']}" if os.getenv("FACTORY_CAI_DOMAIN") else ""))
    cai_api_key: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_API_KEY", ""))
    cai_project_id: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_PROJECT_ID", ""))
    cai_runtime_identifier: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_RUNTIME_IDENTIFIER", ""))
    cai_home: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_HOME", ""))  # the Workbench project root that application script paths are relative to
    cai_cpu: float = field(default_factory=lambda: float(os.getenv("FACTORY_CAI_CPU", "1")))
    cai_memory: float = field(default_factory=lambda: float(os.getenv("FACTORY_CAI_MEMORY", "2")))
    # Workbench runs application scripts relative to the project root; the repository may sit in a subfolder.
    cai_script: str = field(default_factory=lambda: os.getenv("FACTORY_CAI_SCRIPT", ""))
    cai_bypass_auth: bool = field(default_factory=lambda: os.getenv("FACTORY_CAI_BYPASS_AUTH", "false").lower() == "true")
    # docker and kubernetes deployment providers: the image Server containers run, and how clients reach them.
    server_image: str = field(default_factory=lambda: os.getenv("FACTORY_SERVER_IMAGE", os.getenv("FACTORY_IMAGE", "")))
    endpoint_template: str = field(default_factory=lambda: os.getenv("FACTORY_ENDPOINT_TEMPLATE", ""))  # e.g. https://{name}.mcp.example.com/mcp
    docker_host: str = field(default_factory=lambda: os.getenv("FACTORY_DOCKER_HOST", "unix:///var/run/docker.sock"))
    docker_network: str = field(default_factory=lambda: os.getenv("FACTORY_DOCKER_NETWORK", ""))
    docker_publish: bool = field(default_factory=lambda: os.getenv("FACTORY_DOCKER_PUBLISH", "true").lower() == "true")
    docker_host_name: str = field(default_factory=lambda: os.getenv("FACTORY_DOCKER_HOST_NAME", "localhost"))
    k8s_api_url: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_API_URL", ""))
    k8s_token: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_TOKEN", ""))
    k8s_ca_file: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_CA_FILE", ""))
    k8s_insecure: bool = field(default_factory=lambda: os.getenv("FACTORY_K8S_INSECURE", "false").lower() == "true")
    k8s_namespace: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_NAMESPACE", ""))
    k8s_cpu: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_CPU", "500m"))
    k8s_memory: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_MEMORY", "1Gi"))
    k8s_image_pull_secret: str = field(default_factory=lambda: os.getenv("FACTORY_K8S_IMAGE_PULL_SECRET", ""))
    # Caller identity: when an issuer is set, the public MCP port requires a JWT from it (Knox), the
    # verified subject becomes the caller for tools, and Daedalus's own probes use a loopback port.
    jwt_issuer: str = field(default_factory=lambda: os.getenv("FACTORY_JWT_ISSUER", ""))
    jwt_audience: str = field(default_factory=lambda: os.getenv("FACTORY_JWT_AUDIENCE", ""))
    jwt_jwks_file: str = field(default_factory=lambda: os.getenv("FACTORY_JWT_JWKS_FILE", ""))
    probe_port: int = field(default_factory=lambda: int(os.getenv("FACTORY_PROBE_PORT", "15001")))

    def jwt(self):
        if not self.jwt_issuer:
            return None
        return {"issuer": self.jwt_issuer, "audiences": [self.jwt_audience] if self.jwt_audience else None, "jwks": {"file": self.jwt_jwks_file}}

    def verify_url(self):
        """Where the controller verifies the live catalog with its own token."""
        return f"http://127.0.0.1:{self.probe_port if self.jwt_issuer else self.gateway_port}/mcp"

    def __post_init__(self):
        if self.jwt_issuer and not Path(self.jwt_jwks_file).is_file():
            raise ValueError("FACTORY_JWT_JWKS_FILE must point to the issuer's JWKS file when FACTORY_JWT_ISSUER is set")
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
