from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import create_app
from src.core.database import get_db_session
from src.api.deps import get_current_active_user
from src.models.project import Project
from src.models.property import Property
from src.models.user import User
from src.schemas.chat import ChatMessage
from src.services.chat_assistant import ChatAssistantService

app = create_app()


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session


@pytest.fixture
def sample_project():
    return Project(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        name="Vinhomes Grand Park",
        slug="vinhomes-grand-park",
        developer="Vingroup",
        description="Khu đô thị đại công viên 36ha hàng đầu Đông Sài Gòn",
        status="under_construction",
        total_units=44000,
        launch_year=2019,
        handover_year=2024,
        address="Nguyễn Xiển, Long Thạnh Mỹ",
        ward="Long Thạnh Mỹ",
        district="Quận 9",
        city="Hồ Chí Minh",
        latitude=10.845,
        longitude=106.838,
        images=["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00"],
        master_plan_url="https://images.unsplash.com/photo-masterplan",
        legal_status="Sổ hồng lâu dài",
        price_range_min=1500000000.0,
        price_range_max=8000000000.0,
        amenities=["Hồ bơi", "Công viên 36ha", "Trung tâm thương mại", "Bệnh viện Vinmec"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def client(mock_db_session):
    dummy_user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        email="test.admin@space247.vn",
        hashed_password="hash",
        full_name="Admin Test User",
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
async def test_list_projects(client, mock_db_session, sample_project):
    # Total count query mock
    count_result = MagicMock()
    count_result.scalar.return_value = 1

    # Project items query mock
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [sample_project]

    # Stats query mock
    stats_result = MagicMock()
    stats_result.all.return_value = [
        (sample_project.id, 5, 3, 2, 45000000.0)
    ]

    mock_db_session.execute.side_effect = [count_result, items_result, stats_result]

    with patch("src.api.v1.endpoints.projects.get_cached_json", new_callable=AsyncMock) as mock_get_cache, \
         patch("src.api.v1.endpoints.projects.set_cached_json", new_callable=AsyncMock) as mock_set_cache:
        mock_get_cache.return_value = None

        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["name"] == "Vinhomes Grand Park"
        assert item["slug"] == "vinhomes-grand-park"
        assert item["active_properties_count"] == 5
        assert item["for_sale_count"] == 3
        assert item["for_rent_count"] == 2
        assert item["average_price_per_sqm"] == 45000000.0
        mock_set_cache.assert_called_once()


@pytest.mark.asyncio
async def test_get_project_by_slug(client, mock_db_session, sample_project):
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = sample_project

    stats_result = MagicMock()
    stats_result.all.return_value = [
        (sample_project.id, 10, 8, 2, 50000000.0)
    ]

    mock_db_session.execute.side_effect = [mock_res, stats_result]

    with patch("src.api.v1.endpoints.projects.get_cached_json", new_callable=AsyncMock) as mock_get_cache, \
         patch("src.api.v1.endpoints.projects.set_cached_json", new_callable=AsyncMock) as mock_set_cache:
        mock_get_cache.return_value = None

        response = await client.get("/api/v1/projects/vinhomes-grand-park")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_project.id)
        assert data["slug"] == "vinhomes-grand-park"
        assert data["active_properties_count"] == 10
        assert data["average_price_per_sqm"] == 50000000.0


@pytest.mark.asyncio
async def test_get_project_not_found(client, mock_db_session):
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_res

    with patch("src.api.v1.endpoints.projects.get_cached_json", new_callable=AsyncMock) as mock_get_cache:
        mock_get_cache.return_value = None
        response = await client.get("/api/v1/projects/non-existent-slug")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_project(client, mock_db_session):
    slug_check = MagicMock()
    slug_check.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = slug_check

    payload = {
        "name": "Masteri Centre Point",
        "developer": "Masterise Homes",
        "description": "Căn hộ compound cao cấp chuẩn quốc tế",
        "status": "under_construction",
        "total_units": 5000,
        "launch_year": 2020,
        "handover_year": 2023,
        "address": "Khu đô thị Vinhomes Grand Park, Quận 9",
        "city": "Hồ Chí Minh",
        "district": "Quận 9",
        "latitude": 10.843,
        "longitude": 106.840,
        "images": ["https://images.unsplash.com/photo-masteri"],
        "price_range_min": 2500000000.0,
        "price_range_max": 6000000000.0,
        "amenities": ["Hồ bơi phi thuyền", "Gym quốc tế"],
    }

    with patch("src.api.v1.endpoints.projects.get_embedding_service") as mock_emb_service, \
         patch("src.api.v1.endpoints.projects.invalidate_project_caches", new_callable=AsyncMock) as mock_inv:
        mock_emb = MagicMock()
        mock_emb.generate_embedding.return_value = [0.1] * 768
        mock_emb_service.return_value = mock_emb

        response = await client.post("/api/v1/projects", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Masteri Centre Point"
        assert data["slug"] == "masteri-centre-point"
        assert data["developer"] == "Masterise Homes"
        mock_inv.assert_called_once()


@pytest.mark.asyncio
async def test_update_project(client, mock_db_session, sample_project):
    find_mock = MagicMock()
    find_mock.scalar_one_or_none.return_value = sample_project

    stats_mock = MagicMock()
    stats_mock.all.return_value = []

    mock_db_session.execute.side_effect = [find_mock, stats_mock]

    with patch("src.api.v1.endpoints.projects.invalidate_project_caches", new_callable=AsyncMock) as mock_inv:
        response = await client.put(
            f"/api/v1/projects/{sample_project.id}",
            json={"description": "Mô tả mới đã được cập nhật", "total_units": 45000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Mô tả mới đã được cập nhật"
        mock_inv.assert_called_once()


@pytest.mark.asyncio
async def test_list_project_properties(client, mock_db_session, sample_project):
    # First query: project check
    proj_check = MagicMock()
    proj_check.scalar_one_or_none.return_value = sample_project.id

    # Second query: properties
    prop1 = Property(
        id=uuid.uuid4(),
        title="Căn hộ 2PN Origami",
        description="View hồ cá Koi Origami",
        property_type="apartment",
        listing_type="sale",
        price=2800000000.0,
        area_sqm=65.0,
        address="Khu Origami, Vinhomes Grand Park",
        city="Hồ Chí Minh",
        project_id=sample_project.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    props_mock = MagicMock()
    props_mock.scalars.return_value.all.return_value = [prop1]

    mock_db_session.execute.side_effect = [proj_check, props_mock]

    response = await client.get(f"/api/v1/projects/{sample_project.slug}/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Căn hộ 2PN Origami"
    assert data[0]["project_id"] == str(sample_project.id)


def test_chat_assistant_extracts_project_intent():
    service = ChatAssistantService(embedding_service=MagicMock())
    messages = [
        ChatMessage(role="user", content="Tôi muốn xem tiện ích dự án Masteri Centre Point ở Quận 9 giá dưới 4 tỷ"),
    ]
    is_search, criteria = service.parse_intent_and_criteria(messages)
    assert is_search is True
    assert criteria.project_name == "Masteri Centre Point"
    assert criteria.district == "Quận 9"
    assert criteria.max_price == 4000000000.0
