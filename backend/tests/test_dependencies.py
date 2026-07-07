"""Tests for the get_session dependency and the Database session path.

These use asyncio.run (no pytest-asyncio dependency) and an in-memory
aiosqlite database so the persistence layer is exercised without a real
Postgres.
"""
import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from dependencies import get_session
from persistence.db import Database


def test_session_roundtrip_with_sqlite():
    """Database.sessionmaker() yields a working AsyncSession."""
    database = Database(url="sqlite+aiosqlite:///:memory:")

    async def run():
        async with database.sessionmaker()() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        await database.dispose()

    asyncio.run(run())


def test_get_session_raises_503_when_disabled():
    """With no DATABASE_URL configured, get_session fails loudly (503)."""

    async def run():
        generator = get_session()
        with pytest.raises(HTTPException) as excinfo:
            await generator.__anext__()
        assert excinfo.value.status_code == 503

    asyncio.run(run())
