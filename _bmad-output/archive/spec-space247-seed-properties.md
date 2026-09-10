---
title: 'Seed Realistic Property Data for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247 needs realistic sample property data in PostgreSQL with precomputed 768-dimensional vector embeddings so developers, search endpoints, and frontend clients can immediately test and evaluate hybrid/semantic search, filtering, and listings without manual data entry.

**Approach:**
1. Create `backend/scripts/seed_properties.py` defining 25-30 diverse, realistic real estate listings across Hanoi and Ho Chi Minh City covering apartments, townhouses, villas, and commercial spaces for both Sale and Rent.
2. Integrate with `EmbeddingService` to automatically generate 768-dimensional embeddings for each listing (using `build_property_text` and `generate_embedding(..., is_query=False)`).
3. Ensure idempotent execution via title/address deduplication and conflict handling so repeated seed runs do not create duplicate records.
4. Support CLI execution via `uv run python -m scripts.seed_properties` (or standalone script runner) with helpful logging and error handling.
5. Provide automated test cases in `backend/tests/test_seed_properties.py` verifying seed data structure, embedding dimensions, idempotency, and database persistence with 100% test pass.

</frozen-after-approval>

## Implementation Notes

- Created `backend/scripts/__init__.py` and `backend/scripts/seed_properties.py` containing 28 realistic real estate listings:
  - 13 properties in Ho Chi Minh City (District 1, District 3, District 7, District 10, Binh Thanh, Phu Nhuan, Thu Duc City).
  - 15 properties in Hanoi (Ba Dinh, Hoan Kiem, Tay Ho, Cau Giay, Hai Ba Trung, Long Bien, Bac Tu Liem, Nam Tu Liem).
  - Spans apartments, townhouses, villas, and commercial spaces across both Sale and Rent categories.
- Generated dense 768-dimensional vector embeddings using `EmbeddingService` (FastEmbed multilingual-mpnet / multilingual-e5) via `build_property_text` including bathroom and bedroom counts.
- Implemented idempotent insertion checking existing property titles before insert.
- Configured CLI runner via `uv run python -m scripts.seed_properties` and console script `seed-db` in `pyproject.toml` (`uv run seed-db`).
- Added robust Windows UTF-8 stdout reconfiguration and connection pool cleanup via `await engine.dispose()`.
- Authored test cases in `backend/tests/test_seed_properties.py` verifying property diversity, embedding dimensions, and mock idempotency.
- All 43 pytest tests in backend test suite pass (100%).

## Review Triage Log

- **Finding 1 (Include num_bathrooms in build_property_text)**: Fixed in `backend/scripts/seed_properties.py`.
- **Finding 2 (Engine cleanup in main())**: Added `try...finally: await engine.dispose()` in `main()`. Fixed in `backend/scripts/seed_properties.py`.
- **Finding 3 (Unused imports in seed and test files)**: Removed unused `import io`, `from sqlalchemy import select`, and `from src.models.property import Property`.
- **Finding 4 (Standardize ward name prefix)**: Updated `"Võ Thị Sáu"` to `"Phường Võ Thị Sáu"`.
- **Finding 5 (Batch embedding and batch lookup optimizations)**: Deferred for high-volume import jobs.

