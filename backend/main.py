"""Ignite backend — FastAPI app assembly.

Routers live in `routers/`, business logic in `services/`, and the typed
HTTP contract in `schemas/`. The shared `get_session` dependency is in
`dependencies.py`. This module only wires the app together: lifespan,
middleware, and router registration.

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

from config import Settings
from persistence import database
from routers import accounts, budgets, health

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

app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(budgets.router)


def main():
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
