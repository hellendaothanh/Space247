from fastapi import APIRouter

from src.api.v1.endpoints import health, properties, search

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
