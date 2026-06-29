"""
Backend-specific settings loaded from environment variables.

Separates API-layer config from ML-pipeline config (src/config/settings.py).
All values are env-overridable with the RECRUITIQ_ prefix.
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    """API server configuration — all fields have safe defaults."""

    model_config = SettingsConfigDict(
        env_prefix="RECRUITIQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Paths (relative to PROJECT_ROOT)
    project_root: Path = Path(__file__).resolve().parent.parent

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" | "text"

    # CORS
    cors_origins: list[str] = ["*"]

    # Pipeline
    max_upload_size_mb: int = 500


@lru_cache(maxsize=1)
def get_backend_settings() -> BackendSettings:
    """Singleton factory for backend settings."""
    return BackendSettings()
