"""Use sequential listing public identifiers.

Revision ID: 20260720_0004
Revises: 20260720_0003
Create Date: 2026-07-20

"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260720_0004"
down_revision: str | None = "20260720_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE listings AS target
        SET public_id = 'ANN-' || lpad(ordered.row_number::text, 4, '0')
        FROM (
            SELECT id, row_number() OVER (ORDER BY created_at, id) AS row_number
            FROM listings
        ) AS ordered
        WHERE target.id = ordered.id
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE listings
        SET public_id = 'ANN-' || upper(substr(replace(id::text, '-', ''), 1, 8))
        """
    )
