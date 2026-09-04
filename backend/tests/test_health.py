from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import settings
from src.core.database import get_db_session
from src.main import create_app

app = create_app()


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing without a live database."""
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify service root endpoint provides API metadata and links."""
    assert settings.APP_NAME == "Space247"
    assert app.title == "Space247 Real Estate API"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == settings.PROJECT_NAME
        assert data["version"] == settings.VERSION
        assert data["health"] == f"{settings.API_V1_STR}/health"


@pytest.mark.asyncio
async def test_openapi_schema_generation():
    """Verify OpenAPI JSON specification is generated correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{settings.API_V1_STR}/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Space247 Real Estate API"
        assert "paths" in schema
        assert f"{settings.API_V1_STR}/health" in schema["paths"]
        assert f"{settings.API_V1_STR}/properties" in schema["paths"]
        assert f"{settings.API_V1_STR}/search/semantic" in schema["paths"]


@pytest.mark.asyncio
async def test_health_check_healthy(mock_db_session):
    """
    Given a running database with pgvector installed,
    When calling GET /api/v1/health,
    Then response is HTTP 200 with status: healthy, database: connected, pgvector: enabled, vector_dim: 768.
    """
    # Mock successful DB scalar result (SELECT 1 -> 1)
    db_result = MagicMock()
    db_result.scalar.return_value = 1

    # Mock pgvector extension check result
    vector_result = MagicMock()
    vector_result.first.return_value = ("vector", "0.5.0")

    mock_db_session.execute.side_effect = [db_result, vector_result]

    async def override_get_db() -> AsyncGenerator:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{settings.API_V1_STR}/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "database": "connected",
            "pgvector": "enabled",
            "vector_dim": settings.VECTOR_DIM,
        }

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check_vector_missing(mock_db_session):
    """
    Given a database without pgvector extension,
    When calling GET /api/v1/health,
    Then response is HTTP 503.
    """
    db_result = MagicMock()
    db_result.scalar.return_value = 1

    vector_result = MagicMock()
    vector_result.first.return_value = None  # No vector extension

    mock_db_session.execute.side_effect = [db_result, vector_result]

    async def override_get_db() -> AsyncGenerator:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{settings.API_V1_STR}/health")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["pgvector"] == "disabled"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check_database_unreachable(mock_db_session):
    """
    Given a failing database connection,
    When calling GET /api/v1/health,
    Then response is HTTP 503.
    """
    mock_db_session.execute.side_effect = Exception("Connection refused")

    async def override_get_db() -> AsyncGenerator:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{settings.API_V1_STR}/health")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "disconnected"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_semantic_search_vector_dimension_mismatch():
    """
    Given an embedding vector with length != 768,
    When calling POST /api/v1/search/semantic,
    Then response is HTTP 400 Bad Request with explicit dimension mismatch detail.
    """
    invalid_vector = [0.1] * 512  # Mismatch: 512 instead of 768

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"{settings.API_V1_STR}/search/semantic",
            json={"query_vector": invalid_vector, "listing_type": "sale"},
        )
        assert response.status_code == 400
        data = response.json()
        assert (
            data["detail"]
            == f"Query vector dimension mismatch: expected {settings.VECTOR_DIM}, got 512"
        )


@pytest.mark.asyncio
async def test_semantic_search_malformed_filter():
    """
    Given a malformed payload (e.g. invalid listing_type or missing query_vector),
    When calling POST /api/v1/search/semantic,
    Then response is HTTP 422 Unprocessable Entity.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid listing_type enum
        response = await client.post(
            f"{settings.API_V1_STR}/search/semantic",
            json={"query_vector": [0.1] * 768, "listing_type": "invalid_type"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_semantic_search_valid_query(mock_db_session):
    """
    Given a valid 768-dim query vector,
    When calling POST /api/v1/search/semantic,
    Then response is HTTP 200 with ranked list of properties and cosine similarity scores.
    """
    from datetime import datetime, timezone
    import uuid
    from src.models.property import Property

    prop_id = uuid.uuid4()
    mock_prop = Property(
        id=prop_id,
        title="Căn hộ cao cấp 2PN Landmark 81",
        description="Căn hộ view sông Sài Gòn, đầy đủ nội thất cao cấp.",
        property_type="apartment",
        listing_type="rent",
        price=35000000.0,
        currency="VND",
        area_sqm=85.5,
        num_bedrooms=2,
        num_bathrooms=2,
        address="720A Điện Biên Phủ",
        district="Bình Thạnh",
        city="Hồ Chí Minh",
        status="active",
        embedding=[0.05] * 768,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock DB query result returning (property, distance)
    # Cosine distance = 0.15 -> Cosine similarity = 0.85
    mock_result = MagicMock()
    mock_result.all.return_value = [(mock_prop, 0.15)]
    mock_db_session.execute.return_value = mock_result

    async def override_get_db() -> AsyncGenerator:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"{settings.API_V1_STR}/search/semantic",
            json={
                "query_vector": [0.05] * 768,
                "listing_type": "rent",
                "city": "Hồ Chí Minh",
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["vector_dim"] == 768
        assert len(data["results"]) == 1
        result_item = data["results"][0]
        assert result_item["similarity_score"] == 0.85
        assert result_item["property"]["title"] == "Căn hộ cao cấp 2PN Landmark 81"
        assert result_item["property"]["listing_type"] == "rent"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_property_creation_with_valid_and_invalid_embedding(mock_db_session):
    """
    Test property creation endpoint:
    - Embedding length != 768 should return 400 Bad Request.
    - Valid embedding should return 201 Created.
    """
    async def override_get_db() -> AsyncGenerator:
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid embedding dimension
        invalid_payload = {
            "title": "Nhà phố liền kề Thảo Điền",
            "description": "Nhà phố hiện đại 1 trệt 2 lầu có sân vườn riêng.",
            "property_type": "house",
            "listing_type": "sale",
            "price": 18500000000.0,
            "currency": "VND",
            "area_sqm": 120.0,
            "num_bedrooms": 3,
            "num_bathrooms": 3,
            "address": "12 Đường số 10",
            "district": "Quận 2",
            "city": "Hồ Chí Minh",
            "embedding": [0.1] * 100,  # Invalid dimension
        }
        response = await client.post(
            f"{settings.API_V1_STR}/properties",
            json=invalid_payload,
        )
        assert response.status_code == 400
        assert "dimension mismatch" in response.json()["detail"]

        # Valid payload with 768 dimensions
        valid_payload = {
            "title": "Nhà phố liền kề Thảo Điền",
            "description": "Nhà phố hiện đại 1 trệt 2 lầu có sân vườn riêng.",
            "property_type": "house",
            "listing_type": "sale",
            "price": 18500000000.0,
            "currency": "VND",
            "area_sqm": 120.0,
            "num_bedrooms": 3,
            "num_bathrooms": 3,
            "address": "12 Đường số 10",
            "district": "Quận 2",
            "city": "Hồ Chí Minh",
            "embedding": [0.02] * 768,
        }
        response_valid = await client.post(
            f"{settings.API_V1_STR}/properties",
            json=valid_payload,
        )
        assert response_valid.status_code == 201
        created_data = response_valid.json()
        assert created_data["title"] == valid_payload["title"]
        assert created_data["status"] == "active"
        assert "id" in created_data

    app.dependency_overrides.clear()
