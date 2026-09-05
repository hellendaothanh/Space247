# Space247 Backend Service

Dịch vụ Backend API nền tảng Space247 được xây dựng bằng Python FastAPI, cung cấp hệ thống xử lý bất động sản thông minh với PostgreSQL 16 (hỗ trợ phần mở rộng pgvector và PostGIS), Redis Cache, mô hình sinh embedding vector 768 chiều và Trợ lý AI tích hợp.

---

## 1. Yêu Cầu Kỹ Thuật

- Python >= 3.11
- Trình quản lý gói `uv` (Astral)
- Docker và Docker Compose (chạy PostgreSQL 16 + pgvector/PostGIS và Redis 7)

---

## 2. Cài Đặt và Khởi Chạy Từng Bước

### Bước 1: Khởi động cơ sở dữ liệu và cache qua Docker
Từ thư mục gốc của dự án hoặc thư mục `backend`:
```bash
docker compose -f ../docker-compose.yml up -d postgres redis
```

### Bước 2: Thiết lập môi trường ảo và cài đặt thư viện
```bash
cd backend
cp .env.example .env
uv sync --all-extras
```

### Bước 3: Áp dụng các bản di chuyển lược đồ (Alembic Migrations)
Cơ sở dữ liệu được quản lý qua Alembic với lịch sử di chuyển tới revision head `0005`:
```bash
uv run alembic upgrade head
```

Danh mục các bản di chuyển trong `migrations/versions/`:
- `0001_initial_pgvector_properties.py`: Khởi tạo bảng `properties`, kích hoạt pgvector và PostGIS, tạo chỉ mục HNSW và GiST.
- `0002_add_users_table_and_property_user_fk.py`: Khởi tạo bảng `users` và khóa ngoại `user_id` trong `properties`.
- `0003_add_favorite_properties.py`: Khởi tạo bảng liên kết nhiều-nhiều `favorite_properties`.
- `0004_add_alerts_and_notifications.py`: Khởi tạo bảng `saved_search_alerts` và `user_notifications`.
- `0005_add_property_images_and_user_avatar.py`: Bổ sung cột `images TEXT[]` vào bảng `properties` và `avatar_url` vào bảng `users`.

### Bước 4: Nạp dữ liệu khởi tạo (Data Seeding)
Chạy script seeding dữ liệu thực tế mẫu:
```bash
uv run python -m scripts.seed_properties
```
*Script seeding được thiết kế an toàn, có khả năng chạy lại nhiều lần mà không gây lỗi hoặc trùng lặp dữ liệu.*

### Bước 5: Khởi động máy chủ ứng dụng
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```
Sau khi khởi chạy thành công:
- API Base: `http://localhost:8080/api/v1`
- Tài liệu tương tác OpenAPI (Swagger UI): `http://localhost:8080/api/v1/docs`
- Tài liệu ReDoc: `http://localhost:8080/api/v1/redoc`

---

## 3. Cấu Hình Biến Môi Trường (.env)

Tệp cấu hình `.env` được nạp tự động qua Pydantic BaseSettings trong `src/core/config.py`:

| Tên biến | Kiểu dữ liệu | Giá trị mặc định | Mô tả chi tiết |
|---|---|---|---|
| `DATABASE_URL` | String | `postgresql+asyncpg://postgres:postgres@localhost:5432/real_estate_db` | Chuỗi kết nối PostgreSQL thông qua driver asyncpg |
| `REDIS_URL` | String | `redis://localhost:6379/0` | Địa chỉ kết nối Redis phục vụ lưu trữ bộ nhớ đệm |
| `REDIS_CACHE_ENABLED` | Boolean | `True` | Bật hoặc tắt chức năng lưu bộ nhớ đệm Redis |
| `PROPERTY_CACHE_TTL_SECONDS` | Integer | `900` | Thời gian sống (TTL) của cache chi tiết và tìm kiếm BĐS (15 phút) |
| `VECTOR_DIM` | Integer | `768` | Số chiều vector embedding (chuẩn 768 chiều cho paraphrase-multilingual-mpnet-base-v2) |
| `EMBEDDING_MODEL` | String | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Tên mô hình ngôn ngữ sinh vector FastEmbed |
| `SECRET_KEY` | String | `space247-super-secret-jwt-key-for-development-change-in-production-2026` | Khóa bí mật dùng ký và xác minh token JWT HS256 |
| `JWT_ALGORITHM` | String | `HS256` | Thuật toán mã hóa JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `10080` | Thời hạn hiệu lực của token đăng nhập (7 ngày) |
| `CORS_ORIGINS` | List/JSON | `["http://localhost:3000", "http://localhost:8081"]` | Danh sách domain được phép gửi request qua CORS |
| `GEMINI_API_KEY` | String | Trống (tùy chọn) | Khóa API Google Gemini hỗ trợ Trợ lý Chat và Tiện ích Môi giới AI |

---

## 4. Cấu Trúc Mã Nguồn

