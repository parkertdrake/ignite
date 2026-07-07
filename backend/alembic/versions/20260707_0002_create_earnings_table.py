"""create earnings table

Revision ID: 0002_earnings
Revises: 0001_budgets
Create Date: 2026-07-07

Per-person gross income rows hanging off a budget (trickle-down step 1).
Kept portable across Postgres and SQLite.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_earnings"
down_revision = "0001_budgets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "earnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "budget_id",
            sa.Integer(),
            sa.ForeignKey("budgets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("person", sa.String(length=120), nullable=False),
        sa.Column("gross_annual", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_earnings_budget_id", "earnings", ["budget_id"])


def downgrade() -> None:
    op.drop_index("ix_earnings_budget_id", table_name="earnings")
    op.drop_table("earnings")
