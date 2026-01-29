"""drop is_active column and relax eval_run uniqueness

Revision ID: c9e9337900d3
Revises: 04401bc785c8
Create Date: 2025-12-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9e9337900d3"
down_revision: Union[str, None] = "04401bc785c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    schema = "planar" if dialect_name == "postgresql" else None

    # Drop is_active column from eval_suite
    with op.batch_alter_table("eval_suite", schema=schema) as batch_op:
        batch_op.drop_index("ix_planar_eval_suite_is_active")
        batch_op.drop_column("is_active")

    # Drop unique constraint from eval_run
    with op.batch_alter_table("eval_run", schema=schema) as batch_op:
        batch_op.drop_constraint("uq_eval_run_agent_config_suite", type_="unique")


def downgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    schema = "planar" if dialect_name == "postgresql" else None

    # Restore unique constraint on eval_run
    with op.batch_alter_table("eval_run", schema=schema) as batch_op:
        batch_op.create_unique_constraint(
            "uq_eval_run_agent_config_suite",
            ["agent_name", "agent_config_id", "suite_id"],
        )

    # Restore is_active column on eval_suite
    with op.batch_alter_table("eval_suite", schema=schema) as batch_op:
        batch_op.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1")
        )
        batch_op.create_index(
            "ix_planar_eval_suite_is_active", ["is_active"], unique=False
        )
