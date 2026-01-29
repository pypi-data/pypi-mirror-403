"""Add workflow visualization table

Revision ID: f3a1b2c3d4e5
Revises: e814ae2e334b
Create Date: 2025-12-30 13:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a1b2c3d4e5"
down_revision: Union[str, None] = "e814ae2e334b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_visualization",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("workflow_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("code_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("diagram", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("llm_model", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("workflow_name"),
        schema="planar",
    )


def downgrade() -> None:
    op.drop_table("workflow_visualization", schema="planar")
