"""
Scoring Module — Core ranking engine.

Responsibilities:
- Coarse retrieval (TF-IDF/BM25 index query) to narrow 100K -> ~1K
- Composite scoring with weighted sub-scores and behavioral multiplier
- Final reranking with tiebreak logic

Boundary contract:
- Exposes: Retriever.build_index() / .query()
- Exposes: Scorer.score(features, signals) -> float
- Exposes: Reranker.rerank(scored_list, top_n) -> ranked_list
- Depends on: config/settings, features/extractor
"""
