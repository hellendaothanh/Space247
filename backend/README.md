# Space247 Backend

Asynchronous Python FastAPI service leveraging PostgreSQL and `pgvector` for Vietnamese real estate property search and semantic AI recommendations.

## Requirements

- Python >= 3.11
- `uv` package manager
- PostgreSQL 16 with `pgvector` extension

## Local Development

```bash
# Install dependencies
uv sync --all-extras

# Run local postgres with pgvector
docker compose up postgres -d

# Start backend service
uv run uvicorn src.main:app --reload --port 8000
```
