"""
Integrity Module — Honeypot and trap candidate detection.

Responsibilities:
- Detect chronological anomalies (work duration > company age)
- Detect skill inflation (expert proficiency + 0 months duration)
- Detect title-skill mismatch (non-tech title + all AI skills)
- Detect impossible overlaps (concurrent full-time roles)
- Flag candidates with confidence scores

Boundary contract:
- Exposes: HoneypotDetector.check(Candidate) -> HoneypotResult
- Exposes: HoneypotDetector.check_batch(list) -> dict
- Depends on: ingestion/candidate_model
"""
