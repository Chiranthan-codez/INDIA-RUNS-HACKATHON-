"""
RecruitIQ API — FastAPI Application Factory.

Entry point: uvicorn backend.main:app --host 0.0.0.0 --port 8000

Architecture:
    - Lifespan context manager for startup/shutdown hooks
    - CORS middleware (permissive for hackathon)
    - Custom middleware (request ID, timing)
    - Exception handlers
    - Master router with all API endpoints
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_backend_settings
from backend.logging_config import setup_logging
from backend.middleware import RequestIdMiddleware, RequestTimingMiddleware
from backend.exceptions import register_exception_handlers
from backend.api.router import master_router

logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown lifecycle hooks.

    Startup:
      - Configure structured logging
      - Log server config
    Shutdown:
      - Cleanup resources (currently none)
    """
    settings = get_backend_settings()
    setup_logging(level=settings.log_level, fmt=settings.log_format)

    logger.info("=" * 60)
    logger.info("RecruitIQ API starting up")
    logger.info(f"  Project root : {settings.project_root}")
    logger.info(f"  Host:Port    : {settings.host}:{settings.port}")
    logger.info(f"  Log level    : {settings.log_level}")
    logger.info(f"  Debug mode   : {settings.debug}")
    logger.info("=" * 60)

    yield  # Application is running

    logger.info("RecruitIQ API shutting down.")


def create_app() -> FastAPI:
    """
    Application factory — constructs and configures the FastAPI instance.

    Returns a fully configured app ready for uvicorn.
    """
    settings = get_backend_settings()

    app = FastAPI(
        title="RecruitIQ API",
        description=(
            "Offline AI-powered candidate ranking engine. "
            "Ranks 100,000 candidates for a Senior AI Engineer role "
            "under 5 minutes on CPU."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Custom Middleware (order matters: outermost = first executed) ---
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # --- Exception Handlers ---
    register_exception_handlers(app)

    # --- Routes ---
    app.include_router(master_router)

    return app


# Module-level app instance for `uvicorn backend.main:app`
app = create_app()
