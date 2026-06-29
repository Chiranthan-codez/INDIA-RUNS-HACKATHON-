"""
Configuration endpoints — expose scoring weights and JD requirements.

- GET /api/v1/config/scoring-weights   → current scoring config
- GET /api/v1/config/jd-requirements   → current JD requirements
"""
import logging
from fastapi import APIRouter, Depends

from backend.dependencies import get_ml_settings
from backend.schemas.config_schemas import ConfigResponse, JDRequirementsResponse
from backend.services.config_service import ConfigService
from src.config.settings import Settings

logger = logging.getLogger("backend.api.config")
router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


def get_config_service(
    ml_settings: Settings = Depends(get_ml_settings),
) -> ConfigService:
    return ConfigService(ml_settings)


@router.get(
    "/scoring-weights",
    response_model=ConfigResponse,
    summary="Current scoring configuration",
    description="Returns scoring weights, behavioral multipliers, and thresholds.",
)
async def scoring_weights(
    service: ConfigService = Depends(get_config_service),
):
    return service.get_scoring_weights()


@router.get(
    "/jd-requirements",
    response_model=JDRequirementsResponse,
    summary="Current JD requirements",
    description="Returns the target role, locations, required skills, and disqualifiers.",
)
async def jd_requirements(
    service: ConfigService = Depends(get_config_service),
):
    return service.get_jd_requirements()
