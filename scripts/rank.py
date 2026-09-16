"""
rank.py — Phase 2: Scoring and final ranking (timed, must finish <5min CPU).

Loads precomputed TF-IDF index, candidate features, and honeypot flags.
Performs a coarse TF-IDF retrieval for the JD headline/summary,
then extracts fine-grained features for the shortlisted set, scores,
reranks, generates reasoning, and writes the final CSV submission.

Usage:
    python scripts/rank.py
"""
import sys
import json
import pickle
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.config.settings import Settings
from src.ingestion.loader import CandidateLoader
from src.scoring.scorer import Scorer
from src.scoring.reranker import Reranker
from src.reasoning.generator import ReasoningGenerator
from src.output.formatter import SubmissionFormatter
from src.utils.logger import get_logger
from src.utils.timer import StageTimer

logger = get_logger("rank")


def load_precomputed(paths: Settings):
    """Loads TF-IDF index, features DataFrame, and honeypot list."""
    # Load index
    with open(PROJECT_ROOT / paths.settings.paths.index, "rb") as f:
        index_data = pickle.load(f)
    vectorizer = index_data["vectorizer"]
    tfidf_matrix = index_data["matrix"]
    candidate_ids = index_data["candidate_ids"]

    # Load features (parquet)
    features_df = pd.read_parquet(PROJECT_ROOT / paths.settings.paths.features)

    # Load honeypot flags (JSON list)
    with open(PROJECT_ROOT / paths.settings.paths.honeypot_flags, "r", encoding="utf-8") as f:
        honeypot_ids = set(json.load(f))

    return vectorizer, tfidf_matrix, candidate_ids, features_df, honeypot_ids


def build_query_vector(jd_text: str, vectorizer):
    """Transforms JD text into a TF-IDF vector (sparse matrix)."""
    return vectorizer.transform([jd_text])


def coarse_retrieval(tfidf_matrix, query_vec, candidate_ids, top_k: int = 2000):
    """Returns the top_k candidate IDs based on cosine similarity.

    The matrix is large (100k x 20k). We compute similarity in a vectorized way.
    """
    sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx = np.argpartition(-sims, range(top_k))[:top_k]
    # Sort the selected indices by descending similarity
    top_idx = top_idx[np.argsort(-sims[top_idx])]
    return [candidate_ids[i] for i in top_idx], sims[top_idx]


import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="RecruitIQ Ranker")
    parser.add_argument("--candidates", type=str, help="Path to candidates.jsonl file")
    parser.add_argument("--out", type=str, help="Path to write submission.csv")
    return parser.parse_known_args()

def main():
    logger.info("=" * 60)
    logger.info("RecruitIQ Rank — Phase 2 (Scoring)")
    logger.info("=" * 60)

    args, unknown = parse_args()
    settings = Settings.load_defaults(PROJECT_ROOT)

    # Resolve paths (prioritize CLI args, fall back to settings.yaml config)
    raw_data_path = Path(args.candidates) if args.candidates else PROJECT_ROOT / settings.settings.paths.raw_data
    output_path = Path(args.out) if args.out else PROJECT_ROOT / settings.settings.paths.output

    # Load JD text (concatenate role title and required skills)
    jd_text = f"{settings.jd.role.title} " + " ".join(settings.jd.required_skills)

    with StageTimer("Load precomputed artifacts"):
        vectorizer, tfidf_matrix, candidate_ids, features_df, honeypot_ids = load_precomputed(settings)

    # Coarse retrieval using TF-IDF
    with StageTimer("Coarse TF-IDF retrieval"):
        query_vec = build_query_vector(jd_text, vectorizer)
        shortlisted_ids, sim_scores = coarse_retrieval(tfidf_matrix, query_vec, candidate_ids, top_k=2000)
        logger.info(f"Shortlisted {len(shortlisted_ids)} candidates (TF-IDF top 2000)")

    # Align features with shortlisted IDs
    with StageTimer("Extract fine-grained features for shortlist"):
        # features_df rows are in the same order as candidate_ids
        id_to_index = {cid: idx for idx, cid in enumerate(candidate_ids)}
        short_features = []
        short_is_honey = []
        for cid in shortlisted_ids:
            idx = id_to_index[cid]
            row = features_df.iloc[idx].to_dict()
            short_features.append(row)
            short_is_honey.append(cid in honeypot_ids)

    # Scoring
    scorer = Scorer(settings.settings.scoring_weights, settings.settings.behavioral_multiplier)
    with StageTimer("Composite scoring"):
        scored = []
        for cid, feats, is_hp in zip(shortlisted_ids, short_features, short_is_honey):
            score = scorer.score(feats, is_honeypot=is_hp)
            scored.append((cid, score, feats))

    # Rerank and slice top 100
    reranker = Reranker(top_n=100)
    with StageTimer("Rerank top 100"):
        ranked = reranker.rerank(scored)

    # Retrieve candidate objects for top 100 to generate reasoning
    with StageTimer("Load Candidate objects for top 100 reasoning"):
        top_100_ids = {entry["candidate_id"] for entry in ranked}
        loader = CandidateLoader(str(raw_data_path))
        candidate_lookup = {}
        for candidate in loader.stream():
            if candidate.candidate_id in top_100_ids:
                candidate_lookup[candidate.candidate_id] = candidate

    # Reasoning generation
    reasoner = ReasoningGenerator()
    for entry in ranked:
        cid = entry["candidate_id"]
        cand_obj = candidate_lookup[cid]
        entry["reasoning"] = reasoner.generate(
            cand_obj, entry["features"], entry["score"], entry["rank"]
        )

    # Write submission CSV
    formatter = SubmissionFormatter()
    with StageTimer("Write CSV output"):
        formatter.write_csv(ranked, str(output_path))
        errors = formatter.validate(str(output_path))
        if errors:
            logger.error("Submission validation failed:\n" + "\n".join(errors))
        else:
            logger.info(f"Submission CSV written and validated: {output_path}")

    logger.info("Phase 2 complete – final ranking ready for submission.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

