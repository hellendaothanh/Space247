import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import create_app
from src.core.database import get_db_session
from src.models.property import Property

app = create_app()


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def mock_properties():
    return [
        Property(
            id=uuid.uuid4(),
            title="Căn hộ Vinhomes Metropolis Liễu Giai",
            price=9800000000.0,
            currency="VND",
            area_sqm=78.5,
            address="29 Liễu Giai",
            ward="Ngọc Khánh",
            district="Ba Đình",
            city="Hà Nội",
            latitude=21.0331,
            longitude=105.8152,
            property_type="apartment",
            listing_type="sale",
            status="active",
            description="View Hồ Tây",
        ),
        Property(
            id=uuid.uuid4(),
            title="Chung cư Discovery Complex Cầu Giấy",
            price=6000000000.0,
            currency="VND",
            area_sqm=95.0,
            address="302 Cầu Giấy",
            ward="Dịch Vọng",
            district="Cầu Giấy",
            city="Hà Nội",
            latitude=21.0345,
            longitude=105.7925,
            property_type="apartment",
            listing_type="sale",
            status="active",
            description="Cạnh ga Metro",
        ),
    ]


@pytest.fixture
async def client(mock_db_session):
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_isochrone_search_valid_landmark(client, mock_db_session, mock_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_properties
    mock_db_session.execute.return_value = mock_result

    payload = {
        "target_landmark": "Keangnam",
        "max_duration_minutes": 15,
        "transport_mode": "motorcycle",
    }
    response = await client.post("/api/v1/spatial/isochrone-search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "target_location" in data
    assert data["target_location"]["name"] == "Tòa nhà Keangnam Landmark 72"
    assert "isochrone_geojson" in data
    assert data["isochrone_geojson"]["type"] == "FeatureCollection"
    assert len(data["properties"]) == 2
    assert data["properties"][0]["estimated_travel_minutes"] > 0
    assert data["properties"][0]["distance_km"] >= 0


@pytest.mark.asyncio
async def test_isochrone_search_coordinates(client, mock_db_session, mock_properties):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_properties
    mock_db_session.execute.return_value = mock_result

    payload = {
        "target_landmark": "21.0169, 105.7839",
        "max_duration_minutes": 20,
        "transport_mode": "car",
    }
    response = await client.post("/api/v1/spatial/isochrone-search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["max_duration_minutes"] == 20
    assert data["transport_mode"] == "car"


@pytest.mark.asyncio
async def test_isochrone_search_unknown_landmark(client, mock_db_session):
    with patch("src.services.spatial_service.SpatialService.geocode_landmark", AsyncMock(return_value=None)):
        payload = {
            "target_landmark": "DiaDanhKhongTonTai12345XYZ",
            "max_duration_minutes": 15,
            "transport_mode": "motorcycle",
        }
        response = await client.post("/api/v1/spatial/isochrone-search", json=payload)
        assert response.status_code == 404
        assert "Không tìm thấy địa danh" in response.json()["detail"]


@pytest.mark.asyncio
async def test_amenity_heatmap_all(client):
    response = await client.get("/api/v1/spatial/amenities/heatmap?category=all")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "all"
    assert data["total_points"] > 0
    assert len(data["heatmap_points"]) > 0
    # Each heatmap point must be [lat, lng, weight]
    first_pt = data["heatmap_points"][0]
    assert len(first_pt) == 3
    assert isinstance(first_pt[0], float)
    assert isinstance(first_pt[1], float)
    assert isinstance(first_pt[2], (int, float))


@pytest.mark.asyncio
async def test_amenity_heatmap_by_category(client):
    response = await client.get("/api/v1/spatial/amenities/heatmap?category=hospital")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "hospital"
    assert all(poi["category"] == "hospital" for poi in data["pois"])
