"""Email alert ingestion.

Revision ID: 20260720_0002
Revises: 20260717_0001
Create Date: 2026-07-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("listings", "property_id", existing_type=sa.UUID(), nullable=True)
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("items_seen", sa.Integer(), nullable=False),
        sa.Column("items_created", sa.Integer(), nullable=False),
        sa.Column("items_updated", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.alter_column("listings", "property_id", existing_type=sa.UUID(), nullable=False)
