import hashlib
import json
import logging
from typing import Any
import redis.asyncio as aioredis
from redis.asyncio.client import Redis

from src.core.config import settings

logger = logging.getLogger("space247_cache")

# Global Redis client instance
redis_client: Redis | None = None


async def init_redis_pool() -> Redis | None:
    """
    Initialize asynchronous Redis connection pool.
    Returns Redis instance if connected, or None if disabled or connection failed.
    """
    global redis_client
    if not settings.REDIS_CACHE_ENABLED:
        logger.info("Redis cache is disabled via REDIS_CACHE_ENABLED=False.")
        redis_client = None
        return None

    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        await redis_client.ping()
        logger.info("Connected to Redis cache at %s", settings.REDIS_URL)
        return redis_client
    except Exception as exc:
        logger.warning(
            "Redis cache connection failed: %s. Application will run in cache-bypass mode.",
            exc,
        )
        redis_client = None
        return None


async def close_redis_pool() -> None:
    """Close Redis connection pool gracefully."""
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.close()
            logger.info("Redis cache connection pool closed.")
        except Exception as exc:
            logger.warning("Error closing Redis pool: %s", exc)
        finally:
            redis_client = None


def get_redis() -> Redis | None:
    """Get active global Redis client instance."""
    return redis_client


def generate_search_cache_key(search_dict: dict[str, Any]) -> str:
    """
    Generate a deterministic cache key from property search payload parameters.
    Serializes sorted dictionary to JSON and produces SHA-256 hash.
    """
    cleaned = {k: v for k, v in search_dict.items() if v is not None}
    serialized = json.dumps(cleaned, sort_keys=True, default=str)
    hashed = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"cache:search:{hashed}"


def generate_property_cache_key(property_id: Any) -> str:
    """Generate cache key for a single property by UUID."""
    return f"cache:property:{str(property_id)}"


async def get_cached_json(key: str) -> Any | None:
    """
    Retrieve and deserialize JSON value from Redis.
    Returns None on cache miss or connection error.
    """
    client = get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        if raw is not None:
            return json.loads(raw)
        return None
    except Exception as exc:
        logger.debug("Redis get error for key %s: %s", key, exc)
        return None


async def set_cached_json(key: str, data: Any, ttl: int | None = None) -> bool:
    """
    Serialize and store JSON value in Redis with expiration TTL.
    """
    client = get_redis()
    if client is None:
        return False
    try:
        expire_seconds = ttl if ttl is not None else settings.PROPERTY_CACHE_TTL_SECONDS
        raw = json.dumps(data, default=str)
        await client.set(key, raw, ex=expire_seconds)
        return True
    except Exception as exc:
        logger.debug("Redis set error for key %s: %s", key, exc)
        return False


async def delete_cached_key(key: str) -> bool:
    """Delete a specific cache key."""
    client = get_redis()
    if client is None:
        return False
    try:
        await client.delete(key)
        return True
    except Exception as exc:
        logger.debug("Redis delete error for key %s: %s", key, exc)
        return False


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Scan and delete all keys matching the given pattern (e.g. 'cache:search:*').
    Returns count of deleted keys.
    """
    client = get_redis()
    if client is None:
        return 0
    try:
        cursor = 0
        deleted_count = 0
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                deleted_count += await client.delete(*keys)
            if cursor == 0:
                break
        return deleted_count
    except Exception as exc:
        logger.debug("Redis pattern invalidation error for %s: %s", pattern, exc)
        return 0


async def invalidate_property_caches(property_id: Any | None = None) -> None:
    """
    Invalidate both the specific property cache and all search result caches.
    Called on POST, PUT, DELETE operations to ensure data consistency.
    """
    if property_id is not None:
        await delete_cached_key(generate_property_cache_key(property_id))
    # All search queries are invalidated because rankings or total results may have changed
    await invalidate_cache_pattern("cache:search:*")
