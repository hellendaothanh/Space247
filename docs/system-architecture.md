# Kiến Trúc Hệ Thống Space247 (System Architecture)

## 1. Mô Hình Kiến Trúc Phân Tầng (Multi-Tier Layered Architecture)

Space247 được thiết kế theo kiến trúc hướng dịch vụ phân tầng (Layered Service-Oriented Architecture), tối ưu hóa cho khả năng mở rộng, độ trễ thấp và tính nhất quán dữ liệu cao.

```mermaid
flowchart TD
    subgraph Client_Layer["1. Tầng Trải Nghiệm Khách Hàng (Client Tier)"]
        WebClient["Web Client<br/>(Next.js 16 App Router, React 19, TypeScript)"]
        MobileClient["Mobile Client<br/>(Flutter 3.x, Riverpod, Dio)"]
        SharedContracts["Shared SDK Contract<br/>(frontend/shared: DTOs, API Client, Constants)"]
        WebClient -.->|Tham chiếu kiểu dữ liệu| SharedContracts
        MobileClient -.->|Ánh xạ mô hình dữ liệu| SharedContracts
    end

    subgraph Gateway_Layer["2. Tầng Cổng Vào & Định Tuyến (Ingress / API Gateway)"]
        APIGateway["FastAPI Application Router (/api/v1)<br/>(CORS, Middleware, JWT Security)"]
    end

    subgraph Service_Layer["3. Tầng Dịch Vụ Nghiệp Vụ (Application Services Tier)"]
        AuthService["Authentication & RBAC<br/>(JWT HS256, bcrypt)"]
        PropertyService["Property Lifecycle Management<br/>(CRUD, My Listings, Favorites)"]
        HybridEngine["Hybrid Search Orchestrator<br/>(FastEmbed 768-dim + RRF Fusion)"]
        ChatEngine["AI Chat Assistant Service<br/>(Gemini Intent & Criteria Extraction)"]
        AgentCopilot["Agent AI Co-Pilot<br/>(Listing Generator & AVM Pricing Advisor)"]
        SpatialEngine["Spatial Analytics Service<br/>(PostGIS Isochrone & Amenity Heatmap)"]
        FinancialEngine["Financial Tools Engine<br/>(Mortgage & Amortization Scheduler)"]
        AlertEngine["Alert & Notification Engine<br/>(Background Criteria Matching)"]
    end

    subgraph Cache_Layer["4. Tầng Bộ Nhớ Đệm Tốc Độ Cao (Caching Tier)"]
        RedisCache[("Redis 7 Cache Cluster<br/>- cache:search:* (TTL 15m)<br/>- cache:property:* (TTL 15m)<br/>- cache:spatial:* (TTL 60m)")]
    end

    subgraph Storage_Layer["5. Tầng Cơ Sở Dữ Liệu & Chỉ Mục (Persistence & Indexing Tier)"]
        PostgresCore[("PostgreSQL 16 Engine<br/>(ACID Transactions, Relational Integrity)")]
        PGVectorExt[("pgvector Extension<br/>(VECTOR 768, HNSW Cosine Distance Index)")]
        PostGISExt[("PostGIS Spatial Extension<br/>(Geometry Point 4326, GiST Spatial Index)")]
        FTSExt[("Full-Text Search Engine<br/>(GIN Index, Simple Dict Lexemes)")]
        PostgresCore --- PGVectorExt
        PostgresCore --- PostGISExt
        PostgresCore --- FTSExt
    end

    WebClient -->|HTTP REST and Bearer Token| APIGateway
    MobileClient -->|HTTP REST and Bearer Token| APIGateway
    APIGateway --> AuthService
    APIGateway --> PropertyService
    APIGateway --> HybridEngine
    APIGateway --> ChatEngine
    APIGateway --> AgentCopilot
    APIGateway --> SpatialEngine
    APIGateway --> FinancialEngine
    APIGateway --> AlertEngine

    PropertyService <-->|Đọc và Xóa Cache| RedisCache
    HybridEngine <-->|Đọc và Ghi Cache| RedisCache
    SpatialEngine <-->|Đọc và Ghi Cache| RedisCache

    PropertyService -->|Async SQLAlchemy Session| PostgresCore
    HybridEngine -->|Vector and Text Queries| PostgresCore
    SpatialEngine -->|ST_DWithin and ST_MakePolygon| PostgresCore
    AlertEngine -->|JSONB Query Criteria| PostgresCore
```

---

## 2. Luồng Dữ Liệu Qua Hợp Đồng Dùng Chung (Data Flow via Shared SDK)

Nhằm loại bỏ rủi ro sai lệch cấu trúc dữ liệu giữa giao diện Web và ứng dụng Di động, dự án áp dụng mô hình Hợp đồng Dùng chung (Single Source of Truth) tại `frontend/shared/`:

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as Giao diện Web / Mobile
    participant SDK as Shared SDK (types.ts / api-client.ts)
    participant API as Backend FastAPI Router (/api/v1)
    participant Cache as Redis 7 Cache
    participant DB as PostgreSQL 16 (pgvector + PostGIS)

    User->>UI: Nhập truy vấn: "Tìm chung cư Cầu Giấy 3 phòng ngủ dưới 5 tỷ"
    UI->>SDK: searchProperties(HybridSearchRequest)
    SDK->>API: POST /api/v1/properties/search {query, filters, limit}
    API->>Cache: Kiểm tra khóa cache:search:{md5_hash}
    alt Có dữ liệu trong Cache (Cache Hit)
        Cache-->>API: Trả về danh sách kết quả JSON
    else Không có trong Cache (Cache Miss)
        API->>API: Gọi FastEmbed tạo vector truy vấn 768 chiều
        par Truy vấn đồng thời
            API->>DB: Truy vấn Vector Cosine qua HNSW Index
            API->>DB: Truy vấn Full-Text qua GIN Index tiếng Việt
        end
        API->>API: Hợp nhất và chấm điểm theo công thức Reciprocal Rank Fusion (RRF)
        API->>Cache: Lưu kết quả vào Redis với TTL 900 giây (15 phút)
    end
    API-->>SDK: Trả về PaginatedResponse<PropertyResponse>
    SDK-->>UI: Cung cấp DTO đã được xác thực an toàn kiểu dữ liệu
    UI-->>User: Hiển thị danh sách thẻ bài đăng kèm điểm tương đồng
