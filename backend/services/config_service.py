"""
Config service — reads and serializes YAML config for API consumption.

No framework imports; pure business logic.
"""
import logging
from src.config.settings import Settings
from backend.schemas.config_schemas import (
    ConfigResponse,
    ScoringWeightsResponse,
    BehavioralMultiplierResponse,
    ThresholdsResponse,
    JDRequirementsResponse,
)

logger = logging.getLogger("backend.services.config")


class ConfigService:
    """Thin wrapper that transforms Settings objects into API response schemas."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def get_scoring_weights(self) -> ConfigResponse:
        sw = self.settings.settings.scoring_weights
        bm = self.settings.settings.behavioral_multiplier
        th = self.settings.settings.thresholds

        return ConfigResponse(
            status="ok",
            scoring_weights=ScoringWeightsResponse(
                title_match=sw.title_match,
                skill_alignment=sw.skill_alignment,
                career_fit=sw.career_fit,
                experience_band=sw.experience_band,
                location=sw.location,
                education=sw.education,
            ),
            behavioral_multiplier=BehavioralMultiplierResponse(
                last_active_decay_days=bm.last_active_decay_days,
                min_response_rate=bm.min_response_rate,
                open_to_work_bonus=bm.open_to_work_bonus,
                notice_period_penalty_days=bm.notice_period_penalty_days,
            ),
            thresholds=ThresholdsResponse(
                retrieval_top_k=th.retrieval_top_k,
                final_top_n=th.final_top_n,
                honeypot_confidence=th.honeypot_confidence,
            ),
        )

    def get_jd_requirements(self) -> JDRequirementsResponse:
        jd = self.settings.jd
        role = jd.role

        return JDRequirementsResponse(
            status="ok",
            role_title=role.title,
            min_experience_years=role.min_experience_years,
            max_experience_years=role.max_experience_years,
            experience_sweet_spot=list(role.experience_sweet_spot),
            target_locations=jd.target_locations,
            required_skills=jd.required_skills,
            disqualified_companies=jd.disqualifiers.services_companies,
        )
