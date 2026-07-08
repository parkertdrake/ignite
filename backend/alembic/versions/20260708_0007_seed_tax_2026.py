"""seed 2026 tax data (federal + WA + IL)

Revision ID: 0007_seed_tax_2026
Revises: 0006_seed_tax_2025
Create Date: 2026-07-08

2026 MFJ tax year (IRS Rev. Proc. 2025-32 inflation adjustments). Federal
brackets + standard deduction + FICA, Washington (no income tax), Illinois
(flat 4.95%). Verify against official tables before relying on them.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_seed_tax_2026"
down_revision = "0006_seed_tax_2025"
branch_labels = None
depends_on = None

YEAR = 2026
MFJ = "mfj"

# 2026 federal MFJ marginal brackets (taxable income floor, rate).
FEDERAL_BRACKETS = [
    (0, 0.10),
    (24800, 0.12),
    (100800, 0.22),
    (211100, 0.24),
    (402500, 0.32),
    (511150, 0.35),
    (767050, 0.37),
]
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
    op.bulk_insert(brackets, bracket_rows)

    op.bulk_insert(params, [
        # Federal: 2026 MFJ standard deduction $32,200. SS wage base 2026 =
        # $184,500 @ 6.2%; Medicare 1.45% + additional 0.9% over $250k (MFJ).
        {"year": YEAR, "jurisdiction": "federal", "filing_status": MFJ,
         "standard_deduction": 32200, "personal_exemption": 0,
         "ss_wage_base": 184500, "ss_rate": 0.062,
         "medicare_rate": 0.0145, "medicare_addl_rate": 0.009,
         "medicare_addl_threshold": 250000},
        {"year": YEAR, "jurisdiction": "WA", "filing_status": MFJ,
         "standard_deduction": 0, "personal_exemption": 0,
         "ss_wage_base": None, "ss_rate": None, "medicare_rate": None,
         "medicare_addl_rate": None, "medicare_addl_threshold": None},
        # Illinois 2026 personal exemption ~$2,850 per earner (verify).
        {"year": YEAR, "jurisdiction": "IL", "filing_status": MFJ,
         "standard_deduction": 0, "personal_exemption": 2850,
         "ss_wage_base": None, "ss_rate": None, "medicare_rate": None,
         "medicare_addl_rate": None, "medicare_addl_threshold": None},
    ])


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM tax_brackets WHERE year = :year"), {"year": YEAR})
    bind.execute(sa.text("DELETE FROM tax_params WHERE year = :year"), {"year": YEAR})
