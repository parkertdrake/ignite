"""Async engine + sessionmaker for ignite.

Empty `database_url` → `enabled=False`; callers treat the DB as a
no-op. The Helm install populates the URL via envFrom on the postgres
secret; laptop dev without a local Postgres simply runs without
persistence.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import Settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, url: str) -> None:
        self._url = url
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    @property
    def url(self) -> str:
        return self._url

    def engine(self) -> AsyncEngine:
        if self._engine is None:
            if not self._url:
                raise RuntimeError("Database.engine: no database_url configured")
            logger.info("Database.engine: creating async engine")
            self._engine = create_async_engine(self._url, pool_pre_ping=True)
        return self._engine

    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            self._sessionmaker = async_sessionmaker(self.engine(), expire_on_commit=False)
        return self._sessionmaker

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None


# Production singleton — driven by Settings env vars at import time.
database = Database(url=Settings().database_url)
