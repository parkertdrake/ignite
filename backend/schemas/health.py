"""Response schemas for the health endpoints."""
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str


class ApiHealth(BaseModel):
    status: str
    service: str


class DbHealth(BaseModel):
    database: str
