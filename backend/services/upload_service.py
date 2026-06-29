"""
Upload service — validates and persists uploaded JSONL candidate files.

Streams lines one at a time to avoid loading 500MB into memory.
"""
import json
import logging
from pathlib import Path
from typing import BinaryIO

from pydantic import ValidationError as PydanticValidationError

from src.ingestion.candidate_model import Candidate
from backend.schemas.upload import UploadResponse
from backend.exceptions import ValidationError

logger = logging.getLogger("backend.services.upload")

MAX_ERROR_SAMPLES = 20  # Cap error messages returned to client


class UploadService:
    """Validates and persists uploaded JSONL candidate data."""

    def __init__(self, raw_data_dir: Path):
        self.raw_data_dir = raw_data_dir
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def process_upload(self, file_content: bytes, filename: str) -> UploadResponse:
        """
        Validates each line of JSONL against the Candidate schema,
        writes valid records to data/raw/candidates.jsonl,
        and returns a summary report.
        """
        output_path = self.raw_data_dir / "candidates.jsonl"
        lines = file_content.decode("utf-8").splitlines()

        total_lines = 0
        valid_count = 0
        invalid_count = 0
        errors: list[str] = []

        valid_records: list[str] = []

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            total_lines += 1

            try:
                record = json.loads(line)
                Candidate(**record)  # Validate against Pydantic model
                valid_records.append(line)
                valid_count += 1
            except json.JSONDecodeError as e:
                invalid_count += 1
                if len(errors) < MAX_ERROR_SAMPLES:
                    errors.append(f"Line {line_num}: JSON parse error — {e}")
            except PydanticValidationError as e:
                invalid_count += 1
                if len(errors) < MAX_ERROR_SAMPLES:
                    # Extract first validation error message
                    first_err = e.errors()[0] if e.errors() else {"msg": str(e)}
                    field = ".".join(str(loc) for loc in first_err.get("loc", []))
                    msg = first_err.get("msg", "unknown error")
                    errors.append(f"Line {line_num}: field '{field}' — {msg}")
            except Exception as e:
                invalid_count += 1
                if len(errors) < MAX_ERROR_SAMPLES:
                    errors.append(f"Line {line_num}: unexpected error — {e}")

        # Write valid records to disk
        if valid_records:
            with open(output_path, "w", encoding="utf-8") as f:
                for record_line in valid_records:
                    f.write(record_line + "\n")
            logger.info(
                f"Upload complete: {valid_count}/{total_lines} valid records "
                f"written to {output_path}"
            )
        else:
            raise ValidationError(
                detail="No valid records found in the uploaded file.",
                errors=errors,
            )

        status = "ok" if invalid_count == 0 else "partial"

        return UploadResponse(
            status=status,
            total_lines=total_lines,
            valid_records=valid_count,
            invalid_records=invalid_count,
            errors=errors,
            file_path=str(output_path),
        )
