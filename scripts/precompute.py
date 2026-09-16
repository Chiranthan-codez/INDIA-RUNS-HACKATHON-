"""
precompute.py — Phase 1: Offline precomputation (untimed).

Streams all 100K candidates, extracts features, detects honeypots,
builds the TF-IDF search index, and saves everything to disk.

Usage:
    python scripts/precompute.py
"""
import sys
import json
import pickle
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config.settings import Settings
from src.ingestion.loader import CandidateLoader
from src.features.extractor import FeatureExtractor
from src.integrity.honeypot_detector import HoneypotDetector
from src.utils.logger import get_logger
from src.utils.timer import StageTimer

logger = get_logger("precompute")


def build_candidate_text(candidate) -> str:
    """
    Builds a single text representation of a candidate for TF-IDF indexing.
    Combines headline, summary, skills, titles, and role descriptions.
    """
    parts = []
    parts.append(candidate.profile.headline or "")
    parts.append(candidate.profile.summary or "")
    parts.append(candidate.profile.current_title or "")

    for entry in candidate.career_history:
        parts.append(entry.title or "")
        parts.append(entry.description or "")

    for skill in candidate.skills:
        # Repeat skill name weighted by proficiency
        weight = {"expert": 3, "advanced": 2, "intermediate": 1, "beginner": 1}
        repeat = weight.get(skill.proficiency, 1)
        parts.extend([skill.name] * repeat)

    return " ".join(parts)


import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="RecruitIQ Precomputer")
    parser.add_argument("--candidates", type=str, help="Path to candidates.jsonl file")
    return parser.parse_known_args()

def main():
    logger.info("=" * 60)
    logger.info("RecruitIQ Precompute — Phase 1")
    logger.info("=" * 60)

    args, unknown = parse_args()
    # Load config
    settings = Settings.load_defaults(PROJECT_ROOT)
    raw_path = Path(args.candidates) if args.candidates else PROJECT_ROOT / settings.settings.paths.raw_data
    features_path = PROJECT_ROOT / settings.settings.paths.features
    honeypot_path = PROJECT_ROOT / settings.settings.paths.honeypot_flags
    index_path = PROJECT_ROOT / settings.settings.paths.index

    # Ensure output directories exist
    features_path.parent.mkdir(parents=True, exist_ok=True)
    honeypot_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize modules
    loader = CandidateLoader(str(raw_path))
    extractor = FeatureExtractor(settings)
    honeypot_detector = HoneypotDetector()

    # Storage
    all_features = []
    honeypot_ids = []
    candidate_texts = []
    candidate_ids = []

    # Stream and process
    with StageTimer("Feature extraction + Honeypot detection"):
        for i, candidate in enumerate(loader.stream()):
            # Extract features
            features = extractor.extract(candidate)
            all_features.append(features)

            # Honeypot check
            is_hp = honeypot_detector.check(candidate)
            if is_hp:
                honeypot_ids.append(candidate.candidate_id)

            # Build text for TF-IDF
            text = build_candidate_text(candidate)
            candidate_texts.append(text)
            candidate_ids.append(candidate.candidate_id)

            if (i + 1) % 10000 == 0:
                logger.info(f"  Processed {i + 1} candidates...")

    logger.info(f"Total candidates processed: {len(all_features)}")
    logger.info(f"Honeypots detected: {len(honeypot_ids)}")

    # Save features as parquet
    with StageTimer("Save features to parquet"):
        df = pd.DataFrame(all_features)
        df.to_parquet(str(features_path), index=False)
        logger.info(f"Features saved: {features_path} ({len(df)} rows, {len(df.columns)} cols)")

    # Save honeypot flags
    with StageTimer("Save honeypot flags"):
        with open(honeypot_path, "w", encoding="utf-8") as f:
            json.dump(honeypot_ids, f)
        logger.info(f"Honeypot flags saved: {honeypot_path} ({len(honeypot_ids)} flagged)")

    # Build and save TF-IDF index
    with StageTimer("Build TF-IDF index"):
        vectorizer = TfidfVectorizer(
            max_features=20000,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(candidate_texts)

        index_data = {
            "vectorizer": vectorizer,
            "matrix": tfidf_matrix,
            "candidate_ids": candidate_ids,
        }
        with open(index_path, "wb") as f:
            pickle.dump(index_data, f)
        logger.info(f"TF-IDF index saved: {index_path} (shape: {tfidf_matrix.shape})")

    logger.info("=" * 60)
    logger.info("Precompute complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
