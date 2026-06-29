"""
Custom exception hierarchy for the RecruitIQ API.

Each exception maps to a specific HTTP status code and produces a consistent
JSON error envelope: { "status": "error", "error": { "type": ..., "detail": ... } }
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("backend.exceptions")


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class RecruitIQError(Exception):
    """Base exception for all RecruitIQ backend errors."""
    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(self, detail: str = "An internal error occurred."):
        self.detail = detail
        super().__init__(detail)


class DataNotFoundError(RecruitIQError):
    """Raised when requested data does not exist (e.g., results before ranking)."""
    status_code = 404
    error_type = "data_not_found"

    def __init__(self, detail: str = "Requested data not found."):
        super().__init__(detail)


class ValidationError(RecruitIQError):
    """Raised when uploaded data fails schema validation."""
    status_code = 422
    error_type = "validation_error"

    def __init__(self, detail: str = "Data validation failed.", errors: list | None = None):
        self.errors = errors or []
        super().__init__(detail)


class PipelineConflictError(RecruitIQError):
    """Raised when a ranking pipeline is triggered while one is already running."""
    status_code = 409
    error_type = "pipeline_conflict"

    def __init__(self, detail: str = "A ranking pipeline is already in progress."):
        super().__init__(detail)


class PipelineError(RecruitIQError):
    """Raised when the ML pipeline fails irrecoverably."""
    status_code = 500
    error_type = "pipeline_error"

    def __init__(self, detail: str = "The ranking pipeline encountered an error."):
        super().__init__(detail)


class ConfigError(RecruitIQError):
    """Raised when YAML configuration is missing or corrupt."""
    status_code = 500
    error_type = "config_error"

    def __init__(self, detail: str = "Configuration error."):
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Exception handlers (registered on the FastAPI app)
# ---------------------------------------------------------------------------

def _build_error_response(exc: RecruitIQError) -> JSONResponse:
    """Builds a consistent JSON error envelope."""
    body = {
        "status": "error",
        "error": {
            "type": exc.error_type,
            "detail": exc.detail,
        },
    }
    # Attach validation errors list if present
    if isinstance(exc, ValidationError) and exc.errors:
        body["error"]["validation_errors"] = exc.errors

    return JSONResponse(status_code=exc.status_code, content=body)


async def recruitiq_exception_handler(request: Request, exc: RecruitIQError) -> JSONResponse:
    logger.warning(f"{exc.error_type}: {exc.detail}")
    return _build_error_response(exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "type": "internal_error",
                "detail": "An unexpected error occurred.",
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers all custom exception handlers on the FastAPI app instance."""
    app.add_exception_handler(RecruitIQError, recruitiq_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
