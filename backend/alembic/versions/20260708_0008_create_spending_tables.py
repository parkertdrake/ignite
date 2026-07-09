"""create categories and expenses tables

Revision ID: 0008_spending
Revises: 0007_seed_tax_2026
Create Date: 2026-07-08

Spending panel (#4/#5): per-budget categories + expense line items
(item / amount / category / payer). Payer classifies funding
(individual / joint_fixed / joint_variable) for the future Levers split.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_spending"
down_revision = "0007_seed_tax_2026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "budget_id",
            sa.Integer(),
            sa.ForeignKey("budgets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("budget_id", "name", name="uq_category_budget_name"),
    )
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "budget_id",
            sa.Integer(),
            sa.ForeignKey("budgets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("item", sa.String(length=200), nullable=False),
        sa.Column("amount_annual", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("period", sa.String(length=10), nullable=False, server_default="yearly"),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "payer_type", sa.String(length=20), nullable=False, server_default="joint_variable"
        ),
        sa.Column("payer_person", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("categories")
