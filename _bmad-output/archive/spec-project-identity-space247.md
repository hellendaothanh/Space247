---
title: 'Update Project Identity to Space247'
type: 'chore'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The project currently uses generic project names like `real-estate-backend` and `Real Estate Platform API`, and needs a standardized identifier `Space247` across backend configurations, environment variables, FastAPI title, and architecture documentation.

**Approach:** Update project name to `Space247` in `backend/pyproject.toml`, set `APP_NAME="Space247"` in `backend/.env.example` (and align `Settings` in `backend/src/core/config.py`), set FastAPI title to `Space247 Real Estate API` in `backend/src/main.py`, update titles and references in `docs/architecture/`, and synchronize `uv.lock` and tests.

</frozen-after-approval>

## Implementation Notes

- Updated `name = "Space247"` in `backend/pyproject.toml` and re-locked via `uv lock`.
- Added `APP_NAME=Space247` and set `PROJECT_NAME="Space247 Real Estate API"` in `backend/.env.example`.
- Added `APP_NAME: str = "Space247"` and updated `PROJECT_NAME: str = "Space247 Real Estate API"` in `backend/src/core/config.py`.
- Updated FastAPI title to `Space247 Real Estate API` and logger name to `space247_backend` in `backend/src/main.py`.
- Updated document titles and platform descriptions to `Space247` in `docs/architecture/01-system-overview.md`, `02-data-model-and-vector-search.md`, and `03-cross-platform-frontend.md`.
- Updated headers and references in `backend/README.md`, `backend/src/__init__.py`, `frontend/README.md`, `frontend/shared/types.ts`, and `frontend/shared/api-client.ts`.
- Created `frontend/shared/constants.ts` providing centralized constants (`VECTOR_DIM = 768`, enums).
- Synchronized dev dependency constraints in `backend/pyproject.toml` and updated `.env.example` with `EMBEDDING_MODEL`.
- Verified all 22 pytest unit and integration tests passing successfully with new assertions in `backend/tests/test_health.py`.

## Review Triage Log

- `backend/pyproject.toml` duplicate/inconsistent dev dependencies: `low` (fixed by harmonizing optional-dependencies with dependency-groups).
- `backend/.env.example` missing EMBEDDING_MODEL: `low` (fixed by adding EMBEDDING_MODEL setting).
- `frontend/shared/constants.ts` missing file: `low` (fixed by creating constants.ts with VECTOR_DIM and domain enums).
- Database migrations tooling (Alembic): `medium` (deferred: pre-existing architectural capability).
- HNSW vector index definition: `medium` (deferred: pre-existing schema enhancement).
- Hybrid Search (FTS + Vector RRF): `low` (deferred: future feature implementation).
- Frontend natural language search & filter methods: `low` (deferred: pre-existing frontend client expansion).
- Startup DDL & error handling: `low` (deferred: intentional dev setup pattern).

