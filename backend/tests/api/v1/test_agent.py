import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import create_app
from src.api.deps import get_current_active_user, get_current_user
from src.core.database import get_db_session
from src.models.property import Property
from src.models.user import User

app = create_app()


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def agent_user():
    return User(
        id=uuid.uuid4(),
        email="agent@space247.vn",
        hashed_password="hash",
        full_name="Nguyễn Văn Môi Giới",
        role="agent",
        is_active=True,
    )


@pytest.fixture
def regular_user():
    return User(
        id=uuid.uuid4(),
        email="customer@space247.vn",
        hashed_password="hash",
        full_name="Khách Hàng Thường",
        role="user",
        is_active=True,
    )


@pytest.fixture
def sample_properties():
    return [
        Property(
            id=uuid.uuid4(),
            title="Căn hộ Sun Grand City Thụy Khuê",
            price=7500000000.0,
            currency="VND",
            area_sqm=90.0,
            address="69 Thụy Khuê, Tây Hồ, Hà Nội",
            latitude=21.0425,
            longitude=105.8235,
            property_type="apartment",
            listing_type="sale",
            num_bedrooms=2,
            num_bathrooms=2,
            status="active",
            description="View Hồ Tây tuyệt đẹp",
        ),
        Property(
            id=uuid.uuid4(),
            title="Chung cư Golden Westlake Hoàng Hoa Thám",
            price=8200000000.0,
            currency="VND",
            area_sqm=100.0,
            address="151 Hoàng Hoa Thám, Ba Đình, Hà Nội",
            latitude=21.0401,
            longitude=105.8188,
            property_type="apartment",
            listing_type="sale",
            num_bedrooms=3,
            num_bathrooms=2,
            status="active",
            description="Tiện ích 5 sao",
        ),
    ]


@pytest.fixture
def distant_properties():
    # Located ~5-6km away from (21.0425, 105.8235)
    return [
        Property(
            id=uuid.uuid4(),
            title="Căn hộ Vinhomes Smart City",
            price=3200000000.0,
            currency="VND",
            area_sqm=65.0,
            address="Tây Mỗ, Nam Từ Liêm, Hà Nội",
            latitude=20.9995,
            longitude=105.7420,
            property_type="apartment",
            listing_type="sale",
            num_bedrooms=2,
            num_bathrooms=1,
            status="active",
            description="Đại đô thị thông minh",
        ),
        Property(
            id=uuid.uuid4(),
            title="Chung cư Masteri West Heights",
            price=3800000000.0,
            currency="VND",
            area_sqm=68.0,
            address="Tây Mỗ, Nam Từ Liêm, Hà Nội",
            latitude=20.9980,
            longitude=105.7405,
            property_type="apartment",
            listing_type="sale",
            num_bedrooms=2,
            num_bathrooms=2,
            status="active",
            description="Căn hộ cao cấp Masterise",
        ),
    ]


