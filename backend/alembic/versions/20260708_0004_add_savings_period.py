"""add period column to savings

Revision ID: 0004_savings_period
Revises: 0003_savings
Create Date: 2026-07-08

Per-row display/entry unit ("monthly" | "yearly"). The amount stays
annualized; this only remembers how the user entered it.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_savings_period"
down_revision = "0003_savings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "savings",
        sa.Column("period", sa.String(length=10), nullable=False, server_default="yearly"),
    )


def downgrade() -> None:
    op.drop_column("savings", "period")
