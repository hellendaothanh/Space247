# Space247 Backend

Python FastAPI service cung cấp AI-powered Real Estate API với PostgreSQL + pgvector + PostGIS.

## Yêu cầu

- Python ≥ 3.11
- `uv` package manager
- Docker (để chạy PostgreSQL + pgvector/PostGIS + Redis)

## Cài đặt & Khởi chạy

\`\`\`bash
# 1. Khởi động database container
docker compose up -d postgres redis

# 2. Cài đặt dependencies Python
uv sync --all-extras

# 3. Đồng bộ schema (migration 0005 head)
uv run alembic upgrade head

# 4. Nạp dữ liệu mẫu
uv run python -m scripts.seed_properties

# 5. Chạy backend
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
\`\`\`

## Biến Môi Trường (.env)

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DATABASE_URL` | PostgreSQL asyncpg connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT signing key (HS256) | *(bắt buộc đặt)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL của JWT token (phút) | `1440` |
| `VECTOR_DIM` | Chiều vector embedding FastEmbed | `768` |
| `GEMINI_API_KEY` | Google Gemini API key (Agent AI Co-Pilot) | *(tuỳ chọn)* |

## Cấu Trúc Mã Nguồn

\`\`\`
backend/
├── migrations/
│   └── versions/
│       ├── 0001_init_properties_pgvector_postgis.py
│       ├── 0002_add_users_and_fk.py
│       ├── 0003_add_favorite_properties.py
│       ├── 0004_add_alerts_and_notifications.py
│       └── 0005_add_property_images_and_user_avatar.py
├── scripts/
│   └── seed_properties.py         # Idempotent seeder — 28 BĐS thực tế
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # POST /register, POST /login, GET+PUT /me
│   │       │   ├── properties.py   # CRUD + search + compare + favorites
│   │       │   ├── search.py       # POST /semantic
│   │       │   ├── chat.py         # POST /assistant (AI Chatbot)
│   │       │   ├── agent.py        # POST /listing/generate, POST /valuation/estimate
│   │       │   ├── spatial.py      # POST /isochrone-search, GET /amenities/heatmap
│   │       │   ├── financial.py    # POST /mortgage-calc
│   │       │   ├── alerts.py       # CRUD /alerts
│   │       │   ├── notifications.py # GET /notifications, POST /read-all
│   │       │   └── health.py       # GET /health
│   │       └── router.py
│   ├── core/
│   │   ├── config.py               # Pydantic Settings
│   │   ├── database.py             # SQLAlchemy AsyncEngine + session factory
│   │   ├── cache.py                # Redis async helpers (get/set/delete JSON)
│   │   └── security.py             # JWT create/verify, bcrypt hash/verify
│   ├── models/
│   │   ├── property.py             # Property — geom, images[], embedding VECTOR(768)
│   │   └── user.py                 # User — avatar_url, phone, role
│   ├── schemas/
│   │   ├── property.py             # PropertyCreate/Update/Response/Detail + PropertyAgentResponse
│   │   ├── user.py                 # UserRegister/Login/Update/Response + Token
│   │   ├── chat.py                 # ChatRequest/Response
│   │   ├── agent.py                # GenerateListingRequest/Response, ValuationRequest/Response
│   │   ├── spatial.py              # IsochroneSearchRequest/Response, AmenityHeatmapRequest
│   │   ├── financial.py            # MortgageCalcRequest/Response
│   │   └── alerts.py               # CreateAlertRequest/Response, NotificationResponse
│   └── services/
│       ├── embedding.py            # FastEmbed — paraphrase-multilingual-mpnet-base-v2 768-dim
│       ├── chat_assistant.py       # Gemini chat với intent extraction + Hybrid Search
│       ├── ai_comparison.py        # So sánh AI 2-3 BĐS theo 4 tiêu chí
│       └── alert_service.py        # Background matching engine
└── tests/
    ├── test_alembic_migrations.py  # Schema + offline SQL gen assertions
    ├── test_auth.py
    ├── test_chat_assistant.py
    ├── test_semantic_search.py
    └── api/v1/
        ├── test_properties.py      # CRUD + images + agent + compare
        ├── test_agent.py
        ├── test_spatial.py
        ├── test_financial.py
        └── test_alerts.py
\`\`\`

## Kiểm Thử

\`\`\`bash
uv run pytest                        # Chạy toàn bộ — 101 tests PASS
uv run pytest -v --tb=short          # Chi tiết từng test
uv run pytest tests/test_alembic_migrations.py  # Migration tests riêng
\`\`\`

## Alembic — Lệnh Thông Dụng

\`\`\`bash
uv run alembic current               # Xem revision đang áp dụng
uv run alembic upgrade head          # Nâng lên revision mới nhất
uv run alembic downgrade -1          # Rollback 1 bước
uv run alembic revision --autogenerate -m "mô tả migration"
\`\`\`

## Tài Khoản Mẫu

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin | `admin@space247.vn` | `Password123@` |
| Agent | `agent@space247.vn` | `Password123@` |
