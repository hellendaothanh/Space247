import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from src.main import create_app
from src.core.database import get_db_session
from src.api.deps import get_current_active_user
from src.models.property import Property
from src.models.user import User

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
    dummy_user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        email="test.default@space247.vn",
        hashed_password="hash",
        full_name="Default Test User",
        role="admin",
        is_active=True,
    )
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user
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


@pytest.mark.asyncio
async def test_get_property_detail_with_images_and_agent(client, mock_db_session):
    owner = User(
        id=uuid.uuid4(),
        email="agent.test@space247.vn",
        hashed_password="hash",
        full_name="Nguyễn Văn Đại Lý",
        phone="0912345678",
        avatar_url="https://images.unsplash.com/photo-agent.jpg",
        role="agent",
        is_active=True,
    )
    prop = Property(
        id=uuid.uuid4(),
        title="Biệt thự Thảo Điền ven sông",
        price=45000000000,
        area_sqm=350.0,
        address="12 Nguyễn Văn Hưởng",
        city="Hồ Chí Minh",
        district="Thành phố Thủ Đức",
        property_type="villa",
        listing_type="sale",
        description="Biệt thự cao cấp có hồ bơi riêng và sân vườn.",
        images=[
            "https://images.unsplash.com/photo-villa1.jpg",
            "https://images.unsplash.com/photo-villa2.jpg",
        ],
        user_id=owner.id,
    )
    prop.owner = owner

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = prop
    mock_db_session.execute.return_value = mock_result

    with patch("src.api.v1.endpoints.properties.get_cached_json", return_value=None):
        response = await client.get(f"/api/v1/properties/{prop.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 2
        assert data["images"][0] == "https://images.unsplash.com/photo-villa1.jpg"
        assert data["images"][1] == "https://images.unsplash.com/photo-villa2.jpg"
        assert data["agent"] is not None
        assert data["agent"]["id"] == str(owner.id)
        assert data["agent"]["full_name"] == "Nguyễn Văn Đại Lý"
        assert data["agent"]["email"] == "agent.test@space247.vn"
        assert data["agent"]["phone_number"] == "0912345678"
        assert data["agent"]["avatar_url"] == "https://images.unsplash.com/photo-agent.jpg"
        assert data["agent"]["role"] == "agent"


@pytest.mark.asyncio
async def test_get_property_detail_no_images_null_agent(client, mock_db_session):
    prop = Property(
        id=uuid.uuid4(),
        title="Nhà phố không có ảnh và chủ",
        price=3000000000,
        area_sqm=60.0,
        address="45 Lê Lợi",
        city="Hà Nội",
        property_type="house",
        listing_type="sale",
        description="Nhà phố trung tâm cần bán gấp.",
        images=[],
        user_id=None,
    )
    prop.owner = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = prop
    mock_db_session.execute.return_value = mock_result

    with patch("src.api.v1.endpoints.properties.get_cached_json", return_value=None):
        response = await client.get(f"/api/v1/properties/{prop.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["images"] == []
        assert data["agent"] is None


@pytest.mark.asyncio
async def test_create_property_with_images(client, mock_db_session):
    new_id = uuid.uuid4()
    mock_db_session.flush = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    with patch("src.services.embedding.EmbeddingService.generate_embedding", return_value=[0.1] * 768):
        payload = {
            "title": "Căn hộ Masteri Thảo Điền 2PN",
            "description": "Căn hộ tầng cao view sông tuyệt đẹp, đầy đủ nội thất.",
            "property_type": "apartment",
            "listing_type": "rent",
            "price": 20000000,
            "currency": "VND",
            "area_sqm": 72.5,
            "num_bedrooms": 2,
            "num_bathrooms": 2,
            "address": "159 Xa Lộ Hà Nội",
            "city": "Hồ Chí Minh",
            "images": [
                "https://images.unsplash.com/photo-apartment1.jpg",
                "https://images.unsplash.com/photo-apartment2.jpg",
            ],
        }
        response = await client.post("/api/v1/properties", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["images"]) == 2
        assert data["images"][0] == "https://images.unsplash.com/photo-apartment1.jpg"

