from typing import List, Tuple


class Reranker:
    """
    Final reranking stage: sorts scored candidates, applies deterministic
    tiebreak (candidate_id ascending for equal scores), and selects top-N.

    Algorithm:
        1. Sort by score descending.
        2. For ties, sort by candidate_id ascending (lexicographic).
        3. Slice top N.
        4. Assign ranks 1..N.

    Complexity: O(K log K) where K = shortlisted candidates (~1000).
    Memory: O(K).
    """

    def __init__(self, top_n: int = 100):
        self.top_n = top_n

    def rerank(
        self,
        scored_candidates: List[Tuple[str, float, dict]],
    ) -> List[dict]:
        """
        Args:
            scored_candidates: List of (candidate_id, score, features_dict) tuples.

        Returns:
            List of dicts with keys: candidate_id, rank, score — top N only.
        """
        # Sort: highest score (rounded to 4 decimals) first, then candidate_id ascending for ties
        sorted_list = sorted(
            scored_candidates,
            key=lambda x: (-round(x[1], 4), x[0]),
        )

        ranked = []
        for rank, (cid, score, features) in enumerate(sorted_list[: self.top_n], start=1):
            ranked.append({
                "candidate_id": cid,
                "rank": rank,
                "score": score,
                "features": features,
            })

        return ranked
