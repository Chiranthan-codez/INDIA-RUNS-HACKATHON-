import yaml
from pathlib import Path
from typing import List, Tuple, Dict
from pydantic import BaseModel, Field

# ============================================================================
# settings.yaml Models
# ============================================================================

class ScoringWeights(BaseModel):
    title_match: float
    skill_alignment: float
    career_fit: float
    experience_band: float
    location: float
    education: float

class BehavioralMultiplier(BaseModel):
    last_active_decay_days: float
    min_response_rate: float
    open_to_work_bonus: float
    notice_period_penalty_days: float

class Thresholds(BaseModel):
    retrieval_top_k: int
    final_top_n: int
    honeypot_confidence: float

class Paths(BaseModel):
    raw_data: str
    features: str
    honeypot_flags: str
    index: str
    output: str

class ProgramSettings(BaseModel):
    scoring_weights: ScoringWeights
    behavioral_multiplier: BehavioralMultiplier
    thresholds: Thresholds
    paths: Paths


# ============================================================================
# jd_requirements.yaml Models
# ============================================================================

class Disqualifiers(BaseModel):
    services_companies: List[str]
    academic_only: bool
    langchain_only: bool

class Role(BaseModel):
    title: str
    min_experience_years: float
    max_experience_years: float
    experience_sweet_spot: Tuple[float, float]

class JDRequirements(BaseModel):
    role: Role
    target_locations: List[str]
    disqualifiers: Disqualifiers
    required_skills: List[str]


# ============================================================================
# Master Settings Orchestrator
# ============================================================================

class Settings:
    """
    Orchestrates configuration loading for RecruitIQ.
    
    Loads program settings and JD requirements from YAML files and validates
    them via Pydantic models.
    """
    def __init__(self, settings_path: Path, jd_path: Path):
        self.settings = self._load_settings(settings_path)
        self.jd = self._load_jd(jd_path)

    @staticmethod
    def _load_settings(path: Path) -> ProgramSettings:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return ProgramSettings(**data)

    @staticmethod
    def _load_jd(path: Path) -> JDRequirements:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return JDRequirements(**data)

    @classmethod
    def load_defaults(cls, project_root: Path) -> "Settings":
        """Loads config files from standard project structure path."""
        settings_path = project_root / "config" / "settings.yaml"
        jd_path = project_root / "config" / "jd_requirements.yaml"
        return cls(settings_path, jd_path)
