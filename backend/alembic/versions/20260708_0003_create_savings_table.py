"""create savings table

Revision ID: 0003_savings
Revises: 0002_earnings
Create Date: 2026-07-08

Savings contributions (person / account / monthly amount) with a pretax
flag splitting pre-tax (401k, HSA) from post-tax savings. Portable across
Postgres and SQLite.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_savings"
down_revision = "0002_earnings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "savings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "budget_id",
            sa.Integer(),
            sa.ForeignKey("budgets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("person", sa.String(length=120), nullable=False),
        sa.Column("account", sa.String(length=120), nullable=False),
        sa.Column("amount_annual", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("pretax", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_savings_budget_id", "savings", ["budget_id"])


def downgrade() -> None:
    op.drop_index("ix_savings_budget_id", table_name="savings")
    op.drop_table("savings")
