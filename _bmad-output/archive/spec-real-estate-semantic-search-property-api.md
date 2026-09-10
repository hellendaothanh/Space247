---
title: 'Semantic Search and Property API Vector Integration'
type: 'feature'
created: '2026-09-04'
status: 'done'
baseline_commit: '1882a9b047706118d541ae79adb4adef47580ab4'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The real estate platform currently lacks automated vector embedding generation for properties and lacks a natural language search endpoint that converts user queries into 768-dimensional embeddings to perform pgvector cosine similarity matching combined with structured real estate filters.

**Approach:** Implement a dedicated 768-dimensional `EmbeddingService` utilizing `FastEmbed`, hook it into `POST /api/v1/properties` and `PUT /api/v1/properties/{id}` to automatically generate embeddings from title, description, and address, build `POST /api/v1/properties/search` supporting natural language text queries with pgvector cosine distance (`<=>`) plus multi-criteria filters (listing type, price range, location), and verify with a comprehensive test suite.

## Boundaries & Constraints

**Always:**
- Generate 768-dimensional vector embeddings adhering to `settings.VECTOR_DIM = 768`.
- Combine property `title`, `description`, and `address` (along with ward/district/city metadata if available) as the semantic representation text.
- Execute pgvector cosine distance ordering (`<=>` operator via SQLAlchemy `Property.embedding.cosine_distance(query_vector)`) on active listings with non-null embeddings.
- Allow structured filters on `listing_type` (`sale` / `rent`), `property_type`, `min_price`, `max_price`, `city`, and `district` alongside the vector distance order.
- Provide dependency override support in tests so that mock or deterministic embedding generation runs quickly and reliably without external network dependencies.

**Never:**
- Block property creation/update if embedding generation is requested: raise a clear 500/503 error only if the embedding service fails unrecoverably.
- Allow mismatched vector dimensions (not equal to 768) to be stored in the database or passed to search queries.
- Remove or break existing endpoints like `/api/v1/health` or raw vector search `/api/v1/search/semantic`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Auto Embedding on Create | `POST /api/v1/properties` with valid fields and `embedding: null` | Property created with auto-computed 768-dim float vector | Returns 400 if invalid data, 500 if embedding service fails |
| Auto Embedding on Update | `PUT /api/v1/properties/{id}` with new `title` or `description` and `embedding: null` | Property updated and embedding re-computed from updated combined text | Returns 404 if property not found |
| Explicit Embedding Override | `POST` or `PUT` with explicit 768-dim vector in payload | Explicit embedding vector is preserved and stored | Returns 400 Bad Request if embedding length != 768 |
| Natural Language Search | `POST /api/v1/properties/search` with `query="căn hộ 2 phòng ngủ cho thuê Bình Thạnh"` and `listing_type="rent"` | Embedding generated from query text, filtered by `listing_type='rent'`, ranked by cosine similarity descending | Returns 200 with `results` list and `similarity_score` |
| Empty or Whitespace Query | `POST /api/v1/properties/search` with `query=""` or whitespace only | Pydantic validation error | Returns 422 Unprocessable Entity |
| Search No Match / Threshold | `query` with `threshold=0.99` when closest match similarity is 0.85 | Empty results list, `total: 0` | Returns 200 OK with empty `results` |

</frozen-after-approval>

## Code Map

- `backend/pyproject.toml` -- Dependencies specification; includes `fastembed>=0.8.0`.
- `backend/src/core/config.py` -- Settings configuration; manages `VECTOR_DIM` (768) and `EMBEDDING_MODEL`.
- `backend/src/services/embedding.py` -- New embedding service wrapper providing 768-dim vector generation and text concatenation logic.
- `backend/src/schemas/property.py` -- Pydantic schemas for `PropertySearchQuery` and search responses.
- `backend/src/api/v1/endpoints/properties.py` -- Handlers for `POST /properties`, `PUT /properties/{id}`, and new `POST /properties/search`.
- `backend/src/api/v1/endpoints/search.py` -- Vector search endpoint `/api/v1/search/semantic` kept for direct vector queries.
- `backend/tests/test_semantic_search.py` -- Comprehensive unit and integration tests covering embedding service, auto-generation on create/update, and natural language search with filters.

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/core/config.py` -- Add `EMBEDDING_MODEL` setting -- Configurable model identifier with sensible default.
- [x] `backend/src/services/embedding.py` -- Create `EmbeddingService` with FastEmbed -- Generate 768-dim embeddings and format property text for indexing.
- [x] `backend/src/schemas/property.py` -- Add `PropertySearchQuery` schema -- Support natural language query string and multi-criteria filters.
- [x] `backend/src/api/v1/endpoints/properties.py` -- Integrate auto-embedding and `POST /search` -- Auto-compute vector on create/update and provide natural language search endpoint.
- [x] `backend/tests/test_semantic_search.py` -- Add comprehensive tests -- Verify embedding generation, create/update auto-embedding, and search filtering.

**Acceptance Criteria:**
- Given a new property without an embedding vector, when `POST /api/v1/properties` is called, then a 768-dim embedding is automatically generated and saved.
- Given an existing property, when `PUT /api/v1/properties/{id}` updates the title, description, or address without providing an embedding, then a fresh embedding is automatically re-generated.
- Given a natural language query with filters, when `POST /api/v1/properties/search` is called, then the query is converted to a 768-dim vector and matching active properties are returned ranked by cosine similarity with filters applied.

## Implementation Notes

- Added `fastembed>=0.8.0` to `backend/pyproject.toml` dependencies.
- Added `EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"` to `Settings` in `src/core/config.py`.
- Created `EmbeddingService` in `src/services/embedding.py` with support for lazy model loading, 768-dim vector generation, batch embeddings, and `build_property_text` semantic formatting for Vietnamese property listings.
- Extended `src/schemas/property.py` with `PropertySearchQuery` (natural language query and multi-criteria filters) and `PropertySearchResponse`.
- Updated `create_property` and `update_property` in `src/api/v1/endpoints/properties.py` with auto-embedding generation whenever embedding is omitted.
- Added `POST /api/v1/properties/search` in `src/api/v1/endpoints/properties.py` utilizing pgvector cosine distance `<=>` operator alongside filters for listing type, property type, price bounds, city, district, and area.
- Added 13 comprehensive unit and integration tests in `backend/tests/test_semantic_search.py` covering all matrix rows. All 22 tests in the suite pass.

## Spec Change Log

## Review Triage Log

- `false` -- Potential performance bottleneck during startup -- Lazy initialization in `EmbeddingService` ensures zero impact on startup time.
- `false` -- Risk of missing embeddings on creation -- `create_property` automatically generates embeddings when `embedding` is null.
- `false` -- Risk of stale embeddings on update -- `update_property` detects text changes and re-generates embeddings automatically.
- `false` -- Route collision between `/search` and `/{property_id}` -- `POST /search` is defined prior to path parameter routes, preventing route shadowing.

## Verification

**Commands:**
- `uv run pytest` -- expected: All unit and integration tests pass successfully with 100% success rate.
