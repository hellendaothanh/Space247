# Space247 — Nền Tảng Bất Động Sản Trí Tuệ Nhân Tạo (AI Real Estate Platform)

Space247 là nền tảng công nghệ bất động sản (PropTech) thế hệ mới tích hợp **Trợ lý AI Chatbot Tư Vấn Bất Động Sản Trực Tuyến**, **AI Semantic Search (Tìm kiếm ngữ nghĩa)** và **Hybrid Search (Vector Cosine + Full-Text Search RRF)**, mang đến trải nghiệm tìm kiếm và kết nối bất động sản thông minh, trực quan và tốc độ cao.

---

## 1. Kiến Trúc Tổng Quan (System Architecture)

\`\`\`mermaid
graph TD
    ClientWeb["Frontend Web - Next.js 16<br/>(Bản đồ, Dashboard, Chat Widget)"] -->|HTTP REST and Bearer JWT| API["Backend API - FastAPI / Uvicorn"]
    ClientMobile["Frontend Mobile - Flutter"] -->|HTTP REST and Bearer JWT| API
    API -->|Chat Assistant Engine| Assistant["AI Chat Assistant Service<br/>(Intent & Criteria Extraction)"]
    Assistant -->|Hybrid Search Trigger| HybridEngine["Hybrid Search Engine"]
    API -->|Async Session| DB[("PostgreSQL 16 + pgvector + PostGIS")]
    API -->|Async Cache 15m-60m TTL| Redis[("Redis 7 Cache")]
    API -->|Embeddings| FastEmbed["Embedding Service - 768 dim"]
    DB -->|HNSW Vector Index| VectorSearch["Vector Cosine Search"]
    DB -->|GIN Index simple dict| FTS["Vietnamese Full-Text Search"]
    DB -->|GiST Spatial Index SRID 4326| GeoSearch["PostGIS Spatial / Isochrone Search"]
    VectorSearch -->|RRF Fusion| HybridResults["Hybrid Ranked Results"]
    FTS -->|RRF Fusion| HybridResults
    HybridResults --> Assistant
\`\`\`

* **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 Async, Pydantic v2, Alembic, FastEmbed (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, vector 768 chiều).
* **AI Chat Assistant**: Trợ lý tư vấn BĐS thông minh — trích xuất tiêu chí (giá, vị trí, tiện ích, loại hình), tự động truy vấn CSDL qua Hybrid Search RRF và phản hồi tự nhiên kèm thẻ bài đăng trực tiếp.
* **Cache Layer**: Redis 7 async — cache tìm kiếm ngữ nghĩa/hybrid (`cache:search:*`), chi tiết BĐS (`cache:property:*`) TTL 15 phút; Isochrone & POI data TTL 60 phút.
* **Database**: PostgreSQL 16 với `pgvector` (HNSW index) + `PostGIS` (GiST Spatial index SRID 4326) + Full-Text Search GIN index đa trường.
* **Frontend Web**: Next.js 16.3.4 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide Icons, Leaflet, ReactMarkdown, Floating Chat Widget.
* **Authentication**: JWT Bearer Token (HS256) + `bcrypt` hashing, phân quyền Role (`user`, `agent`, `admin`).
* **Shared SDK**: DTOs TypeScript và API Client tại `frontend/shared/` dùng chung Web & Mobile.

---

## 2. Yêu Cầu Môi Trường (Prerequisites)

| Phần mềm | Phiên bản | Mục đích |
|---|---|---|
| Docker & Docker Compose | Latest | PostgreSQL + pgvector/PostGIS + Redis |
| Python | ≥ 3.11 | Backend FastAPI |
| `uv` | Latest | Quản lý gói Python |
| Node.js | ≥ 20 LTS | Frontend Web |
| Flutter SDK | ≥ 3.13 | Frontend Mobile |

**Cài đặt `uv`:**
\`\`\`bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
\`\`\`

---

## 3. Khởi Chạy Nhanh Một Chạm (Quick Start)

\`\`\`bash
# Linux / macOS
chmod +x scripts/*.sh && ./scripts/start-dev.sh

# Windows (PowerShell)
.\scripts\start-dev.ps1
\`\`\`

Sau khi khởi chạy:
| Service | URL |
|---|---|
| Frontend Web | http://localhost:3000 |
| Backend API | http://localhost:8080 |
| Swagger UI (Interactive Docs) | http://localhost:8080/api/v1/docs |

---

## 4. Hướng Dẫn Thiết Lập Thủ Công (Manual Setup)

### Bước 1: Khởi động PostgreSQL + Redis
\`\`\`bash
docker compose up -d postgres redis
\`\`\`

### Bước 2: Cấu hình môi trường backend
\`\`\`bash
cd backend && cp .env.example .env
\`\`\`

### Bước 3: Đồng bộ schema database (Alembic)
\`\`\`bash
cd backend && uv run alembic upgrade head
\`\`\`

Lịch sử migration:
| Revision | Nội dung |
|---|---|
| `0001` | Bảng `properties` + pgvector HNSW + PostGIS geom |
| `0002` | Bảng `users` + FK `user_id` trong `properties` |
| `0003` | Bảng `favorite_properties` |
| `0004` | Bảng `saved_search_alerts` + `user_notifications` |
| `0005` | Cột `images TEXT[]` vào `properties` + `avatar_url VARCHAR` vào `users` |

### Bước 4: Nạp dữ liệu mẫu
\`\`\`bash
# Linux/macOS
./scripts/seed-data.sh

# Hoặc chạy trực tiếp
cd backend && uv run python -m scripts.seed_properties
\`\`\`

> [!NOTE]
> Script seeding là **idempotent** — chạy lại nhiều lần không tạo dữ liệu trùng.

**Tài khoản mẫu:**
| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin | `admin@space247.vn` | `Password123@` |
| Agent | `agent@space247.vn` | `Password123@` |

### Bước 5: Khởi động backend
\`\`\`bash
cd backend
uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
\`\`\`

### Bước 6: Khởi động frontend web
\`\`\`bash
cd frontend/web
cp .env.example .env.local
npm install && npm run dev
\`\`\`

### Bước 7 (tuỳ chọn): Khởi chạy mobile Flutter
\`\`\`bash
cd frontend/mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080/api/v1
\`\`\`

---

## 5. Danh Sách Endpoint API (API Reference)

> Tất cả endpoint có tiền tố `/api/v1`. Swagger UI đầy đủ: `http://localhost:8080/api/v1/docs`

