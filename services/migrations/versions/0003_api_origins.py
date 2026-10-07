"""Project-scoped API origin policies."""
from alembic import op
import sqlalchemy as sa

revision = "0003_api_origins"
down_revision = "0002_multi_server_deployments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_origins",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("server_id", sa.String(length=36), sa.ForeignKey("servers.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("origin", sa.String(length=300), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_api_origins_server_id", "api_origins", ["server_id"])


def downgrade():
    op.drop_index("ix_api_origins_server_id", table_name="api_origins")
    op.drop_table("api_origins")
