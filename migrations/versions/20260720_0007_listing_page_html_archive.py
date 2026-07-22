"""Add listing page HTML archive metadata.

Revision ID: 20260720_0007
Revises: 20260720_0006
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_0007"
down_revision: str | None = "20260720_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("page_html_path", sa.Text(), nullable=True))
    op.add_column(
        "listings",
        sa.Column("page_html_saved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("listings", sa.Column("page_html_sha256", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "page_html_sha256")
    op.drop_column("listings", "page_html_saved_at")
    op.drop_column("listings", "page_html_path")
