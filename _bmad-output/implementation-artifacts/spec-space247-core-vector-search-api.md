---
title: 'Complete Space247 Core Vector Search and Property Embedding API'
type: 'feature'
created: '2026-09-04'
status: 'in-progress'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Space247 API requires a fully integrated 768-dimensional embedding service (supporting multilingual models optimized for Vietnamese like `multilingual-e5-base`), automated embedding generation upon property creation and update, and a natural language search endpoint `POST /api/v1/properties/search` with filtering on listing type, price range, number of bedrooms, and address.

**Approach:**
1. Integrate and enhance `EmbeddingService` in `backend/src/services/embedding.py` to support 768-dimensional embeddings with FastEmbed / sentence-transformers and Vietnamese multilingual model configuration (`multilingual-e5-base` / `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`).
2. Ensure `POST /api/v1/properties` and `PUT /api/v1/properties/{id}` automatically generate 768-dim embeddings from property metadata (`title`, `description`, `address`, `ward`, `district`, `city`) and store them in the `Property.embedding` pgvector column.
3. Enhance `POST /api/v1/properties/search` and `PropertySearchQuery` schema to accept natural language query strings, convert to 768-dim vector, query via pgvector cosine distance (`<=>`), and filter on `listing_type` (sale/rent), price range (`min_price`, `max_price`), bedrooms (`num_bedrooms`), and location/address (`address`, `city`, `district`).
4. Add comprehensive unit and integration tests in `backend/tests/` and verify all tests pass with pytest.

</frozen-after-approval>

## Implementation Notes

- Upgraded `EmbeddingService` in `backend/src/services/embedding.py` to support 768-dimensional multilingual embeddings, FastEmbed with model alias mapping (`multilingual-e5-base` -> `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`), optional `sentence-transformers` integration, and automatic E5 prefixing (`query: ` / `passage: `).
- Extended `build_property_text` to include property type, listing type (bán / cho thuê), and bedroom count in the semantic embedding representation.
- Integrated automatic 768-dim embedding generation on `POST /api/v1/properties` when embedding is omitted, and re-generation on `PUT /api/v1/properties/{id}` when text or bedroom/type metadata changes, with seamless fallback for standard and legacy embedding call signatures.
- Enhanced `PropertySearchQuery` and `POST /api/v1/properties/search` to accept `address`, `num_bedrooms`, and `min_bedrooms` filters alongside `listing_type`, `price`, and `location`, generating 768-dim query embeddings and matching via pgvector cosine distance `<=>`.
- Updated shared frontend contracts in `frontend/shared/types.ts` and `frontend/shared/api-client.ts` with `PropertySearchQuery`, `PropertySearchResponse`, and `searchProperties` API client method.
- Added comprehensive unit and integration tests in `backend/tests/test_semantic_search.py` covering E5 prefixes, bedroom auto-embedding, update auto-regeneration, and search filters. All 27 pytest tests pass.

