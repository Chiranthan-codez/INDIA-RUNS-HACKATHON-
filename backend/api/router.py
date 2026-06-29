"""
Master API router — includes all sub-routers.

Single import point for main.py to mount all routes.
"""
from fastapi import APIRouter

from backend.api.health import router as health_router
from backend.api.upload import router as upload_router
from backend.api.ranking import router as ranking_router
from backend.api.config_routes import router as config_router

master_router = APIRouter()

master_router.include_router(health_router)
master_router.include_router(upload_router)
master_router.include_router(ranking_router)
master_router.include_router(config_router)
