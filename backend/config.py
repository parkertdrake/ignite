"""Environment-driven settings for the ignite backend.

All overrides flow through env vars. In-cluster the Helm chart injects
DATABASE_URL via envFrom on the bundled postgres secret; laptop dev
without a local Postgres simply runs with database_url empty, and the
DB-backed features become no-ops.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000

    # Postgres connection URL (postgresql+asyncpg://...). Empty → the
    # backend runs without a database: startup skips the alembic upgrade
    # and /api/db/health reports "disabled". Helm populates this from the
    # ignite-postgres secret.
    database_url: str = ""

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=None, case_sensitive=False)
