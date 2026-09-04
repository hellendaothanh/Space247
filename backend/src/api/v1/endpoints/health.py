from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db_session

router = APIRouter()


@router.get(
    "",
    summary="Service and Vector Database Health Check",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Database and pgvector extension are healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "pgvector": "enabled",
                        "vector_dim": 768,
                    }
                }
            },
        },
        503: {
            "description": "Database connectivity or pgvector extension failure",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "database": "error",
                        "pgvector": "disabled",
                        "vector_dim": 768,
                        "detail": "Connection error details",
                    }
                }
            },
        },
    },
)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Health check endpoint verifying:
    1. PostgreSQL database connectivity.
    2. pgvector extension activation.
    3. Configured vector dimension consistency.
    """
    db_connected = False
    pgvector_enabled = False

    try:
        # Check basic database connectivity
        result_db = await db.execute(text("SELECT 1"))
        if result_db.scalar() == 1:
            db_connected = True

        # Check if pgvector extension is loaded in the connected database
        result_vector = await db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        row = result_vector.first()
        if row and row[0] == "vector":
            pgvector_enabled = True

        if not db_connected or not pgvector_enabled:
            reason = []
            if not db_connected:
                reason.append("Database connection test failed")
            if not pgvector_enabled:
                reason.append("pgvector extension not installed in database")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "database": "connected" if db_connected else "disconnected",
                    "pgvector": "enabled" if pgvector_enabled else "disabled",
                    "vector_dim": settings.VECTOR_DIM,
                    "detail": "; ".join(reason),
                },
            )

        return {
            "status": "healthy",
            "database": "connected",
            "pgvector": "enabled",
            "vector_dim": settings.VECTOR_DIM,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "pgvector": "disabled",
                "vector_dim": settings.VECTOR_DIM,
                "detail": str(exc),
            },
        ) from exc
