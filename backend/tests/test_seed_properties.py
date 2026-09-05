from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.seed_properties import (
    DEFAULT_SEED_USERS,
    SAMPLE_PROJECTS,
    SAMPLE_PROPERTIES,
    seed_projects,
    seed_properties,
    seed_users,
)


def test_sample_properties_structure_and_diversity():
    """Verify that sample properties list meets all diversity and data completeness requirements."""
    assert len(SAMPLE_PROPERTIES) >= 25, f"Expected at least 25 properties, got {len(SAMPLE_PROPERTIES)}"

    property_types = {item["property_type"] for item in SAMPLE_PROPERTIES}
    listing_types = {item["listing_type"] for item in SAMPLE_PROPERTIES}
    cities = {item["city"] for item in SAMPLE_PROPERTIES}

    # Verify diversity
    assert {"apartment", "house", "villa", "commercial", "land"}.issubset(property_types)
    assert {"sale", "rent"}.issubset(listing_types)
    assert any("Hà Nội" in city for city in cities)
    assert any("Hồ Chí Minh" in city for city in cities)

    # Verify all items have complete mandatory fields
    for item in SAMPLE_PROPERTIES:
        assert item.get("title"), "Property missing title"
        assert item.get("description"), "Property missing description"
        assert item.get("price") and item["price"] > 0, "Invalid price"
        assert item.get("area_sqm") and item["area_sqm"] > 0, "Invalid area_sqm"
        assert item.get("address"), "Property missing address"
        assert item.get("city"), "Property missing city"
        assert item.get("status") == "active"


class MockEmbeddingServiceForSeed:
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.call_count = 0

    def build_property_text(self, **kwargs) -> str:
        return f"{kwargs.get('title', '')} {kwargs.get('address', '')}"

    def generate_embedding(self, text: str, is_query: bool = False) -> list[float]:
        self.call_count += 1
        return [0.05] * self.dim


@pytest.mark.asyncio
async def test_seed_properties_logic_and_idempotency():
    """Verify that seed_properties accurately creates items and skips existing items on repeat runs."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_embedding = MockEmbeddingServiceForSeed(dim=768)

    sample_batch = [
        {
            "title": "Căn hộ thử nghiệm Quận 1",
            "description": "Mô tả căn hộ thử nghiệm",
            "property_type": "apartment",
            "listing_type": "sale",
            "price": 5000000000.0,
            "currency": "VND",
            "area_sqm": 70.0,
            "num_bedrooms": 2,
            "num_bathrooms": 2,
            "address": "123 Lê Lợi",
            "ward": "Bến Nghé",
            "district": "Quận 1",
            "city": "Thành phố Hồ Chí Minh",
            "latitude": 10.77,
            "longitude": 106.70,
            "status": "active",
        },
        {
            "title": "Nhà phố thử nghiệm Ba Đình",
            "description": "Mô tả nhà phố Ba Đình",
            "property_type": "house",
            "listing_type": "rent",
            "price": 25000000.0,
            "currency": "VND",
            "area_sqm": 80.0,
            "num_bedrooms": 3,
            "num_bathrooms": 3,
            "address": "45 Kim Mã",
            "ward": "Kim Mã",
            "district": "Quận Ba Đình",
            "city": "Thành phố Hà Nội",
            "latitude": 21.03,
            "longitude": 105.82,
            "status": "active",
        },
    ]

    added_properties = []

    def fake_add(obj):
        added_properties.append(obj)

    mock_session.add = fake_add
    mock_session.commit = MagicMock()

    # 1. First run: No existing properties in database
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.first.return_value = None

    async def fake_execute_empty(stmt):
        return mock_result_empty

    async def fake_commit():
        pass

    mock_session.execute = fake_execute_empty
    mock_session.commit = fake_commit

    stats_first = await seed_properties(
        session=mock_session,
        properties_data=sample_batch,
        embedding_svc=mock_embedding,
    )

    assert stats_first["total"] == 2
    assert stats_first["created"] == 2
    assert stats_first["skipped"] == 0
    assert len(added_properties) == 2
    assert len(added_properties[0].embedding) == 768
    assert added_properties[0].title == "Căn hộ thử nghiệm Quận 1"
    assert mock_embedding.call_count == 2

    # 2. Second run: Both properties already exist in database
    mock_existing_obj = MagicMock()
    mock_result_existing = MagicMock()
    mock_result_existing.scalars.return_value.first.return_value = mock_existing_obj

    async def fake_execute_existing(stmt):
        return mock_result_existing

    mock_session.execute = fake_execute_existing
    added_properties.clear()
    mock_embedding.call_count = 0

    stats_second = await seed_properties(
        session=mock_session,
        properties_data=sample_batch,
        embedding_svc=mock_embedding,
    )

    assert stats_second["total"] == 2
    assert stats_second["created"] == 0
    assert stats_second["skipped"] == 2
    assert len(added_properties) == 0
    assert mock_embedding.call_count == 0


@pytest.mark.asyncio
async def test_seed_users_idempotency():
    """Verify that default admin and agent users are created idempotently."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()

    added_users = []

    def fake_add_user(obj):
        added_users.append(obj)

    mock_session.add = fake_add_user

    # 1. First run: No existing users
    mock_result_none = MagicMock()
    mock_result_none.scalar_one_or_none.return_value = None

    async def fake_execute_no_users(stmt):
        return mock_result_none

    mock_session.execute = fake_execute_no_users

    users_map_first = await seed_users(session=mock_session)
    assert len(users_map_first) == 3
    assert "admin@space247.vn" in users_map_first
    assert "agent@space247.vn" in users_map_first
    assert "user@space247.vn" in users_map_first
    assert len(added_users) == 3
    assert all(u.role in ("admin", "agent", "user") for u in added_users)

    # 2. Second run: Users already exist
    existing_admin = MagicMock()
    existing_admin.role = "admin"
    existing_admin.email = "admin@space247.vn"
    existing_agent = MagicMock()
    existing_agent.role = "agent"
    existing_agent.email = "agent@space247.vn"
    existing_user = MagicMock()
    existing_user.role = "user"
    existing_user.email = "user@space247.vn"

    call_count = 0

    async def fake_execute_existing_users(stmt):
        nonlocal call_count
        res = MagicMock()
        # Extract bound parameter value from statement if present, or toggle by call order
        params = getattr(stmt, "_compile_state", None)
        try:
            param_values = [p.value for p in stmt._bind_params.values()]
        except Exception:
            param_values = []

        if any("admin@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_admin
        elif any("agent@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_agent
        elif any("user@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_user
        else:
            # By call order: admin, agent, user
            order_map = [existing_admin, existing_agent, existing_user]
            res.scalar_one_or_none.return_value = order_map[call_count % len(order_map)]
        call_count += 1
        return res

    mock_session.execute = fake_execute_existing_users
    added_users.clear()

    users_map_second = await seed_users(session=mock_session)
    assert len(users_map_second) == 3
    assert users_map_second["admin@space247.vn"].role == "admin"
    assert users_map_second["agent@space247.vn"].role == "agent"
    assert users_map_second["user@space247.vn"].role == "user"
    assert len(added_users) == 0  # No new users added


@pytest.mark.asyncio
async def test_seed_properties_links_owner_id():
    """Verify that seeded properties correctly store the owner_user_id."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_embedding = MockEmbeddingServiceForSeed(dim=768)

    sample = [
        {
            "title": "Căn hộ Quận 7 có chủ sở hữu",
            "description": "Mô tả căn hộ Quận 7",
            "property_type": "apartment",
            "listing_type": "sale",
            "price": 3200000000.0,
            "currency": "VND",
            "area_sqm": 65.0,
            "address": "Phú Mỹ Hưng",
            "city": "Thành phố Hồ Chí Minh",
            "status": "active",
        }
    ]

    added_properties = []
    mock_session.add = lambda obj: added_properties.append(obj)

    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.first.return_value = None

    async def fake_execute_empty(stmt):
        return mock_result_empty

    async def fake_commit():
        pass

    mock_session.execute = fake_execute_empty
    mock_session.commit = fake_commit

    agent_id = uuid.uuid4()
    stats = await seed_properties(
        session=mock_session,
        properties_data=sample,
        embedding_svc=mock_embedding,
        owner_user_id=agent_id,
    )

    assert stats["created"] == 1
    assert len(added_properties) == 1
    assert added_properties[0].user_id == agent_id


def test_sample_projects_structure_and_diversity():
    """Verify that sample projects list has complete information and valid structure."""
    assert len(SAMPLE_PROJECTS) >= 5, f"Expected at least 5 projects, got {len(SAMPLE_PROJECTS)}"

    slugs = [item["slug"] for item in SAMPLE_PROJECTS]
    assert len(slugs) == len(set(slugs)), "Duplicate project slugs detected"

    cities = {item["city"] for item in SAMPLE_PROJECTS}
    assert any("Hồ Chí Minh" in city for city in cities)
    assert any("Hà Nội" in city for city in cities)

    for item in SAMPLE_PROJECTS:
        assert item.get("name"), "Project missing name"
        assert item.get("slug"), "Project missing slug"
        assert item.get("developer"), "Project missing developer"
        assert item.get("description"), "Project missing description"
        assert item.get("status") in ("upcoming", "under_construction", "handing_over", "completed")
        assert item.get("address"), "Project missing address"
        assert item.get("city"), "Project missing city"
        assert isinstance(item.get("amenities"), list) and len(item["amenities"]) > 0
        assert isinstance(item.get("images"), list) and len(item["images"]) > 0
        assert item.get("master_plan_url"), "Project missing master_plan_url"


@pytest.mark.asyncio
async def test_seed_projects_logic_and_idempotency():
    """Verify that seed_projects creates project entities and handles duplicate runs."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()
    mock_embedding = MockEmbeddingServiceForSeed(dim=768)

    sample_projects = [
        {
            "name": "Dự án Thử nghiệm Alpha",
            "slug": "du-an-thu-nghiem-alpha",
            "developer": "Chủ đầu tư Thử nghiệm",
            "description": "Mô tả dự án alpha",
            "status": "completed",
            "total_units": 500,
            "address": "123 Nguyễn Huệ",
            "city": "Thành phố Hồ Chí Minh",
            "district": "Quận 1",
            "latitude": 10.77,
            "longitude": 106.70,
            "images": ["https://example.com/img1.jpg"],
            "master_plan_url": "https://example.com/masterplan.jpg",
            "amenities": ["Hồ bơi", "Công viên"],
        }
    ]

    added_projects = []
    mock_session.add = lambda obj: added_projects.append(obj)

    # 1. First run: No existing project
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.first.return_value = None

    async def fake_execute_empty(stmt):
        return mock_result_empty

    async def fake_commit():
        pass

    mock_session.execute = fake_execute_empty
    mock_session.commit = fake_commit

    result_first = await seed_projects(
        session=mock_session,
        projects_data=sample_projects,
        embedding_svc=mock_embedding,
    )

    assert result_first["total"] == 1
    assert result_first["created"] == 1
    assert result_first["skipped"] == 0
    assert len(added_projects) == 1
    assert added_projects[0].name == "Dự án Thử nghiệm Alpha"
    assert added_projects[0].slug == "du-an-thu-nghiem-alpha"
    assert len(added_projects[0].embedding) == 768
    assert added_projects[0].geom == "SRID=4326;POINT(106.7 10.77)"
    assert "du-an-thu-nghiem-alpha" in result_first["project_map"]

    # 2. Second run: Project already exists
    mock_existing_proj = MagicMock()
    mock_existing_proj.slug = "du-an-thu-nghiem-alpha"
    mock_result_existing = MagicMock()
    mock_result_existing.scalars.return_value.first.return_value = mock_existing_proj

    async def fake_execute_existing(stmt):
        return mock_result_existing

    mock_session.execute = fake_execute_existing
    added_projects.clear()

    result_second = await seed_projects(
        session=mock_session,
        projects_data=sample_projects,
        embedding_svc=mock_embedding,
    )

    assert result_second["total"] == 1
    assert result_second["created"] == 0
    assert result_second["skipped"] == 1
    assert len(added_projects) == 0
    assert result_second["project_map"]["du-an-thu-nghiem-alpha"] == mock_existing_proj


@pytest.mark.asyncio
async def test_seed_properties_links_project_id():
    """Verify that properties with project_slug are linked to parent project id."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_embedding = MockEmbeddingServiceForSeed(dim=768)

    sample = [
        {
            "title": "Căn hộ thuộc dự án Metropolis",
            "description": "Mô tả căn hộ",
            "property_type": "apartment",
            "listing_type": "sale",
            "price": 5500000000.0,
            "currency": "VND",
            "area_sqm": 75.0,
            "address": "29 Liễu Giai",
            "city": "Thành phố Hà Nội",
            "status": "active",
            "project_slug": "vinhomes-metropolis",
        }
    ]

    added_properties = []
    mock_session.add = lambda obj: added_properties.append(obj)

    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.first.return_value = None

    async def fake_execute_empty(stmt):
        return mock_result_empty

    async def fake_commit():
        pass

    mock_session.execute = fake_execute_empty
    mock_session.commit = fake_commit

    fake_project_id = uuid.uuid4()
    mock_parent_project = MagicMock()
    mock_parent_project.id = fake_project_id

    project_map = {"vinhomes-metropolis": mock_parent_project}

    stats = await seed_properties(
        session=mock_session,
        properties_data=sample,
        embedding_svc=mock_embedding,
        project_map=project_map,
    )

    assert stats["created"] == 1
    assert len(added_properties) == 1
    assert added_properties[0].project_id == fake_project_id
    assert not hasattr(added_properties[0], "project_slug") or getattr(added_properties[0], "project_slug", None) is None
