"""add IDPGroup.num_members

Revision ID: 4ca7ba90cdbc
Revises: f3a1b2c3d4e5
Create Date: 2026-01-06 06:26:33.213287

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ca7ba90cdbc"
down_revision: Union[str, None] = "f3a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # we can't pass `schema=True` for SQLite because we're running `alter_column`
    # on an existing table created in a previous migration.
    _alter = (
        op.batch_alter_table("assignment")
        if is_sqlite
        else op.batch_alter_table("assignment", schema="planar")
    )
    with _alter as batch_op:
        batch_op.alter_column("assignee_id", existing_type=sa.UUID(), nullable=False)

    with op.batch_alter_table("idp_group", schema="planar") as batch_op:
        batch_op.add_column(sa.Column("num_members", sa.Integer(), nullable=False))

    # Create concurrent index only for PostgreSQL
    if not is_sqlite:
        op.execute(sa.text("COMMIT"))
        op.execute(
            sa.text(
                "CREATE INDEX CONCURRENTLY ix_pending_tasks ON planar.human_task (id) WHERE status = 'PENDING'"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # Drop num_members column
    if is_sqlite:
        with op.batch_alter_table("idp_group") as batch_op:
            batch_op.drop_column("num_members")
    else:
        with op.batch_alter_table("idp_group", schema="planar") as batch_op:
            batch_op.drop_column("num_members")

    # Make assignee_id nullable again
    if is_sqlite:
        with op.batch_alter_table("assignment") as batch_op:
            batch_op.alter_column("assignee_id", existing_type=sa.UUID(), nullable=True)
    else:
        with op.batch_alter_table("assignment", schema="planar") as batch_op:
            batch_op.alter_column("assignee_id", existing_type=sa.UUID(), nullable=True)

    # Drop concurrent index only for PostgreSQL
    if not is_sqlite:
        op.execute(sa.text("COMMIT"))
        op.execute(sa.text("DROP INDEX CONCURRENTLY planar.ix_pending_tasks"))
