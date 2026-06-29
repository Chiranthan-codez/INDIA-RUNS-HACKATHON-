"""
Ranking endpoints — trigger pipeline, retrieve results, download CSV.

- POST /api/v1/rank            → execute full ranking pipeline
- GET  /api/v1/rank/results    → retrieve cached ranked results as JSON
- GET  /api/v1/rank/results/csv → download submission CSV file
"""
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.dependencies import (
    get_ml_settings,
    get_feature_extractor,
    get_scorer,
    get_reranker,
    get_reasoning_generator,
    get_honeypot_detector,
)
from backend.config import get_backend_settings, BackendSettings
from backend.schemas.ranking import RankRequest, RankResponse, RankResultsResponse
from backend.services.ranking_service import RankingService
from src.config.settings import Settings
from src.features.extractor import FeatureExtractor
from src.scoring.scorer import Scorer
from src.scoring.reranker import Reranker
from src.reasoning.generator import ReasoningGenerator
from src.integrity.honeypot_detector import HoneypotDetector

logger = logging.getLogger("backend.api.ranking")
router = APIRouter(prefix="/api/v1/rank", tags=["Ranking"])

# Module-level singleton for the ranking service (needs to share state for lock + cache)
_ranking_service: RankingService | None = None


def get_ranking_service(
    ml_settings: Settings = Depends(get_ml_settings),
    feature_extractor: FeatureExtractor = Depends(get_feature_extractor),
    scorer: Scorer = Depends(get_scorer),
    reranker: Reranker = Depends(get_reranker),
    reasoning_generator: ReasoningGenerator = Depends(get_reasoning_generator),
    honeypot_detector: HoneypotDetector = Depends(get_honeypot_detector),
    backend_settings: BackendSettings = Depends(get_backend_settings),
) -> RankingService:
    """
    Lazy-initializes a module-level singleton RankingService.
    Uses Depends() for all ML modules but ensures only one service instance exists
    (to share the threading lock and result cache).
    """
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService(
            settings=ml_settings,
            feature_extractor=feature_extractor,
            scorer=scorer,
            reranker=reranker,
            reasoning_generator=reasoning_generator,
            honeypot_detector=honeypot_detector,
            project_root=backend_settings.project_root,
        )
    return _ranking_service


@router.post(
    "",
    response_model=RankResponse,
    summary="Execute ranking pipeline",
    description=(
        "Triggers the full candidate ranking pipeline: "
        "load → extract features → detect honeypots → score → rerank → reason → CSV. "
        "Returns the top-N results with scores and reasoning."
    ),
)
async def run_ranking(
    request: RankRequest = RankRequest(),
    service: RankingService = Depends(get_ranking_service),
):
    logger.info(f"Ranking pipeline triggered (top_n={request.top_n}, k={request.retrieval_k})")
    result = service.run_pipeline(top_n=request.top_n, retrieval_k=request.retrieval_k)
    return result


@router.get(
    "/results",
    response_model=RankResultsResponse,
    summary="Retrieve cached ranking results",
    description="Returns the latest ranking results from memory. Returns 404 if no pipeline has been run.",
)
async def get_results(
    service: RankingService = Depends(get_ranking_service),
):
    return service.get_cached_results()


@router.get(
    "/results/csv",
    summary="Download submission CSV",
    description="Returns the latest submission CSV file. Returns 404 if no pipeline has been run.",
    response_class=FileResponse,
)
async def download_csv(
    service: RankingService = Depends(get_ranking_service),
):
    csv_path = service.get_csv_path()
    return FileResponse(
        path=str(csv_path),
        filename="submission.csv",
        media_type="text/csv",
    )
