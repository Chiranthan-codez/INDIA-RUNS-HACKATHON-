"""Request/Response schemas for ranking endpoints."""
from pydantic import BaseModel


class CandidateResult(BaseModel):
    """A single ranked candidate in the response."""
    candidate_id: str
    rank: int
    score: float
    reasoning: str


class RankRequest(BaseModel):
    """Optional parameters for the ranking endpoint."""
    top_n: int = 100
    retrieval_k: int = 2000


class RankResponse(BaseModel):
    """Response from the ranking pipeline."""
    status: str  # "ok" | "error"
    pipeline_time_seconds: float
    total_candidates_processed: int
    honeypots_detected: int
    results: list[CandidateResult]


class RankResultsResponse(BaseModel):
    """Response for cached ranking results retrieval."""
    status: str
    results: list[CandidateResult]
    total: int
