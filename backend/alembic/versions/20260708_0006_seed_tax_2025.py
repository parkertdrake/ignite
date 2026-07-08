"""seed 2025 tax data (federal + WA + IL)

Revision ID: 0006_seed_tax_2025
Revises: 0005_tax_tables
Create Date: 2026-07-08

Seeds the 2025 MFJ tax year: federal progressive brackets + FICA, Washington
(no state income tax), and Illinois (flat 4.95% with a per-person exemption).
Values are reference data — verify against official IRS / state tables before
relying on them for filing. Add later years / states as new seed migrations.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_seed_tax_2025"
down_revision = "0005_tax_tables"
branch_labels = None
depends_on = None

YEAR = 2025
MFJ = "mfj"

# 2025 federal MFJ marginal brackets (taxable income floor, rate).
FEDERAL_BRACKETS = [
    (0, 0.10),
    (23850, 0.12),
    (96950, 0.22),
    (206700, 0.24),
    (394600, 0.32),
    (501050, 0.35),
    (751600, 0.37),
]
# Illinois: flat tax from the first dollar, so a single bracket at 0.
ILLINOIS_BRACKETS = [(0, 0.0495)]


def _brackets_table() -> sa.Table:
    return sa.table(
        "tax_brackets",
        sa.column("year", sa.Integer),
        sa.column("jurisdiction", sa.String),
        sa.column("filing_status", sa.String),
        sa.column("lower_bound", sa.Numeric),
        sa.column("rate", sa.Numeric),
    )


def _params_table() -> sa.Table:
    return sa.table(
        "tax_params",
        sa.column("year", sa.Integer),
        sa.column("jurisdiction", sa.String),
        sa.column("filing_status", sa.String),
        sa.column("standard_deduction", sa.Numeric),
        sa.column("personal_exemption", sa.Numeric),
        sa.column("ss_wage_base", sa.Numeric),
        sa.column("ss_rate", sa.Numeric),
        sa.column("medicare_rate", sa.Numeric),
        sa.column("medicare_addl_rate", sa.Numeric),
        sa.column("medicare_addl_threshold", sa.Numeric),
    )


def upgrade() -> None:
    brackets = _brackets_table()
    params = _params_table()

    bracket_rows = [
        {"year": YEAR, "jurisdiction": "federal", "filing_status": MFJ,
         "lower_bound": lower, "rate": rate}
        for lower, rate in FEDERAL_BRACKETS
    ]
    bracket_rows += [
        {"year": YEAR, "jurisdiction": "IL", "filing_status": MFJ,
         "lower_bound": lower, "rate": rate}
        for lower, rate in ILLINOIS_BRACKETS
    ]
    # Washington: no brackets seeded → zero income tax.
    op.bulk_insert(brackets, bracket_rows)

    op.bulk_insert(params, [
        # Federal: 2025 MFJ standard deduction + FICA. SS wage base 2025 =
        # $176,100 @ 6.2%; Medicare 1.45% + additional 0.9% over $250k (MFJ).
        {"year": YEAR, "jurisdiction": "federal", "filing_status": MFJ,
         "standard_deduction": 30000, "personal_exemption": 0,
         "ss_wage_base": 176100, "ss_rate": 0.062,
         "medicare_rate": 0.0145, "medicare_addl_rate": 0.009,
         "medicare_addl_threshold": 250000},
        # Washington: present so it shows in the dropdown; zero everything.
        {"year": YEAR, "jurisdiction": "WA", "filing_status": MFJ,
         "standard_deduction": 0, "personal_exemption": 0,
         "ss_wage_base": None, "ss_rate": None, "medicare_rate": None,
         "medicare_addl_rate": None, "medicare_addl_threshold": None},
        # Illinois: no standard deduction; $2,775 personal exemption per earner.
        {"year": YEAR, "jurisdiction": "IL", "filing_status": MFJ,
         "standard_deduction": 0, "personal_exemption": 2775,
         "ss_wage_base": None, "ss_rate": None, "medicare_rate": None,
         "medicare_addl_rate": None, "medicare_addl_threshold": None},
    ])


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM tax_brackets WHERE year = :year"), {"year": YEAR})
    bind.execute(sa.text("DELETE FROM tax_params WHERE year = :year"), {"year": YEAR})
