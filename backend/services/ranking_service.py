"""
Ranking service — orchestrates the full pipeline from ingestion to ranked output.

Uses a threading lock to prevent concurrent pipeline runs (409 conflict).
Does NOT touch ML internals — only calls existing module APIs.
"""
import json
import time
import threading
import logging
from pathlib import Path
from typing import Optional

from src.config.settings import Settings
from src.ingestion.loader import CandidateLoader
from src.ingestion.candidate_model import Candidate
from src.features.extractor import FeatureExtractor
from src.integrity.honeypot_detector import HoneypotDetector
from src.scoring.scorer import Scorer
from src.scoring.reranker import Reranker
from src.reasoning.generator import ReasoningGenerator
from src.output.formatter import SubmissionFormatter

from backend.schemas.ranking import CandidateResult, RankResponse, RankResultsResponse
from backend.exceptions import (
    DataNotFoundError,
    PipelineConflictError,
    PipelineError,
)

logger = logging.getLogger("backend.services.ranking")


class RankingService:
    """
    Orchestrates: Load → Extract Features → Honeypot Check → Score → Rerank → Reason → CSV.

    Thread-safe: uses a lock to prevent concurrent runs.
    Caches the last result set in memory for fast GET retrieval.
    """

    def __init__(
        self,
        settings: Settings,
        feature_extractor: FeatureExtractor,
        scorer: Scorer,
        reranker: Reranker,
        reasoning_generator: ReasoningGenerator,
        honeypot_detector: HoneypotDetector,
        project_root: Path,
    ):
        self.settings = settings
        self.feature_extractor = feature_extractor
        self.scorer = scorer
        self.reranker = reranker
        self.reasoning_generator = reasoning_generator
        self.honeypot_detector = honeypot_detector
        self.project_root = project_root

        # Concurrency control
        self._lock = threading.Lock()
        self._running = False

        # Cached results
        self._last_results: Optional[list[CandidateResult]] = None
        self._last_stats: Optional[dict] = None

    def run_pipeline(self, top_n: int = 100, retrieval_k: int = 2000) -> RankResponse:
        """
        Executes the full ranking pipeline synchronously.

        Raises PipelineConflictError if already running.
        Raises PipelineError on irrecoverable failure.
        """
        if not self._lock.acquire(blocking=False):
            raise PipelineConflictError()

        self._running = True
        start_time = time.perf_counter()

        try:
            return self._execute(top_n, retrieval_k, start_time)
        except PipelineConflictError:
            raise
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            raise PipelineError(detail=str(e))
        finally:
            self._running = False
            self._lock.release()

    def _execute(self, top_n: int, retrieval_k: int, start_time: float) -> RankResponse:
        """Core pipeline execution — called with lock held."""

        raw_path = self.project_root / self.settings.settings.paths.raw_data
        output_path = self.project_root / self.settings.settings.paths.output

        if not raw_path.exists():
            raise PipelineError(
                detail=f"Candidate data not found at {raw_path}. Upload data first."
            )

        # Stage 1: Stream, extract features, detect honeypots
        logger.info("Stage 1: Loading candidates and extracting features...")
        loader = CandidateLoader(str(raw_path))

        all_candidates: list[Candidate] = []
        all_features: list[dict] = []
        honeypot_ids: set[str] = set()

        for i, candidate in enumerate(loader.stream()):
            features = self.feature_extractor.extract(candidate)
            all_features.append(features)
            all_candidates.append(candidate)

            if self.honeypot_detector.check(candidate):
                honeypot_ids.add(candidate.candidate_id)

            if (i + 1) % 10000 == 0:
                logger.info(f"  Processed {i + 1} candidates...")

        total_processed = len(all_candidates)
        logger.info(
            f"Stage 1 complete: {total_processed} candidates, "
            f"{len(honeypot_ids)} honeypots flagged"
        )

        # Stage 2: Score all candidates
        logger.info("Stage 2: Scoring candidates...")
        scored = []
        for candidate, features in zip(all_candidates, all_features):
            is_hp = candidate.candidate_id in honeypot_ids
            score = self.scorer.score(features, is_honeypot=is_hp)
            scored.append((candidate.candidate_id, score, features))

        # Stage 3: Rerank and select top N
        logger.info(f"Stage 3: Reranking top {top_n}...")
        self.reranker.top_n = top_n
        ranked = self.reranker.rerank(scored)

        # Stage 4: Generate reasoning for top N
        logger.info("Stage 4: Generating reasoning...")
        # Build a lookup from candidate_id to Candidate object for top N
        id_to_candidate = {c.candidate_id: c for c in all_candidates}

        results: list[CandidateResult] = []
        for entry in ranked:
            cid = entry["candidate_id"]
            candidate_obj = id_to_candidate[cid]
            reasoning = self.reasoning_generator.generate(
                candidate=candidate_obj,
                features=entry["features"],
                score=entry["score"],
                rank=entry["rank"],
            )
            results.append(CandidateResult(
                candidate_id=cid,
                rank=entry["rank"],
                score=round(entry["score"], 4),
                reasoning=reasoning,
            ))

        # Stage 5: Write submission CSV
        logger.info("Stage 5: Writing submission CSV...")
        formatter = SubmissionFormatter()
        csv_data = [
            {
                "candidate_id": r.candidate_id,
                "rank": r.rank,
                "score": r.score,
                "reasoning": r.reasoning,
            }
            for r in results
        ]
        formatter.write_csv(csv_data, str(output_path))

        # Validate
        validation_errors = formatter.validate(str(output_path))
        if validation_errors:
            logger.warning(f"Submission validation issues: {validation_errors}")

        elapsed = time.perf_counter() - start_time

        # Cache results
        self._last_results = results
        self._last_stats = {
            "pipeline_time_seconds": round(elapsed, 2),
            "total_candidates_processed": total_processed,
            "honeypots_detected": len(honeypot_ids),
        }

        logger.info(f"Pipeline complete in {elapsed:.2f}s — {len(results)} candidates ranked")

        return RankResponse(
            status="ok",
            pipeline_time_seconds=round(elapsed, 2),
            total_candidates_processed=total_processed,
            honeypots_detected=len(honeypot_ids),
            results=results,
        )

    def get_cached_results(self) -> RankResultsResponse:
        """Returns the last pipeline results from memory cache."""
        if self._last_results is None:
            raise DataNotFoundError(
                detail="No ranking results available. Run POST /api/v1/rank first."
            )
        return RankResultsResponse(
            status="ok",
            results=self._last_results,
            total=len(self._last_results),
        )

    def get_csv_path(self) -> Path:
        """Returns the path to the latest submission CSV."""
        output_path = self.project_root / self.settings.settings.paths.output
        if not output_path.exists():
            raise DataNotFoundError(
                detail="No submission CSV found. Run POST /api/v1/rank first."
            )
        return output_path

    @property
    def is_running(self) -> bool:
        return self._running
