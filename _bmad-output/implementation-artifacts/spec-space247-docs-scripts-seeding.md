---
title: 'Documentation, One-Click Startup Scripts, and Independent Database Seeding for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

Problem: Space247 lacks root documentation (README.md), one-click developer startup scripts (start-dev.ps1 / start-dev.sh), and independent database seeding runner scripts (seed-data.ps1 / seed-data.sh) that provisions seed users (admin@space247.vn, agent@space247.vn) alongside the 28+ real-estate listings with 768-dim embeddings.

Approach:
1. Root Documentation (README.md):
   - Comprehensive overview of Space247 architecture (FastAPI + pgvector + Next.js App Router).
   - Prerequisites (Docker, Python/uv, Node.js 20+).
   - Step-by-step instructions for installation, configuration (.env), migrations, seeding, and execution.
   - Comprehensive table of primary API endpoints (/api/v1/auth, /api/v1/properties, /api/v1/properties/search, Swagger docs).
2. One-Click Startup Scripts (scripts/start-dev.ps1, scripts/start-dev.sh):
   - Launch PostgreSQL + pgvector Docker container (docker compose up -d postgres).
   - Wait for database health readiness (pg_isready).
   - Run Alembic migrations (uv run alembic upgrade head inside backend).
   - Start backend server on port 8080.
   - Start frontend Next.js dev server on port 3000.
3. Independent Database Seeding Mechanism (backend/scripts/seed_properties.py, scripts/seed-data.ps1, scripts/seed-data.sh):
   - Update seeding script to automatically check and provision default seed users if missing:
     - admin@space247.vn (role: admin, password: Password123@)
     - agent@space247.vn (role: agent, password: Password123@)
     - user@space247.vn (role: user, password: Password123@)
   - Link sample properties to the agent seed user ID.
   - Ensure full idempotency (safe to re-run without creating duplicate users or properties).
   - Provide standalone CLI scripts scripts/seed-data.ps1 and scripts/seed-data.sh.
4. Testing & Verification:
   - Ensure all backend tests (uv run pytest) and frontend builds (npm run build) pass 100%.
   - Verify script syntax and execution permissions.

</frozen-after-approval>

## Implementation Notes

- **Root Documentation (`README.md`)**:
  - Detailed overview of Space247 architecture with Mermaid diagram, technology stack (FastAPI 0.115, PostgreSQL 16 + pgvector, Next.js 16.3.4 App Router, Tailwind CSS).
  - Prerequisites and one-click startup instructions for both PowerShell and Bash.
  - Manual setup guide with commands for dependency management (`uv`, `npm`), migrations, and seeding.
  - Comprehensive API endpoint table covering Auth, Properties, Hybrid/Vector Search, and OpenAPI/Swagger specifications.
  - Testing commands for backend and frontend.

- **One-Click Startup Scripts (`scripts/start-dev.ps1`, `scripts/start-dev.sh`)**:
  - Automatically verifies prerequisites (`docker`, `uv`, `node`/`npm`).
  - Automatically copies `.env.example` to `.env` / `.env.local` if missing.
  - Checks if Docker PostgreSQL is running; starts and waits for container health (`pg_isready`).
  - Runs Alembic migrations (`uv run alembic upgrade head`) with exit code checks.
  - Installs frontend packages if `node_modules` is not present.
  - Starts backend on port 8080 and frontend on port 3000.
  - Traps `SIGINT`/`SIGTERM` or `Ctrl+C` in PowerShell to cleanly shut down child processes (`uvicorn` and Next.js dev server).

- **Standalone Seeding Mechanism (`backend/scripts/seed_properties.py`, `scripts/seed-data.ps1`, `scripts/seed-data.sh`)**:
  - Added user seeding (`seed_users`) for `admin@space247.vn`, `agent@space247.vn`, and `user@space247.vn`.
  - Added `land` (đất nền) property category to `SAMPLE_PROPERTIES` (now 30 items total).
  - Linked seeded properties to the agent's user ID.
  - Added transaction rollback handling on error before engine disposal.
  - Updated unit tests in `backend/tests/test_seed_properties.py` to cover user seeding, idempotency, and property linking.
  - Added migration and Docker container health checks in `seed-data.ps1` and `seed-data.sh`.

- **Configuration Alignment**:
  - Standardized backend port to 8080 in `docker-compose.yml`.

## Review Triage Log

- **Subagent Reviewer Findings & Resolutions**:
  1. *Mock query matching in unit tests*: Fixed query matching in `test_seed_properties.py` using bound parameters instead of relying on `str(stmt)`.
  2. *Add land property category*: Added 2 `land` properties (Hanoi & Danang) to fulfill property diversity requirements.
  3. *Error handling during seeding*: Added `await session.rollback()` on exception in `backend/scripts/seed_properties.py`.
  4. *Docker-compose port mismatch*: Aligned `docker-compose.yml` backend port from 8000 to 8080.
  5. *PowerShell child process cleanup*: Added process tree termination in `start-dev.ps1` to prevent orphaned `uvicorn` and Node processes.
  6. *Shell script database check*: Added container check and alembic upgrade to `seed-data.sh` matching `seed-data.ps1`.

