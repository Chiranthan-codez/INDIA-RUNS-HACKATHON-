"""
Reasoning Module — Explanation generation for ranked candidates.

Responsibilities:
- Generate a 1-2 sentence justification for why a candidate is at their assigned rank
- Incorporate specific facts from the candidate's profile (years of experience, title, matching skills)
- Contrast achievements and flags (e.g. notice period concerns, lack of product experience)
- Ensure high variance (not templated) and alignment with the candidate's rank

Boundary contract:
- Exposes: ReasoningGenerator.generate(Candidate, score, rank) -> str
- Depends on: ingestion/candidate_model
"""
