"""Initial registry, draft, release, canvas, and audit records."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("servers", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("revision", sa.Integer, nullable=False), sa.Column("desired_release_id", sa.String(36)), sa.Column("active_release_id", sa.String(36)), sa.Column("runtime", sa.JSON, nullable=False))
    op.create_table("connections", sa.Column("id", sa.String(36), primary_key=True), sa.Column("revision", sa.Integer, nullable=False), sa.Column("spec", sa.JSON, nullable=False))
    op.create_table("tools", sa.Column("id", sa.String(36), primary_key=True), sa.Column("server_id", sa.String(36), sa.ForeignKey("servers.id"), nullable=False), sa.Column("connection_id", sa.String(36), sa.ForeignKey("connections.id"), nullable=False), sa.Column("revision", sa.Integer, nullable=False), sa.Column("spec", sa.JSON, nullable=False), sa.Column("tested_fingerprint", sa.String(64)), sa.Column("validated_fingerprint", sa.String(64)), sa.Column("test_summary", sa.JSON))
    op.create_table("layouts", sa.Column("server_id", sa.String(36), sa.ForeignKey("servers.id"), primary_key=True), sa.Column("revision", sa.Integer, nullable=False), sa.Column("positions", sa.JSON, nullable=False))
    op.create_table("releases", sa.Column("id", sa.String(36), primary_key=True), sa.Column("server_id", sa.String(36), sa.ForeignKey("servers.id"), nullable=False), sa.Column("parent_id", sa.String(36)), sa.Column("checksum", sa.String(64), nullable=False), sa.Column("bundle", sa.JSON, nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("error", sa.Text), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_by", sa.String(80), nullable=False))
    op.create_table("audit_events", sa.Column("id", sa.String(36), primary_key=True), sa.Column("actor", sa.String(80), nullable=False), sa.Column("action", sa.String(60), nullable=False), sa.Column("target_id", sa.String(36), nullable=False), sa.Column("details", sa.JSON, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    for table in ("audit_events", "releases", "layouts", "tools", "connections", "servers"):
        op.drop_table(table)
