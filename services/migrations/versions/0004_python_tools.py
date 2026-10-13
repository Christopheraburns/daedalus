"""Python pack tools may exist without a connection."""
from alembic import op
import sqlalchemy as sa

revision = "0004_python_tools"
down_revision = "0003_api_origins"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("tools", "connection_id", existing_type=sa.String(length=36), nullable=True)


def downgrade():
    op.execute("DELETE FROM tools WHERE connection_id IS NULL")
    op.alter_column("tools", "connection_id", existing_type=sa.String(length=36), nullable=False)
