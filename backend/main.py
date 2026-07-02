"""Ignite backend — FastAPI app.

Endpoints:
  /health          liveness/readiness (hit directly on the pod)
  /api/health      same check, through the ingress /api prefix
  /api/db/health   database connectivity
  /api/accounts    stub

On startup (when database_url is set) the app runs `alembic upgrade
head` so the schema is migrated before serving. No tables yet — the
machinery is in place for budgets, holdings, and simulation data.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config import Settings
from persistence import database

settings = Settings()
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


def _run_alembic_upgrade(database_url: str) -> None:
    """Sync `alembic upgrade head` — called from a thread on startup."""
    from alembic import command
    from alembic.config import Config

    here = Path(__file__).resolve().parent
    cfg = Config(str(here / "alembic.ini"))
    cfg.set_main_option("script_location", str(here / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    os.environ["DATABASE_URL"] = database_url
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.database_url:
        logger.info("startup: running alembic upgrade head")
        try:
            await asyncio.to_thread(_run_alembic_upgrade, settings.database_url)
        except Exception:
            logger.exception("startup: alembic upgrade failed; continuing without DB")
    yield
    await database.dispose()


app = FastAPI(title="Ignite", version="0.1.0", lifespan=lifespan)

# Dev-only convenience: the Vite dev server runs on a different origin
# than the API. In-cluster both are served from the same host via the
# ingress, so this is a no-op there.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness/readiness probe target. Hit directly on the pod."""
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    """Same check, reachable through the ingress /api prefix."""
    return {"status": "ok", "service": "ignite-backend"}


@app.get("/api/db/health")
async def db_health():
    """Report database connectivity (disabled when no DATABASE_URL)."""
    if not database.enabled:
        return {"database": "disabled"}
    try:
        async with database.engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as error:
        logger.warning("db_health: %s", error)
        return {"database": "error"}


@app.get("/api/accounts")
def list_accounts():
    """Stub endpoint — returns a placeholder account list."""
    return {
        "accounts": [
            {"id": 1, "name": "Checking", "balance": 0.0},
            {"id": 2, "name": "Savings", "balance": 0.0},
        ]
    }


def main():
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
