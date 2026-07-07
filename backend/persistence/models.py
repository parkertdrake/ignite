"""SQLAlchemy models for ignite.

Models subclass `Base`; alembic/env.py points `target_metadata` at
`Base.metadata`. Schema is kept portable across Postgres (prod) and
SQLite (local dev): plain string columns rather than DB-level enums,
and `CURRENT_TIMESTAMP` server defaults that both dialects understand.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