```

---

## 3. Chiến Lược Bộ Nhớ Đệm (Caching Strategy)

Hệ thống triển khai mẫu kiến trúc **Cache-aside** (Lazy Loading) kết hợp cơ chế **Chủ động Vô hiệu hóa (Proactive Cache Invalidation)**:

### 3.1. Cấu Trúc Khóa Cache (Key Namespaces)
- `cache:search:{hash}`: Lưu kết quả các truy vấn tìm kiếm ngữ nghĩa và tìm kiếm lai. Khóa được tạo từ mã băm MD5 của chuỗi truy vấn kèm bộ lọc.
  - **Thời gian sống (TTL)**: 900 giây (15 phút).
- `cache:property:{property_id}`: Lưu dữ liệu chi tiết của từng bất động sản đơn lẻ.
  - **Thời gian sống (TTL)**: 900 giây (15 phút).
- `cache:spatial:{hash}`: Lưu kết quả tính toán vùng di chuyển Isochrone và bản đồ nhiệt tiện ích (POI Heatmap).
  - **Thời gian sống (TTL)**: 3600 giây (60 phút) do hạ tầng giao thông và tiện ích ít biến động.

### 3.2. Cơ Chế Vô Hiệu Hóa (Invalidation Rules)
Khi có bất kỳ hành vi thay đổi dữ liệu nào (Thêm mới, Cập nhật, Xóa bài đăng):
1. **Xóa trực tiếp**: Gọi `cache_delete(f"cache:property:{property_id}")` để loại bỏ bản ghi chi tiết đã cũ.
2. **Quét và xóa hàng loạt**: Gọi hàm quét mẫu `cache_delete_pattern("cache:search:*")` để hủy bỏ các kết quả tìm kiếm đã lưu trong bộ nhớ đệm, bảo đảm người dùng luôn nhận được dữ liệu mới nhất trong lần tìm kiếm tiếp theo.

---

## 4. Cơ Chế Tìm Kiếm Lai RRF (Hybrid Search with Reciprocal Rank Fusion)

Để đạt được độ chính xác cao nhất đối với ngôn ngữ tiếng Việt (bao gồm cả từ khóa địa lý cụ thể lẫn mô tả nhu cầu trừu tượng), hệ thống kết hợp song song hai nhánh tìm kiếm:

```mermaid
flowchart LR
    Query["Truy vấn người dùng<br/>'nhà phố kinh doanh Cầu Giấy'"] --> Embedding["FastEmbed Embedding<br/>(Vector 768-dim)"]
    Query --> Lexical["Bộ phân tích từ vựng<br/>(PostgreSQL to_tsquery 'simple')"]

    Embedding --> VectorSearch["Nhánh 1: Vector Search<br/>pgvector HNSW Cosine Distance"]
    Lexical --> TextSearch["Nhánh 2: Full-Text Search<br/>GIN Index tiếng Việt"]

    VectorSearch --> RankVector["Xếp hạng Vector<br/>Rank_v: 1, 2, 3..."]
    TextSearch --> RankText["Xếp hạng Văn bản<br/>Rank_t: 1, 2, 3..."]

    RankVector --> RRFBlock["Thuật toán Reciprocal Rank Fusion (RRF)<br/>Score = 1/(k + Rank_v) + 1/(k + Rank_t)<br/>Hằng số làm mịn k = 60"]
    RankText --> RRFBlock

    RRFBlock --> FinalResult["Danh sách kết quả hợp nhất<br/>Sắp xếp theo RRF Score giảm dần"]
```

### Công Thức Toán Học Reciprocal Rank Fusion (RRF)
Điểm số hợp nhất của một tài liệu $d$ được tính theo công thức:
$$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
Trong đó:
- $M$: Tập hợp các phương thức xếp hạng bao gồm $\{VectorSearch, FullTextSearch\}$.
- $r_m(d)$: Thứ hạng của tài liệu $d$ trong danh sách kết quả của phương thức $m$ (bắt đầu từ $1$).
- $k$: Hằng số làm mịn (smoothing factor), được cấu hình mặc định là $60$ theo chuẩn nghiên cứu của Cormack et al. nhằm giảm thiểu độ lệch của các kết quả cá biệt ở đầu danh sách.

### Lợi Ích Của Kiến Trúc RRF
1. **Khắc phục điểm yếu của Vector thuần túy**: Vector Embedding có thể bỏ sót các mã dự án hoặc tên phố hiếm gặp; Full-Text Search xử lý hoàn hảo trường hợp này.
2. **Khắc phục điểm yếu của Tìm kiếm từ khóa**: Khi người dùng mô tả nhu cầu phong cách sống hoặc tiện ích tương đương mà không gõ đúng từ khóa, Vector Cosine bù đắp độ tương đồng ngữ nghĩa.
3. **Không phụ thuộc thang điểm tuyệt đối**: RRF chỉ quan tâm tới thứ hạng tương đối của từng kết quả, giúp triệt tiêu sự khác biệt về phân phối điểm số giữa khoảng cách Cosine và điểm số ts_rank.
