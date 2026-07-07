"""Health endpoints.

  /health          liveness/readiness (hit directly on the pod)
  /api/health      same check, through the ingress /api prefix
  /api/db/health   database connectivity
"""
from fastapi import APIRouter

from persistence import database
from schemas.health import ApiHealth, DbHealth, HealthStatus
from services import health_service

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    """Liveness/readiness probe target. Hit directly on the pod."""
    return HealthStatus(status="ok")


@router.get("/api/health", response_model=ApiHealth)
def api_health() -> ApiHealth:
    """Same check, reachable through the ingress /api prefix."""
    return ApiHealth(status="ok", service="ignite-backend")


@router.get("/api/db/health", response_model=DbHealth)
async def db_health() -> DbHealth:
    """Report database connectivity (disabled when no DATABASE_URL)."""
    return DbHealth(database=await health_service.check_database(database))
