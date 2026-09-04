import hashlib
import json
from unittest.mock import AsyncMock, patch
import uuid
import pytest

from src.core import cache
from src.core.cache import (
    generate_property_cache_key,
    generate_search_cache_key,
    get_cached_json,
    set_cached_json,
    delete_cached_key,
    invalidate_cache_pattern,
    invalidate_property_caches,
    init_redis_pool,
    close_redis_pool,
)


def test_generate_search_cache_key_determinism():
    """Verify that generate_search_cache_key produces the exact same hash regardless of dict key order."""
    payload1 = {
        "query": "căn hộ 2 phòng ngủ",
        "property_type": "apartment",
        "listing_type": "sale",
        "limit": 20,
    }
    payload2 = {
        "limit": 20,
        "listing_type": "sale",
        "query": "căn hộ 2 phòng ngủ",
        "property_type": "apartment",
    }
    key1 = generate_search_cache_key(payload1)
    key2 = generate_search_cache_key(payload2)

    assert key1 == key2
    assert key1.startswith("cache:search:")
    # Ignore None fields
    payload3 = payload1.copy()
    payload3["min_price"] = None
    assert generate_search_cache_key(payload3) == key1


def test_generate_property_cache_key():
    """Verify property cache key format."""
    prop_id = uuid.uuid4()
    key = generate_property_cache_key(prop_id)
    assert key == f"cache:property:{str(prop_id)}"


@pytest.mark.asyncio
async def test_cache_get_set_delete_with_mock_redis():
    """Verify set_cached_json, get_cached_json, and delete_cached_key with mocked Redis."""
    mock_redis = AsyncMock()
    stored_data = {"id": "123", "title": "Căn hộ Vinhomes"}
    mock_redis.get.return_value = json.dumps(stored_data)
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1

    with patch.object(cache, "get_redis", return_value=mock_redis):
        # 1. Set cache
        success = await set_cached_json("cache:property:123", stored_data, ttl=600)
        assert success is True
        mock_redis.set.assert_called_once_with(
            "cache:property:123", json.dumps(stored_data, default=str), ex=600
        )

        # 2. Get cache hit
        retrieved = await get_cached_json("cache:property:123")
        assert retrieved == stored_data
        mock_redis.get.assert_called_once_with("cache:property:123")

        # 3. Delete cache
        del_success = await delete_cached_key("cache:property:123")
        assert del_success is True
        mock_redis.delete.assert_called_once_with("cache:property:123")


@pytest.mark.asyncio
async def test_cache_graceful_degradation_when_redis_none():
    """Verify that all cache helpers gracefully return False/None/0 when Redis client is None."""
    with patch.object(cache, "get_redis", return_value=None):
        assert await get_cached_json("any_key") is None
        assert await set_cached_json("any_key", {"data": 1}) is False
        assert await delete_cached_key("any_key") is False
        assert await invalidate_cache_pattern("cache:*") == 0


@pytest.mark.asyncio
async def test_invalidate_property_caches():
    """Verify that invalidate_property_caches deletes both the property key and scans search keys."""
    mock_redis = AsyncMock()
    mock_redis.delete.return_value = 1
    # Mock SCAN returning one batch of search cache keys then ending
    mock_redis.scan.side_effect = [
        (0, ["cache:search:abc", "cache:search:def"]),
    ]

    prop_id = uuid.uuid4()
    with patch.object(cache, "get_redis", return_value=mock_redis):
        await invalidate_property_caches(prop_id)

        # Should delete single property key
        mock_redis.delete.assert_any_call(f"cache:property:{prop_id}")
        # Should scan and delete search keys
        mock_redis.scan.assert_called_with(cursor=0, match="cache:search:*", count=100)
        mock_redis.delete.assert_any_call("cache:search:abc", "cache:search:def")


@pytest.mark.asyncio
async def test_get_property_endpoint_cache_hit():
    """Verify GET /api/v1/properties/{id} returns directly from Redis cache without querying DB."""
    from httpx import ASGITransport, AsyncClient
    from src.main import app

    prop_id = uuid.uuid4()
    cached_prop = {
        "id": str(prop_id),
        "title": "Cached Villa Thao Dien",
        "description": "Luxury villa in Thao Dien",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 25000000000.0,
        "currency": "VND",
        "area_sqm": 350.0,
        "address": "123 Quoc Huong",
        "city": "Hồ Chí Minh",
        "status": "active",
        "created_at": "2026-09-04T00:00:00Z",
        "updated_at": "2026-09-04T00:00:00Z",
    }

    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached_prop)

    with patch.object(cache, "get_redis", return_value=mock_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/properties/{prop_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(prop_id)
            assert data["title"] == "Cached Villa Thao Dien"
            mock_redis.get.assert_called_once_with(f"cache:property:{prop_id}")


@pytest.mark.asyncio
async def test_search_properties_endpoint_cache_hit():
    """Verify POST /api/v1/properties/search returns directly from Redis cache."""
    from httpx import ASGITransport, AsyncClient
    from src.main import app

    cached_search = {
        "total": 1,
        "vector_dim": 768,
        "query": "villa Thao Dien",
        "results": [
            {
                "property": {
                    "id": str(uuid.uuid4()),
                    "title": "Villa Thao Dien",
                    "description": "Riverfront villa",
                    "property_type": "villa",
                    "listing_type": "sale",
                    "price": 30000000000.0,
                    "currency": "VND",
                    "area_sqm": 400.0,
                    "address": "456 Nguyen Van Huong",
                    "city": "Hồ Chí Minh",
                    "status": "active",
                    "created_at": "2026-09-04T00:00:00Z",
                    "updated_at": "2026-09-04T00:00:00Z",
                },
                "similarity_score": 0.95,
                "rrf_score": 0.032,
                "vector_rank": 1,
                "fts_rank": 1,
            }
        ],
    }

    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached_search)

    with patch.object(cache, "get_redis", return_value=mock_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/properties/search",
                json={"query": "villa Thao Dien", "limit": 10},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["query"] == "villa Thao Dien"
            assert data["results"][0]["property"]["title"] == "Villa Thao Dien"
            assert mock_redis.get.call_count == 1

