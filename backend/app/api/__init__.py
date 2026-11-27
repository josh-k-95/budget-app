from fastapi import APIRouter

from app.api import config, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(config.router)
