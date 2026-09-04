from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from src.api.v1.endpoints.properties import _sanitize_tsquery
from src.core.config import settings
from src.core.database import get_db_session
from src.main import app
from src.models.property import Property
from src.schemas.property import (
    PropertySearchQuery,
    PropertySearchResponse,
    SearchResultItem,
)
from src.services.embedding import get_embedding_service


class MockEmbeddingService:
    def __init__(self, dim: int = 768):
        self.dim = dim
        self.call_count = 0
        self.last_text = None
        self.last_is_query = None

    def generate_embedding(self, text: str, is_query: bool = False) -> list[float]:
        self.call_count += 1
        self.last_text = text
        self.last_is_query = is_query
        return [0.05] * self.dim

    def build_property_text(self, **kwargs) -> str:
        parts = [kwargs.get("title", ""), kwargs.get("description", "")]
        return " ".join(filter(None, parts))


@pytest.fixture
def mock_embedding_svc():
    return MockEmbeddingService(dim=768)


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def test_hnsw_index_defined_on_property_model():
    """Verify HNSW vector index is defined with m=16, ef_construction=64, vector_cosine_ops."""
    indexes = Property.__table__.indexes
    hnsw_index = next((idx for idx in indexes if idx.name == "ix_properties_embedding_hnsw"), None)
    assert hnsw_index is not None, "ix_properties_embedding_hnsw index must be defined"
    assert hnsw_index.dialect_options["postgresql"]["using"] == "hnsw"
    assert hnsw_index.dialect_options["postgresql"]["with"] == {"m": 16, "ef_construction": 64}
    assert hnsw_index.dialect_options["postgresql"]["ops"] == {"embedding": "vector_cosine_ops"}

    # Validate generated DDL syntax
    ddl = str(CreateIndex(hnsw_index).compile(dialect=postgresql.dialect()))
    assert "USING hnsw (embedding vector_cosine_ops)" in ddl
    assert "WITH (m = 16, ef_construction = 64)" in ddl


def test_fts_gin_index_defined_on_property_model():
    """Verify GIN full-text search index is defined on title, address, and description."""
    indexes = Property.__table__.indexes
    fts_index = next((idx for idx in indexes if idx.name == "ix_properties_fts"), None)
    assert fts_index is not None, "ix_properties_fts index must be defined"
    assert fts_index.dialect_options["postgresql"]["using"] == "gin"

    ddl = str(CreateIndex(fts_index).compile(dialect=postgresql.dialect()))
    assert "USING gin" in ddl
    assert "to_tsvector" in ddl
    assert "'simple'" in ddl
    assert "coalesce(district" in ddl
    assert "coalesce(city" in ddl


def test_sanitize_tsquery_vietnamese_phrases():
    """Verify _sanitize_tsquery extracts tokens and joins with OR operator (|)."""
    assert _sanitize_tsquery("") == ""
    assert _sanitize_tsquery("   ") == ""
    assert _sanitize_tsquery("a") == ""  # Single-character tokens ignored
    tsquery = _sanitize_tsquery("Chung cư Masteri Thảo Điền 2PN!")
    assert "Chung" in tsquery
    assert "cư" in tsquery
    assert "Masteri" in tsquery
    assert "Thảo" in tsquery
    assert "Điền" in tsquery
    assert "2PN" in tsquery
    assert " | " in tsquery


def test_property_search_query_schema_hybrid_defaults():
    """Verify PropertySearchQuery defaults to enable_hybrid=True and rrf_k=60."""
    query = PropertySearchQuery(query="Căn hộ cao cấp Vinhomes")
    assert query.enable_hybrid is True
    assert query.rrf_k == 60