```
backend/
├── migrations/
│   ├── env.py                     # Cấu hình môi trường migration của Alembic
│   └── versions/                  # Các bản di chuyển từ 0001 đến 0005
│       ├── 0001_initial_pgvector_properties.py
│       ├── 0002_add_users_table_and_property_user_fk.py
│       ├── 0003_add_favorite_properties.py
│       ├── 0004_add_alerts_and_notifications.py
│       └── 0005_add_property_images_and_user_avatar.py
├── scripts/
│   └── seed_properties.py         # Script nạp 28 bất động sản thực tế tại Hà Nội và TP.HCM
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── agent.py       # POST /listing/generate, POST /valuation/estimate
│   │       │   ├── alerts.py      # CRUD /alerts
│   │       │   ├── auth.py        # POST /register, POST /login, GET+PUT /me
│   │       │   ├── chat.py        # POST /assistant
│   │       │   ├── financial.py   # POST /mortgage-calc
│   │       │   ├── health.py      # GET /health
│   │       │   ├── notifications.py # GET /notifications, POST /read-all
│   │       │   ├── properties.py  # CRUD properties, /search (hybrid), /compare, /favorites
│   │       │   ├── search.py      # POST /semantic
│   │       │   └── spatial.py     # POST /isochrone-search, GET /amenities/heatmap
│   │       └── router.py          # Tập hợp toàn bộ router v1
│   ├── core/
│   │   ├── config.py              # Đọc và xác thực cấu hình ứng dụng
│   │   ├── database.py            # Khởi tạo SQLAlchemy AsyncEngine và AsyncSessionMaker
│   │   ├── cache.py               # Kết nối và thao tác Redis async
│   │   └── security.py            # Mã hóa mật khẩu bcrypt và xử lý token JWT
│   ├── models/
│   │   ├── property.py            # Mô hình thực thể Property (PostGIS geom, pgvector, images[])
│   │   └── user.py                # Mô hình thực thể User, FavoriteProperty, Alert, Notification
│   ├── schemas/                   # Khai báo schema Pydantic v2 cho request và response
│   │   ├── agent.py
│   │   ├── alerts.py
│   │   ├── chat.py
│   │   ├── financial.py
│   │   ├── property.py
│   │   ├── spatial.py
│   │   └── user.py
│   ├── services/                  # Các lớp dịch vụ logic nghiệp vụ chuyên sâu
│   │   ├── ai_comparison.py       # So sánh AI chi tiết giữa các bất động sản
│   │   ├── alert_service.py       # Dịch vụ so khớp và tạo thông báo nền
│   │   ├── chat_assistant.py      # Trợ lý AI hội thoại và trích xuất tiêu chí tìm kiếm
│   │   └── embedding.py           # Dịch vụ sinh vector biểu diễn qua FastEmbed
│   └── main.py                    # Điểm khởi tạo ứng dụng FastAPI và vòng đời lifespan
├── tests/
│   ├── api/v1/
│   │   ├── test_agent.py          # 9 tests
│   │   ├── test_alerts.py         # 4 tests
│   │   ├── test_financial.py      # 4 tests
│   │   ├── test_properties.py     # 8 tests
│   │   └── test_spatial.py        # 5 tests
│   ├── test_alembic_migrations.py # 5 tests
│   ├── test_auth.py               # 2 tests
│   ├── test_cache.py              # 7 tests
│   ├── test_chat_assistant.py     # 10 tests
│   ├── test_favorites.py          # 4 tests
│   ├── test_health.py             # 9 tests
│   ├── test_hybrid_search.py      # 9 tests
│   ├── test_properties_my.py      # 3 tests
│   ├── test_seed_properties.py    # 4 tests
│   └── test_semantic_search.py    # 18 tests
└── pyproject.toml
```

---

## 5. Quy Trình Kiểm Thử Tự Động (Testing)

Bộ kiểm thử được viết bằng `pytest` kết hợp `pytest-asyncio`:

```bash
# Thực thi toàn bộ bộ kiểm thử
uv run pytest

# Chạy có hiển thị chi tiết từng ca kiểm thử
uv run pytest -v

# Chỉ chạy các kiểm thử di chuyển cơ sở dữ liệu
uv run pytest tests/test_alembic_migrations.py
```

Kết quả kiểm chuẩn thực tế:
- **Tổng số ca kiểm thử**: 101/101 ca kiểm thử đạt trạng thái PASS (100%).
- **Thời gian thực thi trung bình**: ~85 giây khi tải mô hình FastEmbed và băm mật khẩu bcrypt.

---

## 6. Thao Tác Với Cơ Sở Dữ Liệu (Alembic Commands)

```bash
# Kiểm tra phiên bản revision hiện tại trong cơ sở dữ liệu
uv run alembic current

# Nâng cấp lên phiên bản mới nhất
uv run alembic upgrade head

# Quay lui 1 bước di chuyển
uv run alembic downgrade -1

# Tự động tạo bản di chuyển mới khi thay đổi model
uv run alembic revision --autogenerate -m "mo_ta_thay_doi"
```

---

## 7. Tài Khoản Thử Nghiệm

| Vai trò | Địa chỉ Email | Mật khẩu mặc định | Quyền hạn |
|---|---|---|---|
| Admin | admin@space247.vn | Password123@ | Toàn quyền quản trị hệ thống |
| Agent | agent@space247.vn | Password123@ | Quyền đăng tin, cập nhật tin đăng và sử dụng Agent AI Co-Pilot |
| User | Đăng ký tại `/api/v1/auth/register` | Tùy chọn | Tìm kiếm, lưu yêu thích, tạo cảnh báo và tính vay |
