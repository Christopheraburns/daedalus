"""Tool packs move from project-storage files into the registry: project packs, seed enablement, inspection cache."""
from alembic import op
import sqlalchemy as sa

revision = "0006_packs"
down_revision = "0005_connection_checks"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("packs",
        sa.Column("name", sa.String(30), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("forked_from_digest", sa.String(64), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_by", sa.String(80), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("pack_settings",
        sa.Column("name", sa.String(30), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_by", sa.String(80), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("pack_inspections",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))


def downgrade():
    op.drop_table("pack_inspections")
    op.drop_table("pack_settings")
    op.drop_table("packs")
