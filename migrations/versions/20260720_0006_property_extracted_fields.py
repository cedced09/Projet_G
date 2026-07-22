"""Add extracted listing fields to properties.

Revision ID: 20260720_0006
Revises: 20260720_0005
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_0006"
down_revision: str | None = "20260720_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("room_count", sa.Integer(), nullable=True))
    op.add_column("properties", sa.Column("has_pool", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("properties", "has_pool")
    op.drop_column("properties", "room_count")
