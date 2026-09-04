#!/usr/bin/env bash
# ==============================================================================
# Space247 - Database Seeding Runner Script (Linux / macOS)
# Provisions default accounts (admin, agent) and 28+ properties with 768-dim embeddings
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo -e "\033[36m========================================================\033[0m"
echo -e "\033[36m         Space247 - Database Seeding Runner             \033[0m"
echo -e "\033[36m========================================================\033[0m"
echo "Project Root : ${PROJECT_ROOT}"
echo "Backend Dir  : ${BACKEND_DIR}"

command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: https://docs.astral.sh/uv/" >&2; exit 1; }

# 1. Check if database container is running if docker is present
if command -v docker >/dev/null 2>&1; then
    echo "Verifying database container..."
    CONTAINER_STATUS=$(docker inspect --format="{{.State.Health.Status}}" real_estate_postgres 2>/dev/null || true)
    if [ "$CONTAINER_STATUS" != "healthy" ]; then
        echo "Starting postgres container..."
        (cd "${PROJECT_ROOT}" && docker compose up -d postgres)
        sleep 3
    fi
fi

cd "${BACKEND_DIR}"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating backend/.env from .env.example..."
    cp .env.example .env
fi

echo -e "\n\033[36mSynchronizing database schema (alembic upgrade head)...\033[0m"
uv run alembic upgrade head

echo -e "\n\033[36mRunning seed script...\033[0m"
uv run python -m scripts.seed_properties

echo -e "\n\033[32m[SUCCESS] Space247 database seeding completed successfully!\033[0m"
echo "Default Accounts:"
echo "  - Admin : admin@space247.vn | Password: Password123@"
echo "  - Agent : agent@space247.vn | Password: Password123@"
echo "  - User  : user@space247.vn  | Password: Password123@"
echo "  - Properties: 30 real-world listings across Hanoi and HCMC with 768-dim embeddings"

