"""
Dependency Injection factories for the FastAPI backend.

Each factory returns a singleton-cached instance of an ML module.
Route handlers declare these as `Depends(...)` parameters — FastAPI
resolves the dependency graph automatically.

Why @lru_cache?
  - Heavy objects (Settings, FeatureExtractor, Scorer) are expensive to init.
  - We want exactly one instance per process lifetime.
  - lru_cache(maxsize=1) gives us thread-safe singleton behavior.
"""
from functools import lru_cache
from pathlib import Path

from backend.config import BackendSettings, get_backend_settings
from src.config.settings import Settings
from src.features.extractor import FeatureExtractor
from src.scoring.scorer import Scorer
from src.scoring.reranker import Reranker
from src.reasoning.generator import ReasoningGenerator
from src.integrity.honeypot_detector import HoneypotDetector


# ---------------------------------------------------------------------------
# Core config
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_ml_settings() -> Settings:
    """Loads and caches the ML pipeline settings (YAML config)."""
    backend_cfg = get_backend_settings()
    return Settings.load_defaults(backend_cfg.project_root)


# ---------------------------------------------------------------------------
# ML module singletons
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_feature_extractor() -> FeatureExtractor:
    """Creates a singleton FeatureExtractor using the cached Settings."""
    settings = get_ml_settings()
    return FeatureExtractor(settings)


@lru_cache(maxsize=1)
def get_scorer() -> Scorer:
    """Creates a singleton Scorer with weights from config."""
    settings = get_ml_settings()
    return Scorer(
        settings.settings.scoring_weights,
        settings.settings.behavioral_multiplier,
    )


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    """Creates a singleton Reranker with top_n from config."""
    settings = get_ml_settings()
    return Reranker(top_n=settings.settings.thresholds.final_top_n)


@lru_cache(maxsize=1)
def get_reasoning_generator() -> ReasoningGenerator:
    """Creates a singleton ReasoningGenerator."""
    return ReasoningGenerator()


@lru_cache(maxsize=1)
def get_honeypot_detector() -> HoneypotDetector:
    """Creates a singleton HoneypotDetector."""
    return HoneypotDetector()
