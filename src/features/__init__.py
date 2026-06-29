"""
Features Module — Feature extraction from raw candidate profiles.

Responsibilities:
- Extract numeric/categorical features from each candidate
- Sub-modules: profile, career, skill, signal features
- Orchestrated by extractor.py which combines all sub-extractors

Boundary contract:
- Exposes: FeatureExtractor.extract(Candidate) -> FeatureVector
- Exposes: FeatureExtractor.extract_batch(list[Candidate]) -> DataFrame
- Depends on: ingestion/candidate_model, config/settings
"""
