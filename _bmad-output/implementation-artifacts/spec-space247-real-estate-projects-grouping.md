---
title: 'Real Estate Projects and Grouping Architecture for Space247'
type: 'feature'
created: '2026-09-05'
status: 'completed'
baseline_commit: '3ac4ef40c841b5ac0b9776bf3276fcef6a568142'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Currently, property listings in Space247 exist as standalone individual records without master planning, developer context, or project-level clustering, preventing users from exploring real estate developments (such as Vinhomes Central Park, Ecopark) as cohesive complexes with aggregate unit inventories, average price per square meter, master plans, and project amenities.

**Approach:** 
1. Create Alembic migration `0006_add_projects_and_property_project_fk.py` creating the `projects` table with HNSW vector embedding (768-dim), PostGIS `geom` (Point, 4326), and linking `properties.project_id` foreign key.
2. Develop Backend ORM `Project` model, Pydantic v2 schemas (`src/schemas/project.py`), and RESTful API endpoints (`/api/v1/projects`) with Redis caching (`cache:project:*`, TTL 30m) and sub-properties statistics (total active for sale/rent, average price/sqm).
3. Enhance Shared SDK (`frontend/shared/types.ts` & `frontend/shared/api-client.ts`) with project DTOs and API methods.
4. Implement Next.js 16 Web pages: `/projects` (explorer grid & filters) and `/projects/[slug]` (project detail with tabs for Master Plan & Amenities, Available Units grid, and Leaflet Map), plus property detail breadcrumbs.
5. Provide Flutter mobile project models and screen components.
6. Author comprehensive automated tests for Project CRUD, stats aggregation, and relations, ensuring 100% test pass rate across backend and frontend builds.
7. Update documentation (`docs/database-design.md`, `docs/api-specs.md`, and `README.md`).

## Boundaries & Constraints

**Always:**
- Keep all tests at 100% PASS (101 existing backend tests + new project tests).
- Ensure TypeScript compilation (`npx tsc --noEmit`) and Next.js 16 build (`npm run build`) succeed with 0 errors.
- Ensure `flutter analyze` passes without fatal warnings or errors.
- Maintain professional, objective technical tone without AI cliché emojis.
- Support seamless backward compatibility: `project_id` on `properties` is nullable.

**Never:**
- Do not skip, disable, or delete existing test suites.
- Do not hardcode database IDs or external asset URLs without local fallbacks.

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0006_add_projects_table_and_property_project_fk.py` -- Alembic migration for `projects` table and `properties.project_id`.
- `backend/src/models/project.py` -- SQLAlchemy ORM model for `Project` with pgvector, PostGIS, relationships.
- `backend/src/models/property.py` -- Add `project_id` FK and `project` relationship.
- `backend/src/models/__init__.py` -- Export `Project`.
- `backend/src/schemas/project.py` -- Pydantic schemas: `ProjectBase`, `ProjectCreate`, `ProjectUpdate`, `ProjectResponse`, `ProjectDetailResponse`, `ProjectSummary`.
- `backend/src/schemas/property.py` -- Add `project` summary to `PropertyResponse` & `PropertyDetailResponse`.
- `backend/src/api/v1/endpoints/projects.py` -- REST API endpoints: list, get by id/slug, create, update, sub-properties.
- `backend/src/api/v1/router.py` -- Register `/projects` router.
- `backend/src/core/cache.py` -- Project cache key generator (`cache:project:*`).
- `backend/tests/api/v1/test_projects.py` -- Pytest suite for projects CRUD, stats, filtering.
- `frontend/shared/types.ts` -- DTO interfaces for `Project`, `ProjectDetail`, `ProjectSummary`, `ProjectFilter`.
- `frontend/shared/api-client.ts` -- Methods `getProjects`, `getProjectDetail`, `getProjectProperties`.
- `frontend/web/src/app/projects/page.tsx` -- Web project directory page.
- `frontend/web/src/app/projects/[slug]/page.tsx` -- Web project detail page.
- `frontend/web/src/components/project/ProjectCard.tsx` -- Reusable project card component.
- `frontend/web/src/app/properties/[id]/page.tsx` -- Breadcrumb link to parent project if present.
- `frontend/mobile/lib/models/project_models.dart` -- Dart models for Project & ProjectDetail.
- `docs/database-design.md` -- Update with `projects` table and ERD.
- `docs/api-specs.md` -- Update with `/api/v1/projects` endpoints.
- `README.md` -- Update endpoints and migration revision 0006.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0006_add_projects_table_and_property_project_fk.py` -- Create migration script.
- [x] `backend/src/models/project.py` & `backend/src/models/property.py` -- Define Project ORM and update Property relationship.
- [x] `backend/src/schemas/project.py` & `backend/src/schemas/property.py` -- Define schemas and response DTOs.
- [x] `backend/src/api/v1/endpoints/projects.py` & `router.py` -- Implement REST endpoints with Redis caching.
- [x] `backend/tests/api/v1/test_projects.py` -- Create pytest suite and verify 100% PASS.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add project types and client methods.
- [x] `frontend/web/src/components/project/` & `frontend/web/src/app/projects/` -- Build Web projects listing and detail pages.
- [x] `frontend/web/src/app/properties/[id]/page.tsx` -- Add parent project banner.
- [x] `frontend/mobile/lib/models/project_models.dart` -- Add Dart project models.
- [x] `docs/database-design.md`, `docs/api-specs.md`, `README.md` -- Update documentation with project specifications.

**Acceptance Criteria:**
- Given a project with sub-properties, when `GET /api/v1/projects/{slug}` is requested, then detail includes metadata, unit counts for sale/rent, and average price/sqm. [VERIFIED]
- Given the web frontend, when navigating to `/projects` and `/projects/[slug]`, then projects render with filters, tabs, units grid, and map. [VERIFIED]
- Given backend tests, when `uv run pytest` is executed, then all tests pass with 100% success. [VERIFIED: 108/108 PASS]
- Given web frontend, when `npx tsc --noEmit` and `npm run build` are executed, then 0 errors occur. [VERIFIED: 0 errors]

## Implementation Notes
- Created Alembic revision `0006_add_projects_table_and_property_project_fk.py` with full offline and online compatibility.
- Added HNSW vector index (`vector_cosine_ops`), PostGIS GiST index, and B-Tree indexes on `slug`, `city`, and `developer`.
- Implemented `Project` ORM model and established bidirectional SQLAlchemy relationship `properties` <-> `project`.
- Implemented `/api/v1/projects` REST endpoints with Redis caching (`cache:project:*`, TTL 1800s) and cache invalidation on mutation.
- Built Next.js 16 Web `/projects` and `/projects/[slug]` with interactive Leaflet map, master plan, and sub-property filtering.
- Implemented Flutter Dart models with clean JSON deserialization.

## Verification

**Commands Executed:**
- `uv run pytest` in `backend` -- Result: 108 passed, 0 failed (100% PASS).
- `npx tsc --noEmit` in `frontend/web` -- Result: 0 errors.
- `npm run build` in `frontend/web` -- Result: Succeeded in 3.2s, all static and dynamic pages generated.
- `flutter analyze` in `frontend/mobile` -- Result: No issues found.