### Auth & Người dùng
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/auth/register` | — | Đăng ký tài khoản mới, trả về JWT |
| POST | `/auth/login` | — | Đăng nhập, trả về JWT Bearer token |
| GET | `/auth/me` | ✅ | Lấy thông tin hồ sơ người dùng đang đăng nhập |
| PUT | `/auth/me` | ✅ | Cập nhật hồ sơ (`full_name`, `phone`, `avatar_url`) |

### Bất động sản
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| GET | `/properties` | — | Danh sách BĐS với phân trang và bộ lọc |
| POST | `/properties` | ✅ | Đăng tin mới (tự sinh embedding 768-dim, gán owner, lưu `images[]`) |
| GET | `/properties/{id}` | — | Chi tiết BĐS — `images[]`, thông tin `agent`, toạ độ |
| PUT | `/properties/{id}` | ✅ | Cập nhật BĐS (tự tái sinh embedding khi sửa nội dung) |
| GET | `/properties/my` | ✅ | Bài đăng của người dùng hiện tại |
| GET | `/properties/favorites` | ✅ | BĐS đã lưu yêu thích |
| POST | `/properties/{id}/favorite` | ✅ | Toggle lưu / bỏ yêu thích |
| POST | `/properties/compare` | — | **So sánh AI** 2–3 căn theo đơn giá/m², vị trí, tiềm năng |

### Tìm kiếm
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/properties/search` | — | **Hybrid Search**: Vector Cosine + Full-Text RRF |
| POST | `/search/semantic` | — | Tìm kiếm thuần vector embedding 768 chiều |

### AI Chat Assistant
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/chat/assistant` | — | Chatbot trích xuất tiêu chí tự nhiên, gọi Hybrid Search, phân tích tài chính |

### Agent AI Co-Pilot
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/agent/listing/generate` | ✅ Agent+ | AI sinh tiêu đề SEO + mô tả Markdown + trích xuất thông số |
| POST | `/agent/valuation/estimate` | ✅ Agent+ | Smart AVM định giá Weighted KNN bán kính 2.5–8 km |

