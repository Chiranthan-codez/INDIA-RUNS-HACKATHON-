"""
Health check endpoints — liveness and readiness probes.

- GET /health          → always 200 (liveness)
- GET /health/ready    → 200 if data exists, 503 otherwise (readiness)
"""
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, Response

from backend.config import get_backend_settings, BackendSettings
from backend.schemas.health import HealthResponse, ReadinessResponse, ReadinessDetail

logger = logging.getLogger("backend.api.health")
router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 if the server process is alive.",
)
async def health():
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Checks if required data files and config are available.",
)
async def readiness(
    settings: BackendSettings = Depends(get_backend_settings),
):
    checks: list[ReadinessDetail] = []
    all_ready = True

    # Check 1: Raw candidate data exists
    raw_data = settings.project_root / "data" / "raw" / "candidates.jsonl"
    data_exists = raw_data.exists()
    checks.append(ReadinessDetail(
        name="candidate_data",
        ready=data_exists,
        detail=str(raw_data) if data_exists else f"Not found: {raw_data}",
    ))
    if not data_exists:
        all_ready = False

    # Check 2: Config files exist
    settings_yaml = settings.project_root / "config" / "settings.yaml"
    config_exists = settings_yaml.exists()
    checks.append(ReadinessDetail(
        name="config_settings",
        ready=config_exists,
        detail=str(settings_yaml) if config_exists else f"Not found: {settings_yaml}",
    ))
    if not config_exists:
        all_ready = False

    # Check 3: JD requirements exist
    jd_yaml = settings.project_root / "config" / "jd_requirements.yaml"
    jd_exists = jd_yaml.exists()
    checks.append(ReadinessDetail(
        name="jd_requirements",
        ready=jd_exists,
        detail=str(jd_yaml) if jd_exists else f"Not found: {jd_yaml}",
    ))
    if not jd_exists:
        all_ready = False

    status = "ready" if all_ready else "not_ready"
    response = ReadinessResponse(status=status, checks=checks)

    if not all_ready:
        return Response(
            content=response.model_dump_json(),
            status_code=503,
            media_type="application/json",
        )

    return response
