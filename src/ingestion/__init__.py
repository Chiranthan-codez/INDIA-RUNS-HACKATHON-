"""
Ingestion Module — Data loading and candidate model definitions.

Responsibilities:
- Stream or batch-load candidates from JSONL/GZ files
- Define Pydantic data models for Candidate, Profile, CareerEntry, etc.
- Validate raw data against the candidate schema

Boundary contract:
- Exposes: CandidateLoader.stream() / .load_all()
- Exposes: Candidate, Profile, CareerEntry, Skill, RedrobSignals models
- Depends on: config/settings (for paths)
"""
