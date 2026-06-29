"""Response schemas for health endpoints."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness probe response."""
    status: str = "ok"


class ReadinessDetail(BaseModel):
    """Individual readiness check result."""
    name: str
    ready: bool
    detail: str = ""


class ReadinessResponse(BaseModel):
    """Readiness probe response with per-component status."""
    status: str  # "ready" | "not_ready"
    checks: list[ReadinessDetail]
