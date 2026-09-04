from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.database import Base, engine

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("space247_backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager:
    1. Boots up and verifies database connectivity.
    2. Initializes pgvector extension if not exists.
    3. Scaffolds tables if needed in development.
    """
    logger.info("Initializing Space247 Real Estate API...")
    try:
        async with engine.begin() as conn:
            # Check and register pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Create schema tables if needed
            await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "Database connection established and pgvector extension verified (dim: %d)",
                settings.VECTOR_DIM,
            )
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup (may be running in test or offline mode): %s",
            exc,
        )

    yield

    # Teardown
    logger.info("Shutting down Space247 Real Estate API...")
    await engine.dispose()
    logger.info("Database connection closed.")


def create_app() -> FastAPI:
    """Application factory for FastAPI service."""
    application = FastAPI(
        title="Space247 Real Estate API",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Set up CORS middleware
    if settings.CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mount API v1 router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/", tags=["root"], summary="Service Root")
    async def root() -> dict[str, str]:
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return application


app = create_app()