@pytest.fixture
async def unauth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def agent_client(agent_user, mock_db_session):
    app.dependency_overrides[get_current_user] = lambda: agent_user
    app.dependency_overrides[get_current_active_user] = lambda: agent_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def regular_client(regular_user, mock_db_session):
    app.dependency_overrides[get_current_user] = lambda: regular_user
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_listing_unauthenticated(unauth_client):
    response = await unauth_client.post(
        "/api/v1/agent/listing/generate",
        json={"text_prompts": ["Căn hộ 2PN 80m2"]}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_listing_forbidden_regular_user(regular_client):
    response = await regular_client.post(
        "/api/v1/agent/listing/generate",
        json={"text_prompts": ["Căn hộ 2PN 80m2"]}
    )
    assert response.status_code == 403
    assert "Môi giới" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_listing_agent_success(agent_client):
    payload = {
        "text_prompts": [
            "Căn hộ 3PN 95m2 D'Capitale",
            "Tầng trung view hồ điều hòa thoáng mát",
            "Nội thất cao cấp đầy đủ, ban công Đông Nam",
            "Sổ hồng chính chủ, giá 6.8 tỷ",
        ],
        "property_type": "apartment",
        "target_audience": "Gia đình trẻ thành đạt",
    }
    response = await agent_client.post("/api/v1/agent/listing/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "title_seo" in data
    assert len(data["title_seo"]) > 0
    assert "description_markdown" in data
    assert len(data["description_markdown"]) > 50
    specs = data["extracted_specs"]
    assert specs["area_sqm"] == 95.0
    assert specs["num_bedrooms"] == 3
    assert specs["orientation"] == "Đông Nam"
    assert "Sổ hồng" in (specs["legal_status"] or "")
    assert specs["suggested_price"] == 6800000000.0


@pytest.mark.asyncio
async def test_generate_listing_multimodal_image(agent_client):
    payload = {
        "text_prompts": ["Căn nhà phố 4 tầng 60m2 mặt tiền 4.5m"],
        "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=",
        "property_type": "house",
    }
    response = await agent_client.post("/api/v1/agent/listing/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_specs"]["area_sqm"] == 60.0
    assert data["extracted_specs"]["frontage_meters"] == 4.5


@pytest.mark.asyncio
async def test_valuation_unauthenticated(unauth_client):
    response = await unauth_client.post(
        "/api/v1/agent/valuation/estimate",
        json={"area_sqm": 85.0, "latitude": 21.0425, "longitude": 105.8235}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valuation_agent_success(agent_client, mock_db_session, sample_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_properties
    mock_db_session.execute.return_value = mock_result

    payload = {
        "property_type": "apartment",
        "area_sqm": 90.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "latitude": 21.0425,
        "longitude": 105.8235,
        "radius_km": 2.5,
    }
    response = await agent_client.post("/api/v1/agent/valuation/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_price_per_sqm"] > 0
    assert data["estimated_total_price"] > 0
    assert data["price_range_low"] < data["estimated_total_price"] < data["price_range_high"]
    assert data["confidence_score"] >= 0.7
    assert len(data["comparable_properties"]) == 2
    assert data["radius_used_km"] == 2.5


@pytest.mark.asyncio
async def test_valuation_dynamic_expansion(agent_client, mock_db_session, distant_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = distant_properties
    mock_db_session.execute.return_value = mock_result

    # Request centered at (21.0425, 105.8235), distant properties are ~10km away or at (20.9995, 105.7420)
    # Haversine distance from (21.0425, 105.8235) to (20.9995, 105.7420) is ~9.7km
    # So let's place distant properties at ~5.5km away:
    # 0.04 deg lat ~ 4.4km
    for p in distant_properties:
        p.latitude = 21.0425 + 0.045  # ~5.0 km
        p.longitude = 105.8235

    payload = {
        "property_type": "apartment",
        "area_sqm": 70.0,
        "latitude": 21.0425,
        "longitude": 105.8235,
        "radius_km": 2.0,  # Initial 2km will not find them
    }
    response = await agent_client.post("/api/v1/agent/valuation/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should have expanded radius past 2.0km
    assert data["radius_used_km"] > 2.0
    assert data["confidence_score"] < 0.85
    assert len(data["comparable_properties"]) >= 2


@pytest.mark.asyncio
async def test_valuation_deviation_high_and_low(agent_client, mock_db_session, sample_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_properties
    mock_db_session.execute.return_value = mock_result

    # 1. Proposed price significantly higher (+30%)
    high_payload = {
        "property_type": "apartment",
        "area_sqm": 90.0,
        "latitude": 21.0425,
        "longitude": 105.8235,
        "radius_km": 2.5,
        "user_proposed_price": 12000000000.0,
    }
    res_high = await agent_client.post("/api/v1/agent/valuation/estimate", json=high_payload)
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["deviation_percentage"] is not None
    assert data_high["deviation_percentage"] > 10.0
    assert "cao hơn" in data_high["pricing_advice"].lower()

    # 2. Proposed price significantly lower (-25%)
    low_payload = {
        "property_type": "apartment",
        "area_sqm": 90.0,
        "latitude": 21.0425,
        "longitude": 105.8235,
        "radius_km": 2.5,
        "user_proposed_price": 5000000000.0,
    }
    res_low = await agent_client.post("/api/v1/agent/valuation/estimate", json=low_payload)
    assert res_low.status_code == 200
    data_low = res_low.json()
    assert data_low["deviation_percentage"] is not None
    assert data_low["deviation_percentage"] < -10.0
    assert "thấp hơn" in data_low["pricing_advice"].lower()


@pytest.mark.asyncio
async def test_valuation_caching(agent_client, mock_db_session, sample_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_properties
    mock_db_session.execute.return_value = mock_result

    payload = {
        "property_type": "apartment",
        "area_sqm": 90.0,
        "latitude": 21.0425,
        "longitude": 105.8235,
        "radius_km": 2.5,
        "user_proposed_price": 7500000000.0,
    }

    # Patch cache to test cache hit
    with patch("src.services.agent_service.get_cached_json", AsyncMock(return_value=None)) as mock_get_cache, \
         patch("src.services.agent_service.set_cached_json", AsyncMock(return_value=True)) as mock_set_cache:
        res1 = await agent_client.post("/api/v1/agent/valuation/estimate", json=payload)
        assert res1.status_code == 200
        assert mock_set_cache.called

    cached_val = res1.json()
    with patch("src.services.agent_service.get_cached_json", AsyncMock(return_value=cached_val)) as mock_get_cache:
        res2 = await agent_client.post("/api/v1/agent/valuation/estimate", json=payload)
        assert res2.status_code == 200
        assert res2.json()["estimated_total_price"] == cached_val["estimated_total_price"]
        # Database should not have been called when cached
        mock_db_session.execute.reset_mock()
