---
title: 'Redis Caching Integration for Space247 API'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** Natural language semantic / hybrid search and repeated single-property lookups query PostgreSQL and pgvector repeatedly, increasing database load and latency. Space247 needs an asynchronous Redis caching layer with automated cache invalidation upon property modifications.

**Approach:**
1. Infrastructure:
   - Add `redis` service (`redis:7-alpine`) to `docker-compose.yml` with healthcheck on port 6379.
   - Update startup scripts (`scripts/start-dev.ps1`, `scripts/start-dev.sh`) to start and verify the Redis container alongside PostgreSQL.
   - Add `redis` service in `.github/workflows/ci.yml` for backend CI.
2. Configuration & Redis Connection:
   - Add `REDIS_URL` (default `redis://localhost:6379/0`), `REDIS_CACHE_ENABLED` (default `True`), and cache TTL settings (`PROPERTY_CACHE_TTL_SECONDS: int = 900`, i.e. 15 minutes) to `backend/src/core/config.py` and `backend/.env.example`.
   - Create `backend/src/core/cache.py` managing the async Redis client connection pool, graceful error degradation (bypassing cache if Redis is unavailable), and helper methods:
     - `get_cache(key: str) -> dict | list | None`
     - `set_cache(key: str, value: Any, ttl_seconds: int = 900) -> None`
     - `delete_cache(key: str) -> None`
     - `delete_pattern(pattern: str) -> None` (e.g. `cache:search:*`, `cache:property:{id}`)
     - Hash generator for search payloads: `generate_search_cache_key(payload: dict) -> str`
   - Wire Redis client initialization and teardown into `backend/src/main.py` lifespan.
3. Endpoint Caching & Invalidation:
   - `POST /api/v1/properties/search`: Check Redis cache for key `cache:search:<md5_or_sha256_hash>`. If hit, return cached `PropertySearchResponse`. On miss, execute search, store in Redis with 10-15m TTL, and return.
   - `GET /api/v1/properties/{id}`: Check Redis cache for key `cache:property:<uuid>`. If hit, return cached `PropertyResponse`. On miss, fetch from DB, cache in Redis, and return.
   - Invalidation:
     - When `POST /api/v1/properties` is called: invalidate all search caches (`cache:search:*`).
     - When `PUT /api/v1/properties/{id}` is called: invalidate `cache:property:{id}` and all search caches (`cache:search:*`).
     - When `DELETE /api/v1/properties/{id}` is called: invalidate `cache:property:{id}` and all search caches (`cache:search:*`).
4. Testing & Verification:
   - Create unit/integration tests in `backend/tests/test_cache.py` testing cache hits, misses, TTL, search payload key generation, and invalidation on POST/PUT/DELETE.
   - Ensure 100% pass across all existing and new test cases (`uv run pytest`).
5. Documentation:
   - Update `README.md`, `docs/architecture/01-system-overview.md`, and `docs/architecture/02-data-model-and-vector-search.md` documenting Redis caching layer and architecture diagram.

</frozen-after-approval>

## Implementation Notes

1. **Redis Service & Configuration**:
   - Added `redis:7-alpine` container to `docker-compose.yml` with healthcheck (`redis-cli ping`), `--maxmemory 256mb` and `--maxmemory-policy allkeys-lru`.
   - Added `redis` service container to GitHub Actions CI workflow (`.github/workflows/ci.yml`).
   - Updated `scripts/start-dev.ps1` and `scripts/start-dev.sh` to start and verify readiness of both `postgres` and `redis`.
   - Configured `REDIS_URL`, `REDIS_CACHE_ENABLED`, and `PROPERTY_CACHE_TTL_SECONDS: int = 900` (15m) in `src/core/config.py` and `.env.example`.
2. **Cache Module & Lifespan**:
   - Created `src/core/cache.py` with async Redis client pool management, error handling, deterministic SHA-256 key hashing (`generate_search_cache_key`), single-property key formatting (`generate_property_cache_key`), and key/pattern invalidators (`invalidate_property_caches`).
   - Wired `init_redis_pool()` and `close_redis_pool()` into `src/main.py` lifespan within robust `try...finally` teardown to ensure DB connection disposal even if Redis termination fails.
3. **Endpoint Caching & Cache Invalidation**:
   - `POST /api/v1/properties/search`: Intercepts search requests with `cache:search:<sha256>`, returning cached responses on hit and caching results using `model_dump(mode="json")` on miss.
   - `POST /api/v1/search/semantic`: Intercepts semantic queries with deterministic query payload cache keys.
   - `GET /api/v1/properties/{id}`: Intercepts single property lookups with `cache:property:<uuid>`, returning cached DTO or caching DB result with `model_dump(mode="json")`.
   - Invalidation: Proactively triggers `invalidate_property_caches()` upon `POST`, `PUT`, and `DELETE /api/v1/properties/{id}` (with `await db.flush()` prior to invalidation in `delete_property`).
4. **Testing**:
   - Created `tests/test_cache.py` covering key determinism, mock Redis GET/SET/DELETE, graceful degradation on connection failure, pattern invalidation, and endpoint-level cache hit emulation for GET and POST.
   - Ran `uv lock` ensuring `redis` dependency is locked for CI with `uv sync --frozen`.
   - Verified 100% pass across all 57 backend tests (`uv run pytest`).
5. **Documentation**:
   - Updated `README.md` with Redis cache architecture diagram, tech stack listing, manual startup commands, and repository structure.
   - Updated `docs/architecture/01-system-overview.md` and `docs/architecture/02-data-model-and-vector-search.md` documenting caching topology, sequence diagram, and invalidation rules.

## Review Triage Log

- **Reviewer**: Blind Hunter Reviewer subagent (Floor N = 9, reported 14 findings).
- **Triage Decision**:
  - *Applied*: Updated `backend/uv.lock` with `uv lock` to ensure `uv sync --frozen` in CI passes without lockfile drift.
  - *Applied*: Added Redis caching to `/api/v1/search/semantic` endpoint.
  - *Applied*: Switched `model_dump()` to `model_dump(mode="json")` across cached responses for safe JSON serialization of non-primitive types.
  - *Applied*: Added `await db.flush()` before cache invalidation in `delete_property`.
  - *Applied*: Added `--maxmemory 256mb` and `--maxmemory-policy allkeys-lru` to Redis service in `docker-compose.yml`.
  - *Applied*: Wrapped `main.py` lifespan teardown in `try...finally` to ensure database engine disposal if Redis teardown errors.
  - *Applied*: Updated `README.md` test counts (57+ tests) and repository structure for `cache.py` and `test_cache.py`.
  - *Deferred (Non-blocking)*: Background task asynchronous worker for scan/delete pattern invalidation (sufficient for current traffic scale).
