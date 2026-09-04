---
title: 'GitHub Actions CI Workflow for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** Space247 lacks continuous integration (CI) automation to validate code quality, database migrations, backend tests, frontend typing, and Next.js builds on incoming changes to the `main` branch.

**Approach:**
1. Create GitHub Actions workflow `.github/workflows/ci.yml` triggered on `push` and `pull_request` targeting the `main` branch.
2. Backend Job (`backend-ci`):
   - Service container running `pgvector/pgvector:pg16` with healthcheck on port 5432.
   - Install Python 3.11+, install and setup `uv`.
   - Install project dependencies with dev group (`uv sync`).
   - Run Alembic database migrations (`alembic upgrade head`).
   - Run the full pytest suite (`uv run pytest`).
3. Frontend Job (`frontend-ci`):
   - Setup Node.js 20+ with npm cache.
   - Install dependencies in `frontend/web/` (`npm ci` or `npm install`).
   - Run TypeScript type check (`npx tsc --noEmit`).
   - Run Next.js production build (`npm run build`).

</frozen-after-approval>

## Implementation Notes

1. **Workflow File Creation**:
   - Created `.github/workflows/ci.yml` with separate `backend-ci` and `frontend-ci` jobs.
   - Added `on.push` and `on.pull_request` triggers targeting branch `main`.
2. **Backend Job**:
   - Spawns service container `pgvector/pgvector:pg16` with healthcheck on port 5432.
   - Uses `actions/setup-python@v5` (Python 3.12) and `astral-sh/setup-uv@v5`.
   - Caches FastEmbed and HuggingFace transformer models under `~/.cache/fastembed` and `~/.cache/huggingface` using `backend/pyproject.toml` hash.
   - Enforces deterministic dependencies with `uv sync --frozen --group dev`.
   - Executes database migrations with `uv run alembic upgrade head`.
   - Executes full pytest test suite with `uv run pytest -v --durations=10`.
3. **Frontend Job**:
   - Uses `actions/setup-node@v4` (Node.js 20) with npm cache keyed to `frontend/web/package-lock.json`.
   - Enforces clean lockfile installation with `npm ci`.
   - Executes TypeScript compiler check `npx tsc --noEmit`.
   - Executes Next.js production build `npm run build` with `NEXT_PUBLIC_API_URL` injected.

## Review Triage Log

- **Reviewer**: Blind Hunter Reviewer subagent (Floor N = 2, reported 11 findings).
- **Triage Decisions**:
  - *Applied*: Added explicit top-level `permissions: contents: read` (least privilege).
  - *Applied*: Switched `npm install` to `npm ci` for deterministic frontend installations.
  - *Applied*: Corrected npm cache dependency path to `frontend/web/package-lock.json`.
  - *Applied*: Added `--frozen` flag to `uv sync` to ensure lockfile compliance without silent drifts.
  - *Applied*: Scoped model cache specifically to `~/.cache/fastembed` and `~/.cache/huggingface` rather than entire `~/.cache`.
  - *Applied*: Made concurrency cancellation conditional (`${{ github.ref != 'refs/heads/main' }}`) to prevent canceling runs on the default branch.
  - *Rejected / Deferred*: Backend/frontend linting additions (e.g. ruff, next lint) and path filtering; kept focused strictly on the user's explicit CI scope.
