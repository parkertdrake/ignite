"""SQLAlchemy models for ignite.

Models subclass `Base`; alembic/env.py points `target_metadata` at
`Base.metadata`. Schema is kept portable across Postgres (prod) and
SQLite (local dev): plain string columns rather than DB-level enums,
and `CURRENT_TIMESTAMP` server defaults that both dialects understand.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Budget lifecycle states. Stored as a string (not a DB enum) for
# Postgres/SQLite parity; "archived" arrives with M1 #8.
BUDGET_STATUS_ACTIVE = "active"
BUDGET_STATUS_INACTIVE = "inactive"


class Base(DeclarativeBase):
    pass


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=BUDGET_STATUS_INACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    # Tax config drives the computed Taxes panel. `tax_year` selects which
    # seeded bracket set to use (null → latest available); `state` is the
    # state jurisdiction code (null → federal-only); filing status is fixed
    # to MFJ for now but stored so the engine stays general.
    tax_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    filing_status: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="mfj"
    )
    # Optional manual add-on to the computed taxes (annual $). Folded into the
    # tax total everywhere; the Taxes panel surfaces it separately as a hint.
    tax_override_annual: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )

    earnings: Mapped[list["Earning"]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )


class Earning(Base):
    """A single person's gross salaried income within a budget.

    Top of the trickle-down flow (green). `person` is a free-text label
    for now; it normalizes to a Person row when the household model lands
    (M0 #3). Amount is annual gross; the summary divides by 12.
    """

    __tablename__ = "earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person: Mapped[str] = mapped_column(String(120), nullable=False)
    gross_annual: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )

    budget: Mapped["Budget"] = relationship(back_populates="earnings")


class Saving(Base):
    """A savings contribution within a budget: who, which account, how much
    per year. `pretax` splits the trickle-down into the pre-tax panel
    (401k/HSA, before Taxes) and the post-tax Savings panel — one table,
    matching the sheet's "Pre-Tax?" column. Amount is annual (the summary
    divides by 12), mirroring earnings.
    """

    __tablename__ = "savings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person: Mapped[str] = mapped_column(String(120), nullable=False)
    account: Mapped[str] = mapped_column(String(120), nullable=False)
    amount_annual: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    # Display/entry unit the user chose ("monthly" | "yearly"); the amount
    # is always stored annualized, so this is only a presentation hint.
    period: Mapped[str] = mapped_column(String(10), nullable=False, server_default="yearly")
    pretax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# Filing statuses. Only MFJ is used in v1, but stored on brackets/params so
# the schema can hold single/MFS/HoH later without a migration.
FILING_MFJ = "mfj"

# Jurisdiction code for the federal bracket set. States use their 2-letter
# postal code (e.g. "WA", "IL").
JURISDICTION_FEDERAL = "federal"


class TaxBracket(Base):
    """One marginal bracket of a progressive schedule: everything earned at
    or above `lower_bound` (up to the next bracket's floor) is taxed at
    `rate`. Rows are reference data seeded per (year, jurisdiction, filing
    status); a flat-tax state (e.g. IL) is a single bracket at lower_bound 0.
    A jurisdiction with no bracket rows is treated as zero income tax (WA).
    """

    __tablename__ = "tax_brackets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    filing_status: Mapped[str] = mapped_column(String(10), nullable=False)
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)


class TaxParams(Base):
    """Non-bracket tax parameters for a (year, jurisdiction, filing status):
    the standard deduction, a per-person personal exemption (states like IL
    use this instead of a standard deduction), and the FICA payroll params
    (federal only — null on state rows). A row's existence is also what makes
    a jurisdiction appear in the state dropdown, even at zero tax (WA).
    """

    __tablename__ = "tax_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    filing_status: Mapped[str] = mapped_column(String(10), nullable=False)
    # Return-level deduction (federal MFJ standard deduction).
    standard_deduction: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    # Per-earner exemption, multiplied by the number of earners (IL-style).
    personal_exemption: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    # FICA (federal rows only; null elsewhere). SS caps at the wage base per
    # person; the additional Medicare rate applies above the MFJ threshold.
    ss_wage_base: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ss_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)
    medicare_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)
    medicare_addl_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)
    medicare_addl_threshold: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )


# How an expense is funded (drives the future Levers paycheck split):
# a single person owns it, or it's shared and split by the division %.
# "Fixed" = large/predictable (rent) → shared checking; "variable" = smaller
# take-turns spend (dinners) → each person's personal checking.
PAYER_INDIVIDUAL = "individual"
PAYER_JOINT_FIXED = "joint_fixed"
PAYER_JOINT_VARIABLE = "joint_variable"


class Category(Base):
    """A spending category, scoped to a budget (copied on clone). Topical
    only (Car, Food, Home) — independent of how the expense is paid. Name is
    unique within a budget; created inline from the expense category dropdown.
    """

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("budget_id", "name", name="uq_category_budget_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class Expense(Base):
    """A single spending line within a budget: what, how much, which category,
    and how it's funded. `payer_type` is individual / joint_fixed /
    joint_variable; `payer_person` names the owner only when individual.
    Amount is stored annualized (like earnings/savings); the summary and the
    category rollup divide by 12.
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_annual: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    # Display/entry unit ("monthly" | "yearly"); amount stays annualized.
    period: Mapped[str] = mapped_column(String(10), nullable=False, server_default="yearly")
    # Nullable so a row can be uncategorized; SET NULL if the category is removed.
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payer_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=PAYER_JOINT_VARIABLE
    )
    payer_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
