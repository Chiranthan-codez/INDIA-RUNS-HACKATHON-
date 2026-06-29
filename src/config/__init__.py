"""
Config Module — Configuration loading and validation.

Responsibilities:
- Load settings.yaml and jd_requirements.yaml
- Validate all config values via Pydantic models
- Provide a single Settings object to all other modules

Boundary contract:
- Exposes: Settings.load(path) -> Settings
- Depends on: nothing in src/
"""
