"""Health/diagnostics logic."""
from __future__ import annotations

import logging

from sqlalchemy import text

from persistence.db import Database

logger = logging.getLogger(__name__)


async def check_database(database: Database) -> str:
    """Report DB connectivity: 'disabled' | 'connected' | 'error'."""
    if not database.enabled:
        return "disabled"
    try:
        async with database.engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return "connected"
    except Exception as error:  # noqa: BLE001 - report any failure as "error"
        logger.warning("check_database: %s", error)
        return "error"
