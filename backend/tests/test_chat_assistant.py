from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db_session
from src.main import app
from src.schemas.chat import ChatMessage, ChatRole
from src.schemas.property import (
    ListingType,
    PropertyResponse,
    PropertyStatus,
    PropertyType,
)
from src.services.chat_assistant import ChatAssistantService, get_chat_assistant_service


def test_parse_intent_greeting():
    service = ChatAssistantService()
    messages = [
        ChatMessage(role="user", content="Xin chào bạn, bạn là ai và có thể giúp gì cho tôi?")
    ]
    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is False
    assert criteria.raw_query == "Xin chào bạn, bạn là ai và có thể giúp gì cho tôi?"


def test_parse_intent_criteria_apartment_sale():
    service = ChatAssistantService()
    messages = [
        ChatMessage(role="user", content="Tìm căn hộ 2 phòng ngủ giá dưới 3 tỷ ở Quận 1 TP.HCM có ban công")
    ]
    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is True
    assert criteria.property_type == PropertyType.APARTMENT
    assert criteria.listing_type == ListingType.SALE
    assert criteria.district == "Quận 1"
    assert criteria.city == "Hồ Chí Minh"
    assert criteria.max_price == 3_000_000_000.0
    assert criteria.min_bedrooms == 2
    assert "ban công" in criteria.amenities


def test_parse_intent_criteria_rental_house():
    service = ChatAssistantService()
    messages = [
        ChatMessage(role="user", content="Cần thuê nhà phố Bình Thạnh khoảng 15 triệu/tháng")
    ]
    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is True
    assert criteria.listing_type == ListingType.RENT
    assert criteria.property_type == PropertyType.HOUSE
    assert criteria.district == "Bình Thạnh"
    assert criteria.city == "Hồ Chí Minh"
    assert criteria.min_price is not None
    assert criteria.max_price is not None
    assert criteria.min_price < criteria.max_price


def test_parse_intent_villa_with_pool():
    service = ChatAssistantService()
    messages = [
        ChatMessage(role="user", content="Tìm biệt thự nghỉ dưỡng có hồ bơi tại Đà Nẵng giá từ 10 đến 20 tỷ")
    ]
    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is True
    assert criteria.property_type == PropertyType.VILLA
    assert criteria.city == "Đà Nẵng"
    assert "hồ bơi" in criteria.amenities
    assert criteria.min_price == 10_000_000_000.0
    assert criteria.max_price == 20_000_000_000.0


def test_generate_natural_response_greeting():
    service = ChatAssistantService()
    is_search, criteria = service.parse_intent_and_criteria([
        ChatMessage(role="user", content="Hello space247")
    ])
    msg, suggestions = service.generate_natural_response(criteria, [], is_search=False)
    assert "Trợ lý AI" in msg or "Xin chào" in msg
    assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_chat_assistant_endpoint_greeting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/chat/assistant",
            json={
                "messages": [
                    {"role": "user", "content": "Xin chào bạn, Space247 có tính năng gì?"}
                ],
                "limit": 4,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Trợ lý AI" in data["message"] or "Xin chào" in data["message"]
    assert data["properties"] == []
    assert data["criteria"] is None
    assert len(data["suggestions"]) > 0


@pytest.mark.asyncio
async def test_chat_assistant_endpoint_search_with_results():
    sample_property = PropertyResponse(
        id=uuid.uuid4(),
        title="Căn hộ Vinhomes Golden River 2PN view sông",
        description="Căn hộ cao cấp đầy đủ nội thất, view sông Sài Gòn thoáng mát",
        property_type=PropertyType.APARTMENT,
        listing_type=ListingType.SALE,
        price=2_800_000_000.0,
        currency="VND",
        area_sqm=75.5,
        num_bedrooms=2,
        num_bathrooms=2,
        address="2 Tôn Đức Thắng",
        ward="Bến Nghé",
        district="Quận 1",
        city="Hồ Chí Minh",
        latitude=10.78,
        longitude=106.70,
        status=PropertyStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_chat_service = MagicMock(spec=ChatAssistantService)
    is_search, criteria = ChatAssistantService().parse_intent_and_criteria([
        ChatMessage(role="user", content="Tìm căn hộ 2 phòng ngủ giá dưới 3 tỷ ở Quận 1")
    ])
    mock_chat_service.parse_intent_and_criteria.return_value = (is_search, criteria)
    mock_chat_service.execute_hybrid_search = AsyncMock(return_value=[sample_property])
    mock_chat_service.generate_natural_response = MagicMock(
        return_value=(
            "Dạ, Space247 đã tìm thấy 1 bất động sản phù hợp tại Quận 1 với giá 2.80 tỷ.",
            ["Xem thêm căn hộ", "Lọc giá rẻ hơn"],
        )
    )

    app.dependency_overrides[get_chat_assistant_service] = lambda: mock_chat_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/chat/assistant",
                json={
                    "messages": [
                        {"role": "user", "content": "Tìm căn hộ 2 phòng ngủ giá dưới 3 tỷ ở Quận 1"}
                    ],
                    "limit": 4,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 1
        assert data["properties"][0]["title"] == "Căn hộ Vinhomes Golden River 2PN view sông"
        assert data["criteria"]["district"] == "Quận 1"
        assert data["criteria"]["property_type"] == "apartment"
        assert "Quận 1" in data["message"]
        assert len(data["suggestions"]) == 2
    finally:
        app.dependency_overrides.pop(get_chat_assistant_service, None)


@pytest.mark.asyncio
async def test_chat_assistant_endpoint_no_matches():
    mock_chat_service = MagicMock(spec=ChatAssistantService)
    is_search, criteria = ChatAssistantService().parse_intent_and_criteria([
        ChatMessage(role="user", content="Tìm biệt thự 100 nghìn đồng ở sao Hỏa")
    ])
    mock_chat_service.parse_intent_and_criteria.return_value = (is_search, criteria)
    mock_chat_service.execute_hybrid_search = AsyncMock(return_value=[])
    mock_chat_service.generate_natural_response = MagicMock(
        return_value=(
            "Rất tiếc Space247 chưa tìm thấy bất động sản nào khớp hoàn toàn với yêu cầu của bạn.",
            ["Tìm căn hộ 3 - 5 tỷ", "Xem bất động sản mới"],
        )
    )

    app.dependency_overrides[get_chat_assistant_service] = lambda: mock_chat_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/chat/assistant",
                json={
                    "messages": [
                        {"role": "user", "content": "Tìm biệt thự 100 nghìn đồng ở sao Hỏa"}
                    ],
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["properties"] == []
        assert "chưa tìm thấy" in data["message"]
        assert len(data["suggestions"]) > 0
    finally:
        app.dependency_overrides.pop(get_chat_assistant_service, None)


@pytest.mark.asyncio
async def test_chat_assistant_endpoint_empty_messages_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/chat/assistant",
            json={"messages": []},
        )
    # Pydantic validation error for min_length=1
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_assistant_endpoint_invalid_role_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/chat/assistant",
            json={
                "messages": [
                    {"role": "alien_bot", "content": "Hello"}
                ]
            },
        )
    assert response.status_code == 422
