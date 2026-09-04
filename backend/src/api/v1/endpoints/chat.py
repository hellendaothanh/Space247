import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.schemas.chat import (
    ChatAssistantRequest,
    ChatAssistantResponse,
)
from src.services.chat_assistant import (
    ChatAssistantService,
    get_chat_assistant_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/assistant",
    response_model=ChatAssistantResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Real Estate Chatbot Assistant",
    description=(
        "Conversational AI assistant for real estate discovery. Analyzes conversation messages, "
        "extracts intent and structured criteria (price range, location, property type, bedrooms, amenities), "
        "executes Hybrid Search with Reciprocal Rank Fusion against active listings, and synthesizes "
        "a friendly, natural Vietnamese response along with recommended property cards."
    ),
)
async def chat_assistant(
    request: ChatAssistantRequest,
    db: AsyncSession = Depends(get_db_session),
    chat_service: ChatAssistantService = Depends(get_chat_assistant_service),
) -> ChatAssistantResponse:
    """
    Handle chat messages with AI assistant:
    1. Parse intent and extract criteria
    2. If search intent, run hybrid search
    3. Synthesize natural Vietnamese response with property cards & suggestions
    """
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty",
        )

    is_search, criteria = chat_service.parse_intent_and_criteria(request.messages)

    properties = []
    if is_search:
        try:
            properties = await chat_service.execute_hybrid_search(
                db=db,
                criteria=criteria,
                limit=request.limit,
            )
        except Exception as e:
            logger.error("Error executing hybrid search in chat assistant: %s", e, exc_info=True)
            properties = []

    message, suggestions = chat_service.generate_natural_response(
        criteria=criteria,
        properties=properties,
        is_search=is_search,
    )

    return ChatAssistantResponse(
        message=message,
        properties=properties,
        criteria=criteria if is_search else None,
        suggestions=suggestions,
    )
