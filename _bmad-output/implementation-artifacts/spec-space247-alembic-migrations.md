---
title: 'Setup and Complete Alembic Migration Framework for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247 currently initializes database tables via `Base.metadata.create_all` during startup, lacking an automated and reproducible database migration mechanism for schema evolution, pgvector extension registration, HNSW vector indexes, and Full-Text Search GIN indexes.

**Approach:**
1. Configure `backend/alembic.ini` with `script_location = migrations` (and optional env interpolation) and create `backend/migrations/` structure.
2. Implement asyncpg-compatible `backend/migrations/env.py` importing `target_metadata = Base.metadata` from `src.core.database`, dynamically pulling `settings.DATABASE_URL`, and supporting pgvector `Vector` autogeneration / comparator hooks.
3. Author the baseline initial migration (`0001_initial_pgvector_properties.py`) defining:
   - Registration of PostgreSQL extension `vector` (`CREATE EXTENSION IF NOT EXISTS vector`).
   - Table `properties` with all columns (`id`, `title`, `description`, `property_type`, `listing_type`, `price`, `currency`, `area_sqm`, `num_bedrooms`, `num_bathrooms`, `address`, `ward`, `district`, `city`, `latitude`, `longitude`, `status`, `embedding`, `created_at`, `updated_at`).
   - HNSW index on `embedding` (`m=16, ef_construction=64, vector_cosine_ops`).
   - GIN index on `to_tsvector('simple', ...)` over `title`, `address`, `ward`, `district`, `city`, and `description`.
4. Verify migration operations (`alembic upgrade head`, offline SQL generation `alembic upgrade head --sql`, and `alembic check` / schema comparison).
5. Add automated pytest tests in `backend/tests/test_alembic_migrations.py` validating migration script integrity, revision heads, and offline SQL generation.

</frozen-after-approval>

## Implementation Notes

- Added `alembic>=1.14.0` to `backend/pyproject.toml` and synchronized dependencies.
- Configured `backend/alembic.ini` with `script_location = migrations`, `prepend_sys_path = .`, and `path_separator = os`.
- Implemented `backend/migrations/env.py` with asyncpg engine (`async_engine_from_config`), dynamic `settings.DATABASE_URL` resolution, `target_metadata = Base.metadata`, and an `include_object` filter ignoring PostgreSQL catalog normalized casts on the functional GIN index `ix_properties_fts`.
- Configured `backend/migrations/script.py.mako` with `import pgvector.sqlalchemy`.
- Created initial migration `backend/migrations/versions/0001_initial_pgvector_properties.py` covering:
  - `CREATE EXTENSION IF NOT EXISTS vector`
  - `properties` table (UUID primary key, numeric, float, string, timestamps, Vector(768))
  - 9 standard B-tree indexes
  - HNSW index `ix_properties_embedding_hnsw` (`m=16, ef_construction=64, vector_cosine_ops`)
  - Full-Text Search GIN index `ix_properties_fts` over concatenated Vietnamese text columns
  - Bidirectional `downgrade()` implementation
- Executed `alembic upgrade head` and `alembic check`, confirming zero schema drift (`No new upgrade operations detected.`).
- Added 5 unit tests in `backend/tests/test_alembic_migrations.py` validating directory structure, revision heads, offline upgrade/downgrade SQL generation, and metadata alignment. All 41 backend pytest tests pass (100%).

## Review Triage

- **Finding 1 (Cleaned drop_index in downgrade)**: Removed `postgresql_using` argument in `op.drop_index` for standard PostgreSQL DDL compatibility. Fixed in `0001_initial_pgvector_properties.py`.
- **Finding 2 (Alembic version constraint in pyproject.toml)**: Corrected minimum version from `1.19.1` to `1.14.0`. Fixed in `backend/pyproject.toml`.
- **Finding 3 (Dynamic DB URL in env.py)**: Ensured `section["sqlalchemy.url"] = settings.DATABASE_URL` is explicitly set before calling `async_engine_from_config`. Fixed in `backend/migrations/env.py`.
- **Finding 4 (Check constraints and composite index on coordinates)**: Logged as deferred work for future domain validation enhancements.
