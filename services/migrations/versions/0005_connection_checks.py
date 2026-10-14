"""Connection checks (probe results) and discovered upstream MCP tools."""
from alembic import op
import sqlalchemy as sa

revision = "0005_connection_checks"
down_revision = "0004_python_tools"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("connections", sa.Column("probe_summary", sa.JSON(), nullable=True))
    op.add_column("connections", sa.Column("discovered", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("connections", "discovered")
    op.drop_column("connections", "probe_summary")
