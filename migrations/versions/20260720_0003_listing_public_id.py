"""Add human-readable listing identifier.

Revision ID: 20260720_0003
Revises: 20260720_0002
Create Date: 2026-07-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_0003"
down_revision: str | None = "20260720_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("public_id", sa.String(length=20), nullable=True))
    op.execute(
        "UPDATE listings SET public_id = 'ANN-' || upper(substr(replace(id::text, '-', ''), 1, 8))"
    )
    op.alter_column("listings", "public_id", existing_type=sa.String(length=20), nullable=False)
    op.create_unique_constraint("uq_listings_public_id", "listings", ["public_id"])


def downgrade() -> None:
    op.drop_constraint("uq_listings_public_id", "listings", type_="unique")
    op.drop_column("listings", "public_id")
