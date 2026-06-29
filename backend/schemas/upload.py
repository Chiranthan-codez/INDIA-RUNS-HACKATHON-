"""Request/Response schemas for upload endpoints."""
from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response after processing a candidate JSONL upload."""
    status: str  # "ok" | "partial" | "error"
    total_lines: int
    valid_records: int
    invalid_records: int
    errors: list[str]  # First N validation error messages
    file_path: str