### Địa không gian (Spatial)
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/spatial/isochrone-search` | — | BĐS trong vùng di chuyển 5–30 phút (xe máy/ô tô/đi bộ) |
| GET | `/spatial/amenities/heatmap` | — | Bản đồ nhiệt tiện ích lân cận (trường học, bệnh viện, metro, siêu thị) |

### Tài chính & Thông báo
| Method | Endpoint | Auth | Mô tả |
|:---|:---|:---:|:---|
| POST | `/financial/mortgage-calc` | — | Tính vay mua nhà (dư nợ giảm dần / niên kim cố định, lãi ưu đãi) |
| POST | `/alerts` | ✅ | Tạo cảnh báo tìm kiếm |
| GET | `/alerts` | ✅ | Danh sách cảnh báo |
| PATCH | `/alerts/{id}` | ✅ | Bật / tắt cảnh báo |
| DELETE | `/alerts/{id}` | ✅ | Xóa cảnh báo |
| GET | `/notifications` | ✅ | Danh sách thông báo in-app |
| POST | `/notifications/read-all` | ✅ | Đánh dấu tất cả đã đọc |
| GET | `/health` | — | Trạng thái hệ thống, DB & pgvector |

---

## 6. Tính Năng Nổi Bật

### 🖼️ Trang Chi Tiết BĐS Nâng Cao
- **Image Gallery Carousel** — Thumbnail strip, counter, prev/next; fallback ảnh mẫu theo loại BĐS.
- **Dynamic Agent Card** — Tên, SĐT, email, avatar thực từ DB; fallback chữ cái đầu tên.
- **Markdown Rendering** — `react-markdown + remark-gfm` (bảng, danh sách, in đậm, tiêu đề).
- **Share Button** — Web Share API native, fallback clipboard + toast.
- **Bản đồ tương tác** — OpenStreetMap / Leaflet tại toạ độ BĐS.
- **Mortgage Calculator** — Bảng tính vay tích hợp ngay trong trang chi tiết.

### 🗺️ Địa Không Gian & Bản Đồ
- **Isochrone Travel-Time Search** — Đa giác vùng di chuyển 5–30 phút; geocoding địa danh Việt Nam + Nominatim OSM.
- **Amenity Heatmap** — Bản đồ nhiệt POI kèm markers tương tác.

### 🤖 Agent AI Co-Pilot
- **AI Listing Generator** — Gemini Multimodal phân tích ảnh sổ đỏ/mặt bằng, sinh tiêu đề SEO + bài Markdown + trích xuất thông số.
- **Smart AVM Pricing Advisor** — Weighted KNN bán kính 2.5 km (mở rộng tới 8 km), thanh đo lệch giá 3 mức, confidence score.

### 🔔 Giữ Chân Người Dùng & Tài Chính
- **Saved Search Alerts** — Engine khớp nền tự động thông báo bài đăng mới phù hợp tiêu chí.
- **Mortgage Calculator** — Dư nợ giảm dần & niên kim cố định, lãi ưu đãi, lịch trả nợ từng tháng.
- **Notification Bell** — Badge chưa đọc trên Navbar, panel dropdown thông báo in-app.

---

## 7. Kiểm Thử (Testing)

### Backend
\`\`\`bash
cd backend && uv run pytest
\`\`\`
> **101/101 tests PASS** — Bao phủ: migrations (0001–0005), Auth RBAC, Property CRUD & images & agent, Agent AI Co-Pilot, PostGIS Spatial, AI Comparison, AI Chatbot, Hybrid Search, Semantic Search, Redis Cache, Alerts & Notifications, Seeding.

### Frontend Web
\`\`\`bash
cd frontend/web
npx tsc --noEmit   # 0 errors
npm run build      # 9/9 routes — SUCCESS
\`\`\`

### Mobile
\`\`\`bash
cd frontend/mobile && flutter pub get && flutter run
\`\`\`

---

## 8. Cấu Trúc Thư Mục

\`\`\`
Space247/
├── backend/
│   ├── migrations/versions/        # Alembic migrations 0001–0005
│   ├── scripts/                    # seed_properties.py & utilities
│   ├── src/
│   │   ├── api/v1/endpoints/       # auth, properties, search, chat, agent,
│   │   │                           #   spatial, financial, alerts, notifications, health
│   │   ├── core/                   # config, database, redis cache, security (JWT/bcrypt)
│   │   ├── models/                 # User, Property (images[], geom PostGIS, embedding VECTOR)
│   │   ├── schemas/                # Pydantic v2: property, user, chat, agent, spatial, alerts
│   │   └── services/               # EmbeddingService, ChatAssistantService,
│   │                               #   AlertMatchingService, AIComparisonService
│   └── tests/                      # 101 pytest test cases
├── frontend/
│   ├── shared/                     # types.ts, api-client.ts, constants.ts
│   ├── web/                        # Next.js 16.3.4 App Router
│   │   ├── src/components/         # PropertyGallery, PropertyShareButton, PropertyDetailMap,
│   │   │                           #   MortgageCalculator, ChatAssistantWidget, Navbar, ...
│   │   └── src/app/                # /, /properties/[id], /properties/create,
│   │                               #   /properties/my, /favorites, /profile/alerts,
│   │                               #   /login, /register
│   └── mobile/                     # Flutter — Riverpod, Dio, cached_network_image,
│                                   #   flutter_map, flutter_markdown, share_plus, url_launcher
├── scripts/
│   ├── start-dev.sh / .ps1         # One-click starter
│   └── seed-data.sh / .ps1         # Standalone seeder
├── docs/architecture/              # Architecture & design specs
├── docker-compose.yml              # PostgreSQL 16 + pgvector/PostGIS + Redis
└── README.md
\`\`\`

---

## 9. Schema Database (revision head: 0005)

| Bảng | Cột quan trọng |
|---|---|
| `properties` | `id`, `title`, `price`, `area_sqm`, `address`, `city`, `lat/lng`, `geom` (PostGIS), `images TEXT[]`, `embedding VECTOR(768)`, `user_id FK`, `status` |
| `users` | `id`, `email`, `hashed_password`, `full_name`, `phone`, `avatar_url`, `role`, `is_active` |
| `favorite_properties` | `user_id FK`, `property_id FK`, `created_at` |
| `saved_search_alerts` | `user_id FK`, `title`, `criteria JSON`, `frequency`, `is_active`, `last_notified_at` |
| `user_notifications` | `user_id FK`, `alert_id FK`, `property_id FK`, `title`, `message`, `is_read` |

---

## 10. Giấy Phép (License)

Dự án được phát triển cho hệ thống Space247 Real Estate Platform.
