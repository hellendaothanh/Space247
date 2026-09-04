from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.core.database import get_db_session
from src.main import create_app
from src.models.property import Property
from src.schemas.property import ListingType, PropertyType
from src.services.embedding import EmbeddingService, get_embedding_service

app = create_app()


class MockEmbeddingService(EmbeddingService):
    """Deterministic mock embedding service for lightning-fast testing without network/model loading."""

    def __init__(self, vector_dim: int = 768, model_name: str | None = None):
        super().__init__(model_name=model_name, vector_dim=vector_dim)
        self.call_count = 0
        self.last_text: str | None = None
        self.last_is_query: bool | None = None

    def generate_embedding(self, text: str, is_query: bool = False) -> list[float]:
        self.call_count += 1
        self.last_text = text
        self.last_is_query = is_query
        if not text or not text.strip():
            return [0.0] * self.vector_dim
        # Return a deterministic 768-dimensional vector based on text length
        val = (len(text) % 100) / 100.0
        return [val] * self.vector_dim

    def generate_embeddings(
        self, texts: list[str], is_query: bool = False
    ) -> list[list[float]]:
        return [self.generate_embedding(t, is_query=is_query) for t in texts]


@pytest.fixture
def mock_embedding_svc():
    return MockEmbeddingService()


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# 1. Unit Tests for EmbeddingService
# ---------------------------------------------------------------------------


def test_embedding_service_text_builder():
    """Verify build_property_text joins title, description, and location details."""
    service = EmbeddingService()
    text = service.build_property_text(
        title="Biệt thự Thảo Điền ven sông",
        description="Biệt thự đơn lập 5 phòng ngủ có hồ bơi riêng",
        address="12 Quốc Hương",
        ward="Thảo Điền",
        district="Thủ Đức",
        city="Hồ Chí Minh",
    )
    assert "Biệt thự Thảo Điền ven sông" in text
    assert "Biệt thự đơn lập 5 phòng ngủ có hồ bơi riêng" in text
    assert "Địa chỉ: 12 Quốc Hương, Thảo Điền, Thủ Đức, Hồ Chí Minh" in text


def test_embedding_service_empty_text():
    """Verify empty or whitespace text generates a zero vector of length VECTOR_DIM."""
    service = EmbeddingService()
    vec = service.generate_embedding("")
    assert len(vec) == settings.VECTOR_DIM
    assert all(v == 0.0 for v in vec)

    vec_spaces = service.generate_embedding("   \n\t  ")
    assert len(vec_spaces) == settings.VECTOR_DIM
    assert all(v == 0.0 for v in vec_spaces)


def test_embedding_service_batch_empty():
    """Verify batch embedding on empty input returns empty list."""
    service = EmbeddingService()
    assert service.generate_embeddings([]) == []


