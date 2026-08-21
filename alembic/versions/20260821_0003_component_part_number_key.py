"""Add loose match key to components for duplicate-safe import matching."""

import re

from alembic import op
import sqlalchemy as sa

revision = "20260821_0003"
down_revision = "20260818_0002"
branch_labels = None
depends_on = None


def _loose_key(part_number: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (part_number or "").upper())


def upgrade() -> None:
    op.add_column("components", sa.Column("part_number_key", sa.String(length=255), nullable=True))

    connection = op.get_bind()
    components = sa.table(
        "components",
        sa.column("id", sa.Integer),
        sa.column("manufacturer_part_number", sa.String),
        sa.column("part_number_key", sa.String),
    )
    rows = connection.execute(sa.select(components.c.id, components.c.manufacturer_part_number)).fetchall()
    for row_id, part_number in rows:
        connection.execute(
            components.update().where(components.c.id == row_id).values(part_number_key=_loose_key(part_number))
        )

    with op.batch_alter_table("components") as batch_op:
        batch_op.alter_column("part_number_key", existing_type=sa.String(length=255), nullable=False)
    op.create_index("ix_components_part_number_key", "components", ["part_number_key"])


def downgrade() -> None:
    op.drop_index("ix_components_part_number_key", table_name="components")
    op.drop_column("components", "part_number_key")
