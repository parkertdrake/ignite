"""Shared pytest fixtures.

`client` gives a TestClient backed by a throwaway file-based SQLite DB
with `get_session` overridden to use it. Tables are created up front via
a synchronous engine on the same file (no event-loop juggling), then the
app talks to it over aiosqlite.

`seeded_client` is the same, plus the 2025 tax reference data (federal +
WA + IL) inserted so the computed Taxes panel has brackets to work with.
Migrations don't run in tests, so tax data is absent under plain `client`
(taxes compute to 0), keeping non-tax tests unaffected.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from dependencies import get_session
from main import app
from persistence.models import Base, TaxBracket, TaxParams

# Mirrors migration 0006 so seeded tests match production reference data.
_FEDERAL_BRACKETS = [
    (0, 0.10), (23850, 0.12), (96950, 0.22), (206700, 0.24),
    (394600, 0.32), (501050, 0.35), (751600, 0.37),
]


def _seed_tax_data(sync_engine) -> None:
    with Session(sync_engine) as session:
        for lower, rate in _FEDERAL_BRACKETS:
            session.add(TaxBracket(
                year=2025, jurisdiction="federal", filing_status="mfj",
                lower_bound=lower, rate=rate,
            ))
        session.add(TaxBracket(
            year=2025, jurisdiction="IL", filing_status="mfj",
            lower_bound=0, rate=0.0495,
        ))
        session.add(TaxParams(
            year=2025, jurisdiction="federal", filing_status="mfj",
            standard_deduction=30000, personal_exemption=0,
            ss_wage_base=176100, ss_rate=0.062,
            medicare_rate=0.0145, medicare_addl_rate=0.009,
            medicare_addl_threshold=250000,
        ))
        session.add(TaxParams(
            year=2025, jurisdiction="WA", filing_status="mfj",
            standard_deduction=0, personal_exemption=0,
        ))
        session.add(TaxParams(
            year=2025, jurisdiction="IL", filing_status="mfj",
            standard_deduction=0, personal_exemption=2775,
        ))
        session.commit()


def _make_client(db_file, seed_tax: bool):
    sync_engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(sync_engine)
    if seed_tax:
        _seed_tax_data(sync_engine)
    sync_engine.dispose()

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)

    async def override_get_session():
        async with testing_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


@pytest.fixture
def client(tmp_path):
    with _make_client(tmp_path / "test.db", seed_tax=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(tmp_path):
    with _make_client(tmp_path / "test.db", seed_tax=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()
