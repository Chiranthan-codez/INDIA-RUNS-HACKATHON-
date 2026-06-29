"""
Upload endpoints — candidate JSONL file upload and validation.

- POST /api/v1/upload/candidates → upload, validate, persist
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends

from backend.config import get_backend_settings, BackendSettings
from backend.schemas.upload import UploadResponse
from backend.services.upload_service import UploadService
from backend.exceptions import ValidationError

logger = logging.getLogger("backend.api.upload")
router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])


@router.post(
    "/candidates",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload candidate JSONL",
    description=(
        "Accepts a JSONL file where each line is a candidate JSON record. "
        "Validates each line against the Candidate schema, persists valid records, "
        "and returns a detailed validation report."
    ),
)
async def upload_candidates(
    file: UploadFile = File(..., description="JSONL file with candidate records"),
    settings: BackendSettings = Depends(get_backend_settings),
):
    # Size guard
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.max_upload_size_mb:
        raise ValidationError(
            detail=f"File size ({size_mb:.1f}MB) exceeds limit ({settings.max_upload_size_mb}MB)."
        )

    logger.info(f"Received upload: {file.filename} ({size_mb:.1f}MB)")

    raw_data_dir = settings.project_root / "data" / "raw"
    service = UploadService(raw_data_dir)
    result = service.process_upload(content, file.filename or "candidates.jsonl")

    return result
