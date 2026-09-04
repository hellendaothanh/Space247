import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from src.main import create_app
from src.core.database import get_db_session
from src.models.property import Property

app = create_app()

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session

@pytest.fixture
def mock_properties():
    return [
        Property(
            id=uuid.uuid4(),
            title="Nhà mặt tiền quận 1",
            price=20000000000,
            area_sqm=100.0,
            address="1 Lê Duẩn",
            property_type="house",
            listing_type="sale",
            description="Nhà siêu đẹp",
        ),
        Property(
            id=uuid.uuid4(),
            title="Chung cư cao cấp Thảo Điền",
            price=5000000000,
            area_sqm=80.0,
            address="Thảo Điền, Quận 2",
            property_type="apartment",
            listing_type="sale",
            description="View sông",
        )
    ]

@pytest.fixture
async def client(mock_db_session):
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_compare_properties_valid(client, mock_db_session, mock_properties):
    ids = [str(p.id) for p in mock_properties]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_properties
    mock_db_session.execute.return_value = mock_result
    
    with patch("src.api.v1.endpoints.properties.AIComparisonService") as MockAI:
        mock_ai_instance = MockAI.return_value
        mock_ai_instance.generate_comparison = AsyncMock(return_value="## Markdown phân tích")
        
        response = await client.post("/api/v1/properties/compare", json={"property_ids": ids})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["properties"]) == 2
        assert data["analysis_markdown"] == "## Markdown phân tích"

@pytest.mark.asyncio
async def test_compare_properties_invalid_too_few(client):
    response = await client.post("/api/v1/properties/compare", json={"property_ids": [str(uuid.uuid4())]})
    assert response.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_compare_properties_invalid_too_many(client):
    ids = [str(uuid.uuid4()) for _ in range(4)]
    response = await client.post("/api/v1/properties/compare", json={"property_ids": ids})
    assert response.status_code == 422 # Pydantic validation error
    
@pytest.mark.asyncio
async def test_compare_properties_not_found(client, mock_db_session, mock_properties):
    ids = [str(mock_properties[0].id), str(uuid.uuid4())]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_properties[0]]
    mock_db_session.execute.return_value = mock_result
    
    response = await client.post("/api/v1/properties/compare", json={"property_ids": ids})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_compare_properties_cache_hit(client, mock_properties):
    ids = [str(p.id) for p in mock_properties]
    
    with patch("src.api.v1.endpoints.properties.get_cached_json") as mock_cache:
        mock_cache.return_value = {
            "properties": [
                {
                    "property_id": ids[0],
                    "title": "Cached",
                    "price": 1000,
                    "area_sqm": 50,
                    "price_per_sqm": 20
                },
                {
                    "property_id": ids[1],
                    "title": "Cached 2",
                    "price": 2000,
                    "area_sqm": 100,
                    "price_per_sqm": 20
                }
            ],
            "analysis_markdown": "Cached markdown"
        }
        
        response = await client.post("/api/v1/properties/compare", json={"property_ids": ids})
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_markdown"] == "Cached markdown"
