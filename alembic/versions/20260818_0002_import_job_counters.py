"""Add inventory import counters to import jobs."""

from alembic import op
import sqlalchemy as sa

revision = "20260818_0002"
down_revision = "20260818_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("rows_processed", "new_components", "updated_components", "unchanged_components", "invalid_rows", "unmatched_rows"):
        op.add_column("import_jobs", sa.Column(name, sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    for name in ("unmatched_rows", "invalid_rows", "unchanged_components", "updated_components", "new_components", "rows_processed"):
        op.drop_column("import_jobs", name)