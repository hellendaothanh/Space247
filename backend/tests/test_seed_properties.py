from unittest.mock import AsyncMock, MagicMock
import uuid
from geoalchemy2.elements import WKTElement
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.seed_properties import (
    DEFAULT_SEED_USERS,
    SAMPLE_PROJECTS,
    SAMPLE_PROPERTIES,
    SAMPLE_RENTAL_PROPERTIES,
    seed_contracts_invoices_and_inquiries,
    seed_projects,
    seed_properties,
    seed_rental_properties,
    seed_users,
)
from src.schemas.project import ProjectBase
from src.schemas.property import PropertyBase
from src.schemas.rental_management import RentalPropertyBase, RentalUnitBase


def test_sample_properties_structure_and_diversity():
    """Verify that sample properties list meets all diversity and data completeness requirements across Vietnam."""
    assert len(SAMPLE_PROPERTIES) >= 35, f"Expected at least 35 properties, got {len(SAMPLE_PROPERTIES)}"

    property_types = {item["property_type"] for item in SAMPLE_PROPERTIES}
    listing_types = {item["listing_type"] for item in SAMPLE_PROPERTIES}
    cities = {item["city"] for item in SAMPLE_PROPERTIES}

    # Verify diversity
    assert {"apartment", "house", "villa", "commercial", "land"}.issubset(property_types)
    assert {"sale", "rent"}.issubset(listing_types)

    # Verify coverage across 9 major regions from North to South
    required_regions = [
        "Hà Nội",
        "Quảng Ninh",
        "Hải Phòng",
        "Đà Nẵng",
        "Khánh Hòa",
        "Hồ Chí Minh",
        "Bình Dương",
        "Cần Thơ",
        "Kiên Giang",
    ]
    for region in required_regions:
        assert any(region in city for city in cities), f"Missing geographic coverage for region: {region}"

    # Verify homestay / vacation listings presence
    vacation_count = sum(
        1 for item in SAMPLE_PROPERTIES
        if item.get("rental_type") in ("serviced_apartment", "entire_house")
        and (
            "homestay" in item["title"].lower()
            or "homestay" in item["description"].lower()
            or "nghỉ dưỡng" in item["description"].lower()
            or "du lịch" in item["description"].lower()
        )
    )
    assert vacation_count >= 5, f"Expected at least 5 vacation/homestay/villa listings, got {vacation_count}"

    # Verify all items have complete mandatory fields and strictly conform to PropertyBase schema
    for item in SAMPLE_PROPERTIES:
        assert item.get("title"), "Property missing title"
        assert item.get("description"), "Property missing description"
        assert item.get("price") and item["price"] > 0, "Invalid price"
        assert item.get("area_sqm") and item["area_sqm"] > 0, "Invalid area_sqm"
        assert item.get("address"), "Property missing address"
        assert item.get("city"), "Property missing city"
        assert item.get("status") == "active"
        assert isinstance(item.get("images"), list) and len(item["images"]) > 0, "Property missing images"
        assert item.get("latitude") and item.get("longitude"), "Property missing geographic coordinates"

        # Validate with Pydantic PropertyBase schema
        prop_copy = dict(item)
        prop_copy.pop("project_slug", None)
        PropertyBase(**prop_copy)


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
    assert len(users_map_first) == 5
    assert "host@space247.vn" in users_map_first
    assert "superadmin@space247.vn" in users_map_first
    assert "admin@space247.vn" in users_map_first
    assert "agent@space247.vn" in users_map_first
    assert "user@space247.vn" in users_map_first
    assert len(added_users) == 5
    assert all(u.role in ("superadmin", "admin", "agent", "host", "user") for u in added_users)

    # 2. Second run: Users already exist
    existing_host = MagicMock()
    existing_host.role = "host"
    existing_host.email = "host@space247.vn"
    existing_superadmin = MagicMock()
    existing_superadmin.role = "superadmin"
    existing_superadmin.email = "superadmin@space247.vn"
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
        params = getattr(stmt, "_compile_state", None)
        try:
            param_values = [p.value for p in stmt._bind_params.values()]
        except Exception:
            param_values = []

        if any("host@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_host
        elif any("superadmin@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_superadmin
        elif any("admin@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_admin
        elif any("agent@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_agent
        elif any("user@space247.vn" in str(v) for v in param_values):
            res.scalar_one_or_none.return_value = existing_user
        else:
            order_map = [existing_host, existing_superadmin, existing_admin, existing_agent, existing_user]
            res.scalar_one_or_none.return_value = order_map[call_count % len(order_map)]
        call_count += 1
        return res

    mock_session.execute = fake_execute_existing_users
    added_users.clear()

    users_map_second = await seed_users(session=mock_session)
    assert len(users_map_second) == 5
    assert users_map_second["host@space247.vn"].role == "host"
    assert users_map_second["superadmin@space247.vn"].role == "superadmin"
    assert users_map_second["admin@space247.vn"].role == "superadmin"
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
    assert len(SAMPLE_PROJECTS) >= 6, f"Expected at least 6 projects, got {len(SAMPLE_PROJECTS)}"

    slugs = [item["slug"] for item in SAMPLE_PROJECTS]
    assert len(slugs) == len(set(slugs)), "Duplicate project slugs detected"

    cities = {item["city"] for item in SAMPLE_PROJECTS}
    assert any("Hồ Chí Minh" in city for city in cities)
    assert any("Hà Nội" in city for city in cities)
    assert any("Đà Nẵng" in city for city in cities)

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
        assert isinstance(item.get("images"), list) and len(item["images"]) > 0
        assert item.get("master_plan_url"), "Project missing master_plan_url"

        # Validate against ProjectBase schema
        ProjectBase(**item)


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
    assert isinstance(added_projects[0].geom, WKTElement)
    assert added_projects[0].geom.srid == 4326
    assert str(added_projects[0].geom.data) == "POINT(106.7 10.77)"
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


def test_sample_rental_properties_structure_and_diversity():
    """Verify sample rental properties and units completeness, business rules, and Pydantic schema validity."""
    assert len(SAMPLE_RENTAL_PROPERTIES) >= 10, f"Expected at least 10 rental properties, got {len(SAMPLE_RENTAL_PROPERTIES)}"

    total_units = sum(len(rp.get("units", [])) for rp in SAMPLE_RENTAL_PROPERTIES)
    assert total_units >= 25, f"Expected at least 25 rental units across properties, got {total_units}"

    models = {rp["property_model"] for rp in SAMPLE_RENTAL_PROPERTIES}
    assert {"boarding_house", "serviced_apartment"}.issubset(models)

    for rp in SAMPLE_RENTAL_PROPERTIES:
        assert rp.get("name"), "Rental property missing name"
        assert rp.get("description"), "Rental property missing description"
        assert rp.get("address"), "Rental property missing address"
        assert rp.get("city"), "Rental property missing city"
        assert rp.get("shared_costs"), "Rental property missing shared_costs"
        assert "electricity_per_kwh" in rp["shared_costs"] or "electricity_billing" in rp["shared_costs"], "Missing electricity cost specification"
        assert rp.get("shared_rules"), "Rental property missing shared_rules"
        assert len(rp.get("units", [])) >= 2, f"Property {rp['name']} should have at least 2 units"

        # Validate with RentalPropertyBase schema
        rpd = dict(rp)
        units = rpd.pop("units", [])
        rpd.pop("images", None)
        RentalPropertyBase(**rpd)

        for u in units:
            assert u.get("unit_number"), "Unit missing unit_number"
            assert u.get("price") and u["price"] > 0, "Invalid unit price"
            assert u.get("deposit") and u["deposit"] > 0, "Invalid unit deposit"
            assert u.get("area_sqm") and u["area_sqm"] > 0, "Invalid unit area_sqm"
            assert u.get("status") in ("available", "rented", "occupied", "maintenance")
            assert "has_mezzanine" in u
            assert "has_private_bathroom" in u
            # Validate with RentalUnitBase schema
            RentalUnitBase(**u)


@pytest.mark.asyncio
async def test_seed_rental_properties_logic_and_idempotency():
    """Verify that seed_rental_properties creates buildings and units idempotently."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()

    sample_rental_data = [
        {
            "name": "Nhà Trọ Thử Nghiệm",
            "description": "Mô tả nhà trọ",
            "property_model": "boarding_house",
            "address": "12 Cầu Giấy",
            "city": "Thành phố Hà Nội",
            "district": "Quận Cầu Giấy",
            "ward": "Dịch Vọng",
            "latitude": 21.03,
            "longitude": 105.79,
            "shared_costs": {"electricity_per_kwh": 3500, "electricity_billing": "fixed"},
            "shared_rules": {"allow_pets": False},
            "images": ["https://example.com/rental.jpg"],
            "units": [
                {
                    "unit_number": "P.101",
                    "floor": 1,
                    "area_sqm": 22.0,
                    "price": 3500000.0,
                    "deposit": 3500000.0,
                    "status": "available",
                    "furnishing": "fully_furnished",
                    "has_mezzanine": True,
                    "has_private_bathroom": True,
                    "max_occupants": 2,
                    "images": ["https://example.com/unit101.jpg"],
                }
            ],
        }
    ]

    added_objects = []
    mock_session.add = lambda obj: added_objects.append(obj)

    # 1. First run: Property and unit do not exist
    mock_result_none = MagicMock()
    mock_result_none.scalar_one_or_none.return_value = None

    async def fake_execute_empty(stmt):
        return mock_result_none

    mock_session.execute = fake_execute_empty

    host_id = uuid.uuid4()

    stats_first = await seed_rental_properties(
        session=mock_session,
        rentals_data=sample_rental_data,
        host_id=host_id,
    )

    assert stats_first["created_properties"] == 1
    assert stats_first["created_units"] == 1
    assert stats_first["skipped_properties"] == 0
    assert len(added_objects) == 2  # 1 property + 1 unit

    # 2. Second run: Property and unit already exist
    mock_existing_prop = MagicMock()
    mock_existing_prop.id = uuid.uuid4()
    mock_existing_prop.name = "Nhà Trọ Thử Nghiệm"

    mock_existing_unit = MagicMock()
    mock_existing_unit.id = uuid.uuid4()
    mock_existing_unit.unit_number = "P.101"

    added_objects.clear()
    call_count = 0

    async def fake_execute_existing(stmt):
        nonlocal call_count
        call_count += 1
        res = MagicMock()
        # First call checks rental property, second checks unit
        if call_count % 2 == 1:
            res.scalar_one_or_none.return_value = mock_existing_prop
        else:
            res.scalar_one_or_none.return_value = mock_existing_unit
        return res

    mock_session.execute = fake_execute_existing

    stats_second = await seed_rental_properties(
        session=mock_session,
        rentals_data=sample_rental_data,
        host_id=host_id,
    )

    assert stats_second["created_properties"] == 0
    assert stats_second["created_units"] == 0
    assert stats_second["skipped_properties"] == 1
    assert len(added_objects) == 0


@pytest.mark.asyncio
async def test_seed_contracts_invoices_and_inquiries_logic():
    """Verify that sample contracts, monthly invoices, booking inquiries, and deposit transactions are created idempotently."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()

    added_records = []
    mock_session.add = lambda obj: added_records.append(obj)

    agent_user = MagicMock()
    agent_user.id = uuid.uuid4()
    normal_user = MagicMock()
    normal_user.id = uuid.uuid4()
    normal_user.full_name = "Người Dùng Test"
    normal_user.phone = "0900000000"

    mock_unit1 = MagicMock()
    mock_unit1.id = uuid.uuid4()
    mock_unit1.property_id = uuid.uuid4()
    mock_unit1.unit_number = "P.101"
    mock_unit1.price = 3800000.0
    mock_unit1.deposit = 3800000.0

    mock_unit2 = MagicMock()
    mock_unit2.id = uuid.uuid4()
    mock_unit2.property_id = uuid.uuid4()
    mock_unit2.unit_number = "Studio 2A"
    mock_unit2.price = 9500000.0
    mock_unit2.deposit = 9500000.0

    mock_unit_inq = MagicMock()
    mock_unit_inq.id = uuid.uuid4()
    mock_unit_inq.property_id = uuid.uuid4()
    mock_unit_inq.unit_number = "P.202"
    mock_unit_inq.price = 4000000.0
    mock_unit_inq.deposit = 4000000.0

    # 1. First run: Units exist, contracts/invoices/inquiry/deposit do not exist
    async def fake_execute_first(stmt):
        res = MagicMock()
        stmt_str = str(stmt)
        if "unit_number" in stmt_str:
            try:
                pvals = [str(p.value) for p in stmt._bind_params.values()]
            except Exception:
                pvals = []
            if any("Studio 2A" in v for v in pvals):
                res.scalar_one_or_none.return_value = mock_unit2
            elif any("P.202" in v for v in pvals):
                res.scalar_one_or_none.return_value = mock_unit_inq
            else:
                res.scalar_one_or_none.return_value = mock_unit1
        else:
            res.scalar_one_or_none.return_value = None
        return res

    mock_session.execute = fake_execute_first

    stats_first = await seed_contracts_invoices_and_inquiries(
        session=mock_session,
        agent_user=agent_user,
        normal_user=normal_user,
    )

    assert stats_first["contracts"] == 2
    assert stats_first["invoices"] == 2
    assert stats_first["inquiries"] == 1
    assert len(added_records) >= 5

    # 2. Second run: Everything already exists
    mock_existing_obj = MagicMock()

    async def fake_execute_second(stmt):
        res = MagicMock()
        stmt_str = str(stmt)
        if "unit_number" in stmt_str:
            res.scalar_one_or_none.return_value = mock_unit1
        else:
            res.scalar_one_or_none.return_value = mock_existing_obj
        return res

    mock_session.execute = fake_execute_second
    added_records.clear()

    stats_second = await seed_contracts_invoices_and_inquiries(
        session=mock_session,
        agent_user=agent_user,
        normal_user=normal_user,
    )

    assert stats_second["contracts"] == 0
    assert stats_second["invoices"] == 0
    assert stats_second["inquiries"] == 0
    assert len(added_records) == 0


@pytest.mark.asyncio
async def test_reindex_all_vectors_logic():
    """Verify that reindex_all_vectors recomputes 768-dim embeddings for all properties and projects."""
    from scripts.seed_properties import reindex_all_vectors

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_prop = MagicMock()
    mock_prop.id = uuid.uuid4()
    mock_prop.title = "Căn hộ Test Reindex"
    mock_prop.property_type = "apartment"
    mock_prop.listing_type = "rent"
    mock_prop.price = 10000000.0
    mock_prop.currency = "VND"
    mock_prop.area_sqm = 60.0
    mock_prop.num_bedrooms = 2
    mock_prop.num_bathrooms = 1
    mock_prop.address = "123 Test"
    mock_prop.ward = "Test Ward"
    mock_prop.district = "Test District"
    mock_prop.city = "Hà Nội"
    mock_prop.description = "Test description"
    mock_prop.rental_type = "serviced_apartment"
    mock_prop.rental_costs = None
    mock_prop.rental_rules = None

    mock_proj = MagicMock()
    mock_proj.id = uuid.uuid4()
    mock_proj.name = "Dự án Test Reindex"
    mock_proj.developer = "Chủ đầu tư Test"
    mock_proj.address = "456 Test"
    mock_proj.district = "Test District"
    mock_proj.city = "Hà Nội"
    mock_proj.description = "Test project description"
    mock_proj.amenities = ["Hồ bơi", "Gym"]

    call_idx = 0

    async def fake_execute(stmt):
        nonlocal call_idx
        res = MagicMock()
        if call_idx == 0:
            res.scalars.return_value.all.return_value = [mock_prop]
        else:
            res.scalars.return_value.all.return_value = [mock_proj]
        call_idx += 1
        return res

    mock_session.execute = fake_execute

    reindexed_count = await reindex_all_vectors(session=mock_session)
    assert reindexed_count == 2
    assert len(mock_prop.embedding) == 768
    assert len(mock_proj.embedding) == 768

