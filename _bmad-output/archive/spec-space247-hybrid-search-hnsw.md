---
title: 'Implement Hybrid Search and HNSW Index for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247 property discovery needs to support high-performance vector retrieval at scale and handle real estate search queries containing exact keywords, project names, or street addresses alongside semantic preferences. Currently, property queries run purely on vector distance without index acceleration, and lack keyword matching fusion.

**Approach:**
1. Define an HNSW vector index (`m=16`, `ef_construction=64`, `vector_cosine_ops`) on the `Property.embedding` column using SQLAlchemy pgvector index options, ensuring it is created in `Base.metadata.create_all` / DB setup.
2. Integrate PostgreSQL Full-Text Search (FTS) combining `title`, `address`, `district`, `city`, and `description` using `to_tsvector('simple', ...)` or unaccent-compatible tsquery matching.
3. Update `POST /api/v1/properties/search` to implement Reciprocal Rank Fusion (RRF) with smoothing constant $k=60$ (and configurable via query parameter or constant), blending rank positions from vector cosine search and FTS keyword search while retaining all structured metadata filters (`listing_type`, `property_type`, `price`, `bedrooms`, etc.).
4. Add comprehensive automated tests in `backend/tests/test_hybrid_search.py` verifying HNSW index definition, RRF ranking calculation, FTS fallback, and combined filter execution, verified with pytest.

</frozen-after-approval>

## Implementation Notes

- Added `ix_properties_embedding_hnsw` to `Property.__table_args__` with `postgresql_using='hnsw'`, `m=16`, `ef_construction=64`, and `postgresql_ops={'embedding': 'vector_cosine_ops'}`.
- Added `ix_properties_fts` GIN full-text search index on `properties` table over concatenated `title`, `address`, `ward`, `district`, `city`, and `description` using `to_tsvector('simple', ...)`.
- Updated `PropertySearchQuery` with `enable_hybrid` (default: `True`) and `rrf_k` (default: `60`) parameters.
- Extended `SearchResultItem` and frontend shared types with `rrf_score`, `vector_rank`, and `fts_rank` fields and complete JSDoc documentation.
- Upgraded `search_properties` endpoint (`POST /api/v1/properties/search`) to execute concurrent vector candidate retrieval and PostgreSQL FTS candidate retrieval, applying structured metadata filters across both branches, fusing results via Reciprocal Rank Fusion formula:
  $$\text{RRF Score}(d) = \sum_{m \in \{\text{vector}, \text{fts}\}} \frac{1}{k + \text{rank}_m(d)}$$
- Applied deterministic tie-breaking on `(rrf_score, similarity_score, str(property_id))` and threshold filtering for evaluated candidates.
- Added 9 unit and integration tests in `backend/tests/test_hybrid_search.py` covering HNSW and GIN index DDL, tsquery tokenization, RRF rank fusion mathematics, pure vector fallback, FTS-only candidate fusion, and graceful database error fallback. All 36 backend tests pass.

## Review Triage Log

- finding: Threshold filtering dropped full-text search candidates when `sim_score` was 0.0.
  verdict: patched (applied threshold verification on evaluated vector candidates; items meet threshold properly).
- finding: Missing location fields (`ward`, `district`, `city`) in FTS vector expression and GIN index.
  verdict: patched (extended both `ix_properties_fts` index and `to_tsvector` query expression to concatenate title, address, ward, district, city, and description).
- finding: Non-deterministic tie-breaking across items with equal RRF scores due to unordered set iteration.
  verdict: patched (sorted `all_prop_ids` deterministically and added property UUID as final tie-breaker in sort key).
- finding: Sliced pagination length was reported as `total` instead of candidate count.
  verdict: patched (updated `total=len(fused_items)` in hybrid mode and `total=len(vector_map)` in vector mode).
- finding: Silent exception swallowing during FTS execution without diagnostic visibility.
  verdict: patched (added logger debug output capturing FTS execution errors).
- finding: Missing JSDoc comments on hybrid search fields in frontend types.
  verdict: patched (added complete JSDoc annotations to `frontend/shared/types.ts`).
- finding: `PropertySearchQuery` lacks `ward` and `num_bathrooms` search filters.
  verdict: deferred (recorded in `deferred-work.md`).
- finding: Tsquery parsing using custom regex instead of PostgreSQL native `websearch_to_tsquery`.
  verdict: deferred (recorded in `deferred-work.md`).

