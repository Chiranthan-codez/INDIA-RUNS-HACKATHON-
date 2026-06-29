"""Response schemas for configuration endpoints."""
from pydantic import BaseModel


class ScoringWeightsResponse(BaseModel):
    """Current scoring weight configuration."""
    title_match: float
    skill_alignment: float
    career_fit: float
    experience_band: float
    location: float
    education: float


class BehavioralMultiplierResponse(BaseModel):
    """Current behavioral multiplier configuration."""
    last_active_decay_days: float
    min_response_rate: float
    open_to_work_bonus: float
    notice_period_penalty_days: float


class ThresholdsResponse(BaseModel):
    """Current threshold configuration."""
    retrieval_top_k: int
    final_top_n: int
    honeypot_confidence: float


class ConfigResponse(BaseModel):
    """Full configuration overview."""
    status: str
    scoring_weights: ScoringWeightsResponse
    behavioral_multiplier: BehavioralMultiplierResponse
    thresholds: ThresholdsResponse


class JDRequirementsResponse(BaseModel):
    """Current JD requirements configuration."""
    status: str
    role_title: str
    min_experience_years: float
    max_experience_years: float
    experience_sweet_spot: list[float]
    target_locations: list[str]
    required_skills: list[str]
    disqualified_companies: list[str]
