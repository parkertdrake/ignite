"""create tax tables and budget tax config

Revision ID: 0005_tax_tables
Revises: 0004_savings_period
Create Date: 2026-07-08

Adds `tax_brackets` + `tax_params` (per-year reference data for the computed
Taxes panel) and the per-budget tax config columns (tax_year / state /
filing_status). Data is seeded in the following migration (0006).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_tax_tables"
down_revision = "0004_savings_period"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_brackets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, index=True),
        sa.Column("jurisdiction", sa.String(length=12), nullable=False, index=True),
        sa.Column("filing_status", sa.String(length=10), nullable=False),
        sa.Column("lower_bound", sa.Numeric(12, 2), nullable=False),
        sa.Column("rate", sa.Numeric(6, 5), nullable=False),
    )
    op.create_table(
        "tax_params",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, index=True),
        sa.Column("jurisdiction", sa.String(length=12), nullable=False, index=True),
        sa.Column("filing_status", sa.String(length=10), nullable=False),
        sa.Column("standard_deduction", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("personal_exemption", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ss_wage_base", sa.Numeric(12, 2), nullable=True),
        sa.Column("ss_rate", sa.Numeric(6, 5), nullable=True),
        sa.Column("medicare_rate", sa.Numeric(6, 5), nullable=True),
        sa.Column("medicare_addl_rate", sa.Numeric(6, 5), nullable=True),
        sa.Column("medicare_addl_threshold", sa.Numeric(12, 2), nullable=True),
    )

    op.add_column("budgets", sa.Column("tax_year", sa.Integer(), nullable=True))
    op.add_column("budgets", sa.Column("state", sa.String(length=2), nullable=True))
    op.add_column(
        "budgets",
        sa.Column("filing_status", sa.String(length=10), nullable=False, server_default="mfj"),
    )


def downgrade() -> None:
    op.drop_column("budgets", "filing_status")
    op.drop_column("budgets", "state")
    op.drop_column("budgets", "tax_year")
    op.drop_table("tax_params")
    op.drop_table("tax_brackets")
