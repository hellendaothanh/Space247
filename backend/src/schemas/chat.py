from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from src.schemas.property import ListingType, PropertyResponse, PropertyType


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: str = Field(..., description="Sender role: user, assistant, or system")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower not in {r.value for r in ChatRole}:
            raise ValueError(f"Invalid role '{v}'. Allowed roles: user, assistant, system")
        return v_lower


class ExtractedCriteria(BaseModel):
    listing_type: ListingType | None = Field(default=None, description="Sale or rent")
    property_type: PropertyType | None = Field(default=None, description="Apartment, house, villa, etc.")
    city: str | None = Field(default=None, description="Extracted city")
    district: str | None = Field(default=None, description="Extracted district")
    min_price: float | None = Field(default=None, description="Minimum price filter in VND")
    max_price: float | None = Field(default=None, description="Maximum price filter in VND")
    min_bedrooms: int | None = Field(default=None, description="Minimum bedrooms")
    amenities: list[str] = Field(default_factory=list, description="Extracted amenity keywords")
    raw_query: str = Field(default="", description="Search text extracted from user question")


class ChatAssistantRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Conversation history ending with the latest user query",
    )
    limit: int = Field(default=4, ge=1, le=10, description="Maximum number of recommended properties")


class ChatAssistantResponse(BaseModel):
    message: str = Field(..., description="Assistant response text in Vietnamese")
    properties: list[PropertyResponse] = Field(
        default_factory=list,
        description="List of recommended properties matching extracted criteria",
    )
    criteria: ExtractedCriteria | None = Field(
        default=None,
        description="Extracted search parameters",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested quick follow-up queries for the user",
    )
