"""multi-server workspaces and deployment state

Revision ID: 0002_multi_server_deployments
Revises: 0001_registry
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_multi_server_deployments"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("connections", sa.Column("server_id", sa.String(length=36), nullable=True))
    op.execute("UPDATE connections SET server_id = '85d30f87-b285-4d17-a89e-84bac6ac37bc' WHERE server_id IS NULL")
    op.alter_column("connections", "server_id", nullable=False)
    op.create_foreign_key("fk_connections_server", "connections", "servers", ["server_id"], ["id"])
    op.create_index("ix_connections_server_id", "connections", ["server_id"])
    op.create_index("ix_tools_server_id", "tools", ["server_id"])
    op.create_index("ix_releases_server_id", "releases", ["server_id"])
    op.create_table("deployments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("server_id", sa.String(length=36), sa.ForeignKey("servers.id"), nullable=False, unique=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="not_deployed"),
        sa.Column("desired_release_id", sa.String(length=36)), sa.Column("deployed_release_id", sa.String(length=36)),
        sa.Column("application_name", sa.String(length=120)), sa.Column("application_id", sa.String(length=160)),
        sa.Column("endpoint", sa.String(length=500)), sa.Column("provider", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("message", sa.Text()), sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.execute("INSERT INTO deployments (id, server_id, revision, status, provider, metrics, updated_at) SELECT 'eb2667ce-9ff2-463b-9ba8-5e943c4be9e5', id, 1, 'not_deployed', 'manual', '{}', CURRENT_TIMESTAMP FROM servers WHERE id = '85d30f87-b285-4d17-a89e-84bac6ac37bc' AND NOT EXISTS (SELECT 1 FROM deployments WHERE deployments.server_id = servers.id)")


def downgrade():
    op.drop_table("deployments")
    op.drop_index("ix_releases_server_id", table_name="releases")
    op.drop_index("ix_tools_server_id", table_name="tools")
    op.drop_index("ix_connections_server_id", table_name="connections")
    op.drop_constraint("fk_connections_server", "connections", type_="foreignkey")
    op.drop_column("connections", "server_id")
