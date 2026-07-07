"""SQLAlchemy models for ignite.

Models subclass `Base`; alembic/env.py points `target_metadata` at
`Base.metadata`. Schema is kept portable across Postgres (prod) and
SQLite (local dev): plain string columns rather than DB-level enums,
and `CURRENT_TIMESTAMP` server defaults that both dialects understand.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, text
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
