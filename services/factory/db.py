import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def now():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


DEFAULT_SERVER_NAME = "My MCP server"


class Server(Base):
    __tablename__ = "servers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(80), default=DEFAULT_SERVER_NAME)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    desired_release_id: Mapped[str | None] = mapped_column(String(36))
    active_release_id: Mapped[str | None] = mapped_column(String(36))
    runtime: Mapped[dict] = mapped_column(JSON, default=dict)


class Connection(Base):
    __tablename__ = "connections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict] = mapped_column(JSON)
    probe_summary: Mapped[dict | None] = mapped_column(JSON)  # last connection check
    discovered: Mapped[list | None] = mapped_column(JSON)  # mcp connections: upstream tools found by the last check


class ApiOrigin(Base):
    __tablename__ = "api_origins"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    origin: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(String(240), default="")
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Tool(Base):
    __tablename__ = "tools"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), index=True)
    connection_id: Mapped[str | None] = mapped_column(ForeignKey("connections.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    spec: Mapped[dict] = mapped_column(JSON)
    tested_fingerprint: Mapped[str | None] = mapped_column(String(64))
    validated_fingerprint: Mapped[str | None] = mapped_column(String(64))
    test_summary: Mapped[dict | None] = mapped_column(JSON)


class Layout(Base):
    __tablename__ = "layouts"
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    positions: Mapped[dict] = mapped_column(JSON, default=dict)


class Release(Base):
    __tablename__ = "releases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36))
    checksum: Mapped[str] = mapped_column(String(64))
    bundle: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_by: Mapped[str] = mapped_column(String(80))


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(60))
    target_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Deployment(Base):
    __tablename__ = "deployments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"), unique=True, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="not_deployed")
    desired_release_id: Mapped[str | None] = mapped_column(String(36))
    deployed_release_id: Mapped[str | None] = mapped_column(String(36))
    application_name: Mapped[str | None] = mapped_column(String(120))
    application_id: Mapped[str | None] = mapped_column(String(160))
    endpoint: Mapped[str | None] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(32), default="manual")
    message: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Pack(Base):
    """A project pack: code written from the Builder (or a seed pack an administrator edited, which then shadows the seed)."""
    __tablename__ = "packs"
    name: Mapped[str] = mapped_column(String(30), primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    digest: Mapped[str] = mapped_column(String(64))
    forked_from_digest: Mapped[str | None] = mapped_column(String(64))  # the seed's digest when this copy was made
    revision: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str] = mapped_column(String(80), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class PackSetting(Base):
    """Whether a seed pack is switched on; absent rows fall back to FACTORY_PACKS_ENABLED."""
    __tablename__ = "pack_settings"
    name: Mapped[str] = mapped_column(String(30), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[str] = mapped_column(String(80), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class PackInspection(Base):
    """What importing a pack's source found (tools, parameters, docstrings), cached by source digest."""
    __tablename__ = "pack_inspections"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


def database(url, application_name=None):
    # application_name shows in pg_stat_activity, so lock holders can be identified.
    engine = create_engine(url, pool_pre_ping=True, connect_args={"application_name": application_name[:63]} if application_name else {})
    return engine, sessionmaker(engine, expire_on_commit=False)


def audit(session, actor, action, target_id, **details):
    session.add(Audit(actor=actor, action=action, target_id=target_id, details=details))