def test_search_result_item_rrf_and_ranks_serialization():
    """Verify SearchResultItem properly serializes rrf_score, vector_rank, and fts_rank."""
    prop_id = uuid.uuid4()
    item = SearchResultItem(
        property={
            "id": prop_id,
            "title": "Biệt thự Thảo Điền",
            "description": "Biệt thự hồ bơi view sông",
            "property_type": "villa",
            "listing_type": "sale",
            "price": 85000000000.0,
            "currency": "VND",
            "area_sqm": 450.0,
            "num_bedrooms": 5,
            "num_bathrooms": 6,
            "address": "12 Nguyễn Văn Hưởng",
            "ward": "Thảo Điền",
            "district": "Quận 2",
            "city": "Hồ Chí Minh",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        similarity_score=0.92,
        rrf_score=0.032258,
        vector_rank=1,
        fts_rank=2,
    )
    dumped = item.model_dump()
    assert dumped["similarity_score"] == 0.92
    assert dumped["rrf_score"] == 0.032258
    assert dumped["vector_rank"] == 1
    assert dumped["fts_rank"] == 2


@pytest.mark.asyncio
async def test_hybrid_search_rrf_ranking_fusion(mock_db_session, mock_embedding_svc):
    """
    Given two properties:
    - Property A: Vector rank 1 (distance 0.05 -> sim 0.95), FTS rank 2
    - Property B: Vector rank 2 (distance 0.15 -> sim 0.85), FTS rank 1
    - Property C: Vector only, rank 3
    When calling POST /api/v1/properties/search with enable_hybrid=True (rrf_k=60),
    Then properties with both vector and keyword matches score highest via RRF.
    """
    prop_a = Property(
        id=uuid.uuid4(),
        title="Chung cư Masteri Thảo Điền",
        description="Căn hộ 2 phòng ngủ nội thất cao cấp",
        property_type="apartment",
        listing_type="rent",
        price=22000000.0,
        currency="VND",
        area_sqm=75.0,
        num_bedrooms=2,
        address="159 Xa Lộ Hà Nội",
        district="Quận 2",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    prop_b = Property(
        id=uuid.uuid4(),
        title="Căn hộ Masteri Thảo Điền view hồ bơi",
        description="Cho thuê gấp Masteri Thảo Điền",
        property_type="apartment",
        listing_type="rent",
        price=24000000.0,
        currency="VND",
        area_sqm=80.0,
        num_bedrooms=2,
        address="159 Xa Lộ Hà Nội",
        district="Quận 2",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    prop_c = Property(
        id=uuid.uuid4(),
        title="Nhà phố Bình Thạnh",
        description="Nhà phố đẹp khu yên tĩnh",
        property_type="house",
        listing_type="rent",
        price=20000000.0,
        currency="VND",
        area_sqm=70.0,
        num_bedrooms=2,
        address="Bạch Đằng",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # First db.execute: vector search candidates (prop_a, prop_b, prop_c)
    # Second db.execute: FTS search candidates (prop_b at rank 1, prop_a at rank 2)
    mock_vector_result = MagicMock()
    mock_vector_result.all.return_value = [
        (prop_a, 0.05),  # vector_rank 1
        (prop_b, 0.15),  # vector_rank 2
        (prop_c, 0.30),  # vector_rank 3
    ]

    mock_fts_result = MagicMock()
    mock_fts_result.all.return_value = [
        (prop_b, 0.85),  # fts_rank 1
        (prop_a, 0.40),  # fts_rank 2
    ]

    mock_db_session.execute.side_effect = [mock_vector_result, mock_fts_result]

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    payload = {
        "query": "Masteri Thảo Điền 2 phòng ngủ",
        "enable_hybrid": True,
        "rrf_k": 60,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        results = data["results"]

        # Expected RRF calculations with k=60:
        # A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
        # B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.032522 (tied RRF; tie-broken by sim: A sim 0.95 vs B sim 0.85 -> A first)
        # C: 1/(60+3) = 1/63 = 0.015873 (lowest)
        assert results[0]["property"]["id"] == str(prop_a.id)
        assert results[0]["rrf_score"] == pytest.approx(0.032522, abs=1e-4)
        assert results[0]["vector_rank"] == 1
        assert results[0]["fts_rank"] == 2

        assert results[1]["property"]["id"] == str(prop_b.id)
        assert results[1]["rrf_score"] == pytest.approx(0.032522, abs=1e-4)
        assert results[1]["vector_rank"] == 2
        assert results[1]["fts_rank"] == 1

        assert results[2]["property"]["id"] == str(prop_c.id)
        assert results[2]["rrf_score"] == pytest.approx(0.015873, abs=1e-4)
        assert results[2]["vector_rank"] == 3
        assert results[2]["fts_rank"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pure_vector_search_when_hybrid_disabled(mock_db_session, mock_embedding_svc):
    """
    Given search request with enable_hybrid=False,
    When calling POST /api/v1/properties/search,
    Then only vector search query runs and rrf_score is None.
    """
    prop = Property(
        id=uuid.uuid4(),
        title="Căn hộ Sunwah Pearl",
        description="View sông Sài Gòn tuyệt đẹp",
        property_type="apartment",
        listing_type="sale",
        price=8000000000.0,
        currency="VND",
        area_sqm=90.0,
        num_bedrooms=2,
        address="90 Nguyễn Hữu Cảnh",
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

    payload = {
        "query": "căn hộ Sunwah Pearl",
        "enable_hybrid": False,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        res = data["results"][0]
        assert res["property"]["title"] == prop.title
        assert res["similarity_score"] == 0.90
        assert res["rrf_score"] is None
        assert res["vector_rank"] == 1
        assert res["fts_rank"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_hybrid_search_fts_only_candidate(mock_db_session, mock_embedding_svc):
    """
    Given a property matching only on keywords (FTS) and not returned in vector top-K,
    When calling POST /api/v1/properties/search with enable_hybrid=True,
    Then the candidate is included in fused results with valid rrf_score and fts_rank.
    """
    prop_fts = Property(
        id=uuid.uuid4(),
        title="Đất nền Thổ cư Củ Chi",
        description="Đất đẹp phân lô sổ hồng riêng Củ Chi",
        property_type="land",
        listing_type="sale",
        price=1800000000.0,
        currency="VND",
        area_sqm=200.0,
        address="Tỉnh lộ 8",
        ward="Tân An Hội",
        district="Củ Chi",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_vector_result = MagicMock()
    mock_vector_result.all.return_value = []

    mock_fts_result = MagicMock()
    mock_fts_result.all.return_value = [(prop_fts, 0.95)]

    mock_db_session.execute.side_effect = [mock_vector_result, mock_fts_result]

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    payload = {
        "query": "Đất nền Củ Chi sổ hồng",
        "enable_hybrid": True,
        "rrf_k": 60,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        res = data["results"][0]
        assert res["property"]["id"] == str(prop_fts.id)
        assert res["vector_rank"] is None
        assert res["fts_rank"] == 1
        assert res["rrf_score"] == pytest.approx(1.0 / (60 + 1), abs=1e-5)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_hybrid_search_fts_failure_graceful_fallback(mock_db_session, mock_embedding_svc):
    """
    Given a database where FTS execution throws an exception,
    When calling POST /api/v1/properties/search with enable_hybrid=True,
    Then it gracefully degrades to vector-only results without returning HTTP 500.
    """
    prop = Property(
        id=uuid.uuid4(),
        title="Nhà phố Quận 7",
        description="Nhà phố khu dân cư Him Lam",
        property_type="house",
        listing_type="sale",
        price=12000000000.0,
        currency="VND",
        area_sqm=100.0,
        address="Đường số 7",
        district="Quận 7",
        city="Hồ Chí Minh",
        embedding=[0.05] * 768,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_vector_result = MagicMock()
    mock_vector_result.all.return_value = [(prop, 0.12)]

    # First call succeeds (vector), second call raises (FTS exception)
    mock_db_session.execute.side_effect = [mock_vector_result, RuntimeError("Simulated FTS execution failure")]

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_svc

    payload = {
        "query": "Nhà phố Quận 7",
        "enable_hybrid": True,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"{settings.API_V1_STR}/properties/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["property"]["title"] == prop.title

    app.dependency_overrides.clear()

