"""Shared pytest fixtures.

`client` gives a TestClient backed by a throwaway file-based SQLite DB
with `get_session` overridden to use it. Tables are created up front via
a synchronous engine on the same file (no event-loop juggling), then the
app talks to it over aiosqlite.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dependencies import get_session
from main import app
from persistence.models import Base


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test.db"

    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)

    async def override_get_session():
        async with testing_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
