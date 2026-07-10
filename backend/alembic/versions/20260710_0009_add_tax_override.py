"""add per-budget tax override

Revision ID: 0009_tax_override
Revises: 0008_spending_tables
Create Date: 2026-07-10

Adds `budgets.tax_override_annual` — a manual add-on to the computed taxes
(annual $, default 0). Folded into the tax total everywhere; the Taxes panel
surfaces it separately in its collapsed header.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_tax_override"
down_revision = "0008_spending"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "budgets",
        sa.Column(
            "tax_override_annual",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("budgets", "tax_override_annual")
