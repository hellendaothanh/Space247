from fastapi import APIRouter

from src.api.v1.endpoints import (
    agent,
    alerts,
    auth,
    chat,
    financial,
    health,
    notifications,
    properties,
    search,
    spatial,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["spatial"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
