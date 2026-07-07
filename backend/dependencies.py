"""FastAPI dependencies shared across routers.

`get_session` yields one AsyncSession per request over the Database
singleton's sessionmaker. Routers stay thin — they take a session via
`Depends(get_session)` and hand it to a service; services own the logic
and are what a future MCP server will wrap directly.

The first real consumers arrive with the Household/Person models
(M0 #3). Until a database is configured, the dependency returns 503 so
DB-backed routes fail loudly rather than at query time.
"""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from persistence import database


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a per-request AsyncSession; 503 when no DB is configured."""
    if not database.enabled:
        raise HTTPException(status_code=503, detail="database not configured")
    async with database.sessionmaker()() as session:
        yield session