# ---------------------------------------------------------------------------
# 2. Integration Tests: Property Create with Auto-Embedding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_property_auto_embedding(mock_db_session, mock_embedding_svc):
    """
    Given a property payload without an embedding vector,
    When calling POST /api/v1/properties,
    Then an embedding is automatically generated from title + description + address and stored.
    """
    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    payload = {
        "title": "Căn hộ Vinhomes Central Park 3PN",
        "description": "Căn hộ cao cấp view công viên và sông Sài Gòn, nội thất đầy đủ.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 28000000.0,
        "currency": "VND",
        "area_sqm": 105.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "208 Nguyễn Hữu Cảnh",
        "ward": "Phường 22",
        "district": "Bình Thạnh",
        "city": "Hồ Chí Minh",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["listing_type"] == "rent"
        assert mock_embedding_svc.call_count == 1
        assert "Vinhomes Central Park" in mock_embedding_svc.last_text
        assert "Địa chỉ: 208 Nguyễn Hữu Cảnh" in mock_embedding_svc.last_text

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_property_explicit_embedding_override(mock_db_session, mock_embedding_svc):
    """
    Given a property payload with an explicit 768-dim embedding,
    When calling POST /api/v1/properties,
    Then the provided embedding is preserved without calling the embedding service.
    """
    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    custom_vector = [0.123] * settings.VECTOR_DIM
    payload = {
        "title": "Nhà phố thương mại Shophouse Sala",
        "description": "Mặt tiền đại lộ Mai Chí Thọ thuận tiện kinh doanh.",
        "property_type": "commercial",
        "listing_type": "sale",
        "price": 45000000000.0,
        "area_sqm": 250.0,
        "address": "10 Mai Chí Thọ",
        "district": "Quận 2",
        "city": "Hồ Chí Minh",
        "embedding": custom_vector,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties", json=payload)
        assert response.status_code == 201
        assert mock_embedding_svc.call_count == 0  # Service was not called because embedding was provided

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Integration Tests: Property Update with Auto-Embedding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_property_auto_regenerates_embedding(mock_db_session, mock_embedding_svc):
    """
    Given an existing property,
    When calling PUT /api/v1/properties/{id} to update the title or description,
    Then the embedding is automatically re-generated from the updated fields.
    """
    prop_id = uuid.uuid4()
    mock_prop = Property(
        id=prop_id,
        title="Tiêu đề cũ",
        description="Mô tả cũ về bất động sản.",
        property_type="house",
        listing_type="sale",
        price=10000000000.0,
        currency="VND",
        area_sqm=100.0,
        address="100 Lê Lợi",
        district="Quận 1",
        city="Hồ Chí Minh",
        embedding=[0.01] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = mock_prop
    mock_db_session.execute.return_value = db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    update_payload = {
        "title": "Nhà phố Quận 1 mặt tiền kinh doanh sầm uất",
        "description": "Nhà mới xây 4 tầng, vị trí đắc địa trung tâm Quận 1.",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(f"{settings.API_V1_STR}/properties/{prop_id}", json=update_payload)
        assert response.status_code == 200
        assert mock_embedding_svc.call_count == 1
        assert "Nhà phố Quận 1 mặt tiền" in mock_embedding_svc.last_text
        assert mock_prop.title == update_payload["title"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_property_without_text_change_preserves_embedding(mock_db_session, mock_embedding_svc):
    """
    Given an existing property with an embedding,
    When calling PUT /api/v1/properties/{id} updating only non-text fields (e.g. price),
    Then the embedding is preserved without re-generating.
    """
    prop_id = uuid.uuid4()
    initial_embedding = [0.05] * 768
    mock_prop = Property(
        id=prop_id,
        title="Căn hộ Studio Masteri",
        description="Studio hiện đại đầy đủ tiện ích.",
        property_type="apartment",
        listing_type="rent",
        price=12000000.0,
        currency="VND",
        area_sqm=35.0,
        address="159 Xa Lộ Hà Nội",
        district="Quận 2",
        city="Hồ Chí Minh",
        embedding=initial_embedding,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = mock_prop
    mock_db_session.execute.return_value = db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    update_payload = {"price": 14000000.0}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(f"{settings.API_V1_STR}/properties/{prop_id}", json=update_payload)
        assert response.status_code == 200
        assert mock_embedding_svc.call_count == 0  # No text change -> no re-embedding
        assert mock_prop.price == 14000000.0

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. Integration Tests: POST /api/v1/properties/search Natural Language Search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_natural_language_search_with_filters(mock_db_session, mock_embedding_svc):
    """
    Given active properties in the database,
    When calling POST /api/v1/properties/search with a Vietnamese natural language query and filters,
    Then the query is converted to 768-dim vector, filters are applied, and ranked results returned.
    """
    prop1 = Property(
        id=uuid.uuid4(),
        title="Căn hộ 2PN Vinhomes Central Park view sông",
        description="Cho thuê căn hộ 2 phòng ngủ nội thất cao cấp tại Bình Thạnh.",
        property_type="apartment",
        listing_type="rent",
        price=22000000.0,
        currency="VND",
        area_sqm=75.0,
        address="208 Nguyễn Hữu Cảnh",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        embedding=[0.1] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    prop2 = Property(
        id=uuid.uuid4(),
        title="Căn hộ studio Sunwah Pearl",
        description="Cho thuê studio view cầu Sài Gòn giá tốt.",
        property_type="apartment",
        listing_type="rent",
        price=18000000.0,
        currency="VND",
        area_sqm=50.0,
        address="90 Nguyễn Hữu Cảnh",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        embedding=[0.1] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock DB query results with cosine distance
    # prop1 distance = 0.12 -> similarity = 0.88
    # prop2 distance = 0.25 -> similarity = 0.75
    mock_db_result = MagicMock()
    mock_db_result.all.return_value = [(prop1, 0.12), (prop2, 0.25)]
    mock_db_session.execute.return_value = mock_db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    search_payload = {
        "query": "Cần tìm thuê căn hộ 2 phòng ngủ view sông đẹp ở Bình Thạnh",
        "listing_type": "rent",
        "property_type": "apartment",
        "city": "Hồ Chí Minh",
        "district": "Bình Thạnh",
        "min_price": 15000000.0,
        "max_price": 30000000.0,
        "limit": 5,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=search_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["vector_dim"] == 768
        assert data["query"] == search_payload["query"]

        results = data["results"]
        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.88
        assert results[0]["property"]["title"] == prop1.title
        assert results[0]["property"]["listing_type"] == "rent"
        assert results[1]["similarity_score"] == 0.75

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_natural_language_search_threshold_filter(mock_db_session, mock_embedding_svc):
    """
    Given search results with various similarity scores,
    When threshold is provided,
    Then results below threshold are filtered out.
    """
    prop = Property(
        id=uuid.uuid4(),
        title="Nhà mặt tiền Quận 10",
        description="Bán nhà mặt tiền thuận tiện kinh doanh.",
        property_type="house",
        listing_type="sale",
        price=15000000000.0,
        currency="VND",
        area_sqm=80.0,
        address="3 Tháng 2",
        district="Quận 10",
        city="Hồ Chí Minh",
        embedding=[0.1] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # distance = 0.35 -> similarity = 0.65
    mock_db_result = MagicMock()
    mock_db_result.all.return_value = [(prop, 0.35)]
    mock_db_session.execute.return_value = mock_db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    # Query with threshold 0.8 (higher than 0.65) -> expect 0 results
    search_payload = {
        "query": "Tìm biệt thự sân vườn",
        "threshold": 0.8,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=search_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["results"]) == 0

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_natural_language_search_validation_empty_query():
    """
    Given an empty or missing query string,
    When calling POST /api/v1/properties/search,
    Then response is HTTP 422 Unprocessable Entity.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Missing query
        resp1 = await client.post(f"{settings.API_V1_STR}/properties/search", json={})
        assert resp1.status_code == 422

        # Empty string query
        resp2 = await client.post(f"{settings.API_V1_STR}/properties/search", json={"query": ""})
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_update_property_not_found(mock_db_session, mock_embedding_svc):
    """
    Given a non-existent property ID,
    When calling PUT /api/v1/properties/{id},
    Then response is HTTP 404 Not Found.
    """
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    random_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"{settings.API_V1_STR}/properties/{random_id}",
            json={"title": "New Title Here"},
        )
        assert response.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_property_invalid_embedding_dim(mock_db_session, mock_embedding_svc):
    """
    Given an update payload with embedding length != 768,
    When calling PUT /api/v1/properties/{id},
    Then response is HTTP 400 Bad Request.
    """
    prop_id = uuid.uuid4()
    mock_prop = Property(
        id=prop_id,
        title="Title",
        description="Description",
        property_type="house",
        listing_type="sale",
        price=5000000.0,
        area_sqm=50.0,
        address="123 Street",
        city="Hanoi",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = mock_prop
    mock_db_session.execute.return_value = db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"{settings.API_V1_STR}/properties/{prop_id}",
            json={"embedding": [0.1] * 128},  # Invalid dim
        )
        assert response.status_code == 400
        assert "dimension mismatch" in response.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_natural_language_search_mismatched_vector_dim(mock_db_session):
    """
    Given an embedding service that produces unexpected vector dimension,
    When calling POST /api/v1/properties/search,
    Then response is HTTP 400 Bad Request.
    """
    class BrokenDimEmbeddingService(EmbeddingService):
        def generate_embedding(self, text: str) -> list[float]:
            return [0.1] * 512  # Mismatched 512 instead of 768

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: BrokenDimEmbeddingService()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"{settings.API_V1_STR}/properties/search",
            json={"query": "Tìm nhà quận 1"},
        )
        assert response.status_code == 400
        assert "dimension mismatch" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_embedding_service_e5_prefix_handling():
    """Verify E5 model prefixes are automatically prepended for queries and passages."""
    service = EmbeddingService(model_name="intfloat/multilingual-e5-base")
    query_text = service._prepare_text("căn hộ cao cấp", is_query=True)
    assert query_text == "query: căn hộ cao cấp"

    passage_text = service._prepare_text("căn hộ cao cấp", is_query=False)
    assert passage_text == "passage: căn hộ cao cấp"

    # Already prefixed text should not duplicate prefix
    assert service._prepare_text("query: test", is_query=True) == "query: test"
    assert service._prepare_text("passage: test", is_query=False) == "passage: test"


def test_embedding_service_build_property_text_rich_metadata():
    """Verify build_property_text includes property_type, listing_type, and num_bedrooms."""
    service = EmbeddingService()
    text = service.build_property_text(
        title="Penthouse Landmark 81",
        description="Penthouse triệu đô đỉnh cao tiện ích.",
        address="720A Điện Biên Phủ",
        ward="Phường 22",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        property_type="apartment",
        listing_type="sale",
        num_bedrooms=4,
    )
    assert "Penthouse Landmark 81" in text
    assert "Loại hình: apartment" in text
    assert "Hình thức: Bán" in text
    assert "4 phòng ngủ" in text
    assert "Địa chỉ: 720A Điện Biên Phủ, Phường 22, Bình Thạnh, Hồ Chí Minh" in text


@pytest.mark.asyncio
async def test_natural_language_search_with_bedroom_and_address_filters(
    mock_db_session, mock_embedding_svc
):
    """
    Given active property listings,
    When calling POST /api/v1/properties/search with num_bedrooms and address filters,
    Then the query builds with matching filter criteria and returns filtered rankings.
    """
    prop = Property(
        id=uuid.uuid4(),
        title="Căn hộ 3PN Vinhomes Central Park",
        description="View công viên trực diện, 3 phòng ngủ rộng rãi.",
        property_type="apartment",
        listing_type="rent",
        price=32000000.0,
        currency="VND",
        area_sqm=110.0,
        num_bedrooms=3,
        num_bathrooms=2,
        address="208 Nguyễn Hữu Cảnh",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_db_result = MagicMock()
    mock_db_result.all.return_value = [(prop, 0.10)]
    mock_db_session.execute.return_value = mock_db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    search_payload = {
        "query": "căn hộ 3 phòng ngủ Bình Thạnh Nguyễn Hữu Cảnh",
        "listing_type": "rent",
        "address": "Nguyễn Hữu Cảnh",
        "num_bedrooms": 3,
        "min_price": 20000000.0,
        "max_price": 40000000.0,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"{settings.API_V1_STR}/properties/search", json=search_payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["property"]["title"] == prop.title
        assert data["results"][0]["property"]["num_bedrooms"] == 3
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_property_embeds_bedroom_and_type_info(mock_db_session, mock_embedding_svc):
    """
    Given a property with num_bedrooms and property_type specified,
    When calling POST /api/v1/properties,
    Then the auto-generated text contains bedroom and property type details.
    """
    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    payload = {
        "title": "Nhà phố thương mại Shophouse Thảo Điền",
        "description": "Nhà phố 4 phòng ngủ có thang máy hiện đại.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 25000000000.0,
        "area_sqm": 150.0,
        "num_bedrooms": 4,
        "address": "55 Xuân Thủy",
        "district": "Quận 2",
        "city": "Hồ Chí Minh",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties", json=payload)
        assert response.status_code == 201
        assert mock_embedding_svc.call_count == 1
        assert "4 phòng ngủ" in mock_embedding_svc.last_text
        assert "Loại hình: house" in mock_embedding_svc.last_text
        assert "Hình thức: Bán" in mock_embedding_svc.last_text
        assert mock_embedding_svc.last_is_query is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_property_num_bedrooms_regenerates_embedding(
    mock_db_session, mock_embedding_svc
):
    """
    Given an existing property,
    When calling PUT /api/v1/properties/{id} to change num_bedrooms,
    Then the embedding is automatically re-generated with the updated bedroom count.
    """
    prop_id = uuid.uuid4()
    mock_prop = Property(
        id=prop_id,
        title="Căn hộ cao cấp 2PN",
        description="Căn hộ thiết kế mở.",
        property_type="apartment",
        listing_type="rent",
        price=18000000.0,
        currency="VND",
        area_sqm=80.0,
        num_bedrooms=2,
        address="100 Nguyễn Văn Trỗi",
        district="Phú Nhuận",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = mock_prop
    mock_db_session.execute.return_value = db_result

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    # Update num_bedrooms from 2 to 3
    update_payload = {"num_bedrooms": 3}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"{settings.API_V1_STR}/properties/{prop_id}", json=update_payload
        )
        assert response.status_code == 200
        assert mock_embedding_svc.call_count == 1
        assert "3 phòng ngủ" in mock_embedding_svc.last_text
        assert mock_prop.num_bedrooms == 3

    app.dependency_overrides.clear()


