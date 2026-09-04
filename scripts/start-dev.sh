#!/usr/bin/env bash
# ==============================================================================
# Space247 - One-Click Development Environment Starter (Linux / macOS)
# Starts Docker Postgres+pgvector -> Runs Alembic Migrations -> Starts Backend & Web
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend/web"

echo -e "\033[36m========================================================\033[0m"
echo -e "\033[36m   Space247 Real Estate Platform - Development Starter   \033[0m"
echo -e "\033[36m========================================================\033[0m"
echo "Project Root : ${PROJECT_ROOT}"
echo "Backend Dir  : ${BACKEND_DIR}"
echo "Frontend Dir : ${FRONTEND_DIR}"

# 1. Check prerequisites
echo -e "\n\033[33m[1/5] Checking environment prerequisites...\033[0m"
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed." >&2; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: https://docs.astral.sh/uv/" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Node.js / npm is required for Next.js frontend." >&2; exit 1; }
echo -e "\033[32mPrerequisites check passed (Docker, uv, Node.js).\033[0m"

# 2. Start PostgreSQL container with pgvector
echo -e "\n\033[33m[2/5] Starting PostgreSQL with pgvector container...\033[0m"
cd "${PROJECT_ROOT}"
docker compose up -d postgres

# 3. Wait for PostgreSQL readiness
echo -e "\n\033[33m[3/5] Waiting for PostgreSQL to be ready...\033[0m"
for i in {1..30}; do
    STATUS=$(docker inspect --format="{{.State.Health.Status}}" real_estate_postgres 2>/dev/null || echo "unhealthy")
    if [ "$STATUS" = "healthy" ]; then
        break
    fi
    sleep 1
    echo -n "."
done

docker exec real_estate_postgres pg_isready -U postgres -d real_estate_db >/dev/null 2>&1 || {
    echo "PostgreSQL database failed to start." >&2
    exit 1
}
echo -e "\n\033[32mPostgreSQL database is ready!\033[0m"

# 4. Run Alembic Database Migrations
echo -e "\n\033[33m[4/5] Running Alembic migrations to head...\033[0m"
cd "${BACKEND_DIR}"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi
uv run alembic upgrade head
echo -e "\033[32mDatabase schema synchronized successfully!\033[0m"

# Ensure frontend env and dependencies
cd "${FRONTEND_DIR}"
if [ ! -f ".env.local" ] && [ -f ".env.example" ]; then
    cp .env.example .env.local
fi
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (npm install)..."
    npm install
fi

# 5. Start Backend and Frontend Services
echo -e "\n\033[33m[5/5] Launching backend (port 8080) and frontend (port 3000)...\033[0m"
echo -e "\033[36m  - Backend API : http://localhost:8080\033[0m"
echo -e "\033[36m  - Swagger Docs: http://localhost:8080/api/v1/docs\033[0m"
echo -e "\033[36m  - Frontend Web: http://localhost:3000\033[0m"
echo -e "\033[90mPress Ctrl+C to stop all services.\033[0m\n"

cleanup() {
    echo -e "\n\033[33mStopping Space247 services...\033[0m"
    trap - SIGINT SIGTERM
    kill -- -$$ 2>/dev/null || kill 0 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

(cd "${BACKEND_DIR}" && uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload) &
(cd "${FRONTEND_DIR}" && npm run dev) &

wait
