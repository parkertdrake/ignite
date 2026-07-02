"""Postgres persistence for ignite.

No tables yet — budgets, holdings, and simulation models will hang off
`Base` and get their own Alembic migrations. This package wires the
async engine and the migration machinery so those can land later.
"""

from persistence.db import Database, database
from persistence.models import Base

__all__ = ["Base", "Database", "database"]
