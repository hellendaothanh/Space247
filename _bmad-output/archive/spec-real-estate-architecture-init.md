---
title: 'Real Estate Platform Architecture Bootstrap'
type: 'feature'
created: '2026-09-04'
status: 'completed'
baseline_commit: '1882a9b047706118d541ae79adb4adef47580ab4'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The real estate platform for property sales and rentals (Bất Động Sản Bán & Cho Thuê) requires a robust, scalable foundation supporting AI-driven semantic search, vector recommendations, high-throughput backend APIs, and multi-platform client access (Web & Mobile).

**Approach:** Scaffold a clean architecture backend using Python FastAPI and PostgreSQL with `pgvector` configured for 768-dimensional embeddings (optimized for Vietnamese semantic search), package management configured with `uv`/`pyproject.toml`, Docker Compose for local database infrastructure, decoupled frontend project structures for Web (Next.js) and Mobile (React Native / Flutter), and comprehensive architectural context documentation.

## Decisions

- **Embedding Dimension & Model:** 768 dimensions (multilingual open-weight models such as `multilingual-e5-base` or `bge-base`, highly effective for Vietnamese property descriptions and semantic matching).
- **Frontend Architecture:** Separate Web and Mobile clients communicating with FastAPI backend via standardized REST/OpenAPI endpoints: `frontend/web/` (Next.js), `frontend/mobile/` (React Native / Flutter cross-platform architecture), and `frontend/shared/` (shared DTOs and API contracts).

## Boundaries & Constraints

**Always:**
- Use asynchronous SQLAlchemy with `asyncpg` and official `pgvector-python` extensions.
- Manage Python dependencies cleanly via `pyproject.toml` targeting Python >=3.11 with `uv` lockfile support.
- Provide containerized PostgreSQL 16 image bundled with `pgvector` (`pgvector/pgvector:pg16`).
- Isolate architectural documentation under `docs/architecture/` with clear ADRs (Architecture Decision Records) and data models.

**Never:**
- Hardcode database credentials or embedding dimensions in source code; always use environment configurations (`VECTOR_DIM=768`).
- Mix synchronous and asynchronous database sessions in the FastAPI application layer.
- Couple frontend platform specifics directly into the backend API domain schemas.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Health Check | `GET /api/v1/health` | HTTP 200 `{"status": "healthy", "database": "connected", "pgvector": "enabled", "vector_dim": 768}` | Return HTTP 503 if database or vector extension check fails |
| Semantic Search (Valid Query) | `POST /api/v1/search/semantic` with 768-dim query vector and filters | HTTP 200 with ranked list of properties and cosine similarity scores | Return HTTP 422 on malformed filter schema |
| Semantic Search (Vector Dimension Mismatch) | Embedding vector length != 768 | HTTP 400 Bad Request with explicit dimension mismatch detail | Reject before database query execution |
| Property Creation with Embedding | `POST /api/v1/properties` with property attributes and optional 768-dim embedding | HTTP 201 Created with persisted record ID | Return HTTP 400 if required listing fields missing |

</frozen-after-approval>

## Code Map

- `docker-compose.yml` -- Orchestrates PostgreSQL 16 with pgvector extension and local environment settings.
- `.env.example` -- Root template for database credentials, port mapping, and vector configuration (`VECTOR_DIM=768`).
- `backend/pyproject.toml` -- Defines Python dependencies, project metadata, and `uv` package management configuration.
- `backend/Dockerfile` -- Container definition for FastAPI backend using multi-stage build with `uv`.
- `backend/.env.example` -- Backend environment variable template.
- `backend/src/main.py` -- FastAPI entrypoint with lifespan event verifying database and `pgvector` extension.
- `backend/src/core/config.py` -- Pydantic Settings for DB connection string, vector dimension (768), and CORS.
- `backend/src/core/database.py` -- Async SQLAlchemy engine and session factory.
- `backend/src/models/property.py` -- SQLAlchemy model for real estate properties with pgvector embedding column.
- `backend/src/schemas/property.py` -- Pydantic DTOs for property CRUD and semantic search queries.
- `backend/src/api/v1/router.py` -- API router registering health, property, and search endpoints.
- `backend/src/api/v1/endpoints/health.py` -- Health probe verifying DB connectivity and vector extension.
- `backend/src/api/v1/endpoints/properties.py` -- RESTful CRUD endpoints for sale & rental listings.
- `backend/src/api/v1/endpoints/search.py` -- Semantic vector search endpoint using cosine distance.
- `backend/tests/test_health.py` -- Unit and integration tests for health and basic schemas.
- `frontend/README.md` -- Architecture guide for decoupled Web & Mobile frontend structure and shared API client.
- `frontend/web/` -- Directory scaffold for Next.js Web frontend.
- `frontend/mobile/` -- Directory scaffold for React Native & Flutter Mobile clients.
- `frontend/shared/` -- Shared types, DTO contracts, and API client definitions.
- `docs/architecture/01-system-overview.md` -- System topology, architectural diagrams, component responsibilities.
- `docs/architecture/02-data-model-and-vector-search.md` -- Database schema, pgvector indexing (HNSW/IVFFlat), semantic search flow.
- `docs/architecture/03-cross-platform-frontend.md` -- Multi-platform frontend strategy and API communication patterns.

