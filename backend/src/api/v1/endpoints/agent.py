import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_agent_user
from src.core.database import get_db_session
from src.models.user import User
from src.schemas.agent import (
    GenerateListingRequest,
    GenerateListingResponse,
    ValuationRequest,
    ValuationResponse,
)
from src.services.agent_service import AgentService, get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/listing/generate",
    response_model=GenerateListingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate SEO property listing title, rich description and extract specs",
)
async def generate_listing(
    request: GenerateListingRequest,
    current_user: User = Depends(get_current_agent_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> GenerateListingResponse:
    """
    Generate professional SEO-optimized real estate listing and extract specs from quick notes or images.
    Restricted to Agent and Admin accounts.
    """
    return await agent_service.generate_listing(request)


@router.post(
    "/valuation/estimate",
    response_model=ValuationResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate property valuation (AVM) using PostGIS comps and Weighted KNN",
)
async def estimate_valuation(
    request: ValuationRequest,
    current_user: User = Depends(get_current_agent_user),
    db: AsyncSession = Depends(get_db_session),
    agent_service: AgentService = Depends(get_agent_service),
) -> ValuationResponse:
    """
    Automated Valuation Model (AVM) advising optimal listing price based on neighborhood market comps.
    Dynamically expands search radius from 2.5km to 8.0km if sparse, and computes deviation against proposed price.
    Restricted to Agent and Admin accounts.
    """
    return await agent_service.estimate_valuation(db=db, request=request)
