"""Add extracted listing fields.

Revision ID: 20260720_0005
Revises: 20260720_0004
Create Date: 2026-07-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_0005"
down_revision: str | None = "20260720_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("municipality", sa.String(length=255), nullable=True))
    op.add_column("listings", sa.Column("room_count", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("living_area_m2", sa.Numeric(12, 2), nullable=True))
    op.add_column("listings", sa.Column("land_area_m2", sa.Numeric(14, 2), nullable=True))
    op.add_column("listings", sa.Column("bedroom_count", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("has_pool", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "has_pool")
    op.drop_column("listings", "bedroom_count")
    op.drop_column("listings", "land_area_m2")
    op.drop_column("listings", "living_area_m2")
    op.drop_column("listings", "room_count")
    op.drop_column("listings", "municipality")
