"""SQLAlchemy declarative base for ignite.

No tables yet. Budgets, holdings, and simulation models will subclass
`Base` here; alembic/env.py points `target_metadata` at `Base.metadata`,
so `alembic revision --autogenerate` will pick up models added below.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
