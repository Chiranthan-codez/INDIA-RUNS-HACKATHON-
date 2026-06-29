"""
retrieval.py — Coarse candidate retrieval (Stage 1 of funnel).

Narrows the 100K candidate pool to ~1K using a fast index.
Default: TF-IDF cosine similarity (AD-4 in Architecture Doc).
Future: swappable to embedding-based retrieval.
"""
