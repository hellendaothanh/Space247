from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.v1.router import api_router
from src.core.cache import close_redis_pool, init_redis_pool
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
    4. Connects to Redis cache pool.
    """
    logger.info("Initializing Space247 Real Estate API...")
    try:
        async with engine.begin() as conn:
            # Check and register pgvector and postgis extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            # Create schema tables if needed
            await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "Database connection established, pgvector and postgis extensions verified (dim: %d)",
                settings.VECTOR_DIM,
            )
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup (may be running in test or offline mode): %s",
            exc,
        )

    # Initialize Redis connection pool
    try:
        await init_redis_pool()
    except Exception as exc:
        logger.warning("Redis initialization skipped or failed: %s", exc)

    yield

    # Teardown
    logger.info("Shutting down Space247 Real Estate API...")
    try:
        await close_redis_pool()
    except Exception as exc:
        logger.warning("Error closing Redis pool: %s", exc)
    finally:
        await engine.dispose()
        logger.info("Database and cache connections closed.")


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