## Tasks & Acceptance

**Execution:**
- [x] `docker-compose.yml` -- Create Docker Compose configuration with `pgvector/pgvector:pg16` -- Provides local vector database environment.
- [x] `.env.example` -- Create root environment template -- Provides reproducible environment configuration.
- [x] `backend/pyproject.toml` -- Configure FastAPI, SQLAlchemy, asyncpg, pgvector, and dev dependencies -- Establishes `uv`-managed Python workspace.
- [x] `backend/Dockerfile` -- Create multi-stage build Dockerfile for FastAPI using `uv` -- Enables containerized backend execution.
- [x] `backend/.env.example` -- Create backend environment template -- Facilitates environment setup.
- [x] `backend/src/core/config.py` -- Implement Pydantic BaseSettings for database and vector configs -- Centralizes configuration management.
- [x] `backend/src/core/database.py` -- Implement async database engine and session generator -- Provides async database access.
- [x] `backend/src/models/property.py` -- Create Property model with Vector(768) column and listing metadata -- Defines database persistence schema.
- [x] `backend/src/schemas/property.py` -- Implement Pydantic request and response schemas -- Enforces strict API contract validation.
- [x] `backend/src/api/v1/endpoints/health.py` -- Implement health probe verifying PostgreSQL and pgvector -- Guarantees vector extension readiness check.
- [x] `backend/src/api/v1/endpoints/properties.py` -- Implement property creation, listing, and retrieval -- Delivers core property management API.
- [x] `backend/src/api/v1/endpoints/search.py` -- Implement vector similarity search endpoint with filters -- Powers AI semantic recommendations.
- [x] `backend/src/api/v1/router.py` -- Aggregate API v1 endpoints -- Provides unified v1 API routing.
- [x] `backend/src/main.py` -- Implement FastAPI application factory and lifespan -- Boots backend service.
- [x] `backend/tests/test_health.py` -- Create unit test verifying app factory and route registration -- Validates backend code health.
- [x] `frontend/README.md` -- Create multi-platform frontend blueprint and structure guide -- Guides frontend development.
- [x] `frontend/web/.gitkeep` & `frontend/mobile/.gitkeep` & `frontend/shared/.gitkeep` -- Initialize frontend modular folders -- Prepares client boundaries.
- [x] `docs/architecture/01-system-overview.md` -- Author architectural context and component topology -- Documents system architecture.
- [x] `docs/architecture/02-data-model-and-vector-search.md` -- Author data model, vector search indexing and query strategies -- Documents semantic search pipeline.
- [x] `docs/architecture/03-cross-platform-frontend.md` -- Author frontend architecture and state management conventions -- Documents multi-platform frontend strategy.

**Acceptance Criteria:**
- Given a running pgvector container, when calling `GET /api/v1/health`, then the response indicates database connected and pgvector extension active with dimension 768.
- Given property records with embeddings, when querying `POST /api/v1/search/semantic`, then results are ordered by cosine similarity and respect listing filters (sale vs rent).
- Given the root directory, when inspecting project layout, then backend, frontend, docker-compose, and docs/architecture adhere to modular architectural boundaries.

## Implementation Notes

- Scaffolding complete for backend (FastAPI, SQLAlchemy 2.0 asyncpg, pgvector 768-dim), frontend structure (`web`, `mobile`, and `shared` with TypeScript types and API client), and Docker Compose orchestration.
- Verified with `docker compose config`, `python -m compileall backend/src`, and `uv run pytest backend/tests` (9 tests passing).

## Spec Change Log

## Review Triage Log

## Design Notes

- **Hybrid Search Flow**: PostgreSQL Full-Text Search (FTS) with `tsvector` for keyword/address matching combined with `pgvector` (`vector(768)` data type + HNSW index) for conceptual/semantic property recommendations.
- **Async DB Strategy**: Utilizing `asyncpg` driver with `SQLAlchemy 2.0` syntax and `pgvector.sqlalchemy.Vector` type.

## Verification

**Commands:**
- `docker compose config` -- expected: Valid compose configuration syntax.
- `python -m compileall backend/src` -- expected: Clean syntax with 0 compilation errors.
- `pytest backend/tests` -- expected: All test cases pass.
