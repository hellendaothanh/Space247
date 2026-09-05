# Danh Mục Công Nghệ và Quyết Định Kỹ Thuật (Tech Stack & ADRs)

Tài liệu này định nghĩa chi tiết các công nghệ cốt lõi, phiên bản chính xác và luận chứng kỹ thuật đằng sau mỗi lựa chọn kiến trúc trong hệ sinh thái Space247.

---

## 1. Bảng Tổng Hợp Công Nghệ Cốt Lõi

| Phân tầng | Công nghệ | Phiên bản | Mục đích & Trách nhiệm chính |
|---|---|---|---|
| **Backend Framework** | FastAPI | 0.115+ (Python >= 3.11) | Máy chủ API RESTful bất đồng bộ, tự động sinh tài liệu OpenAPI |
| **Cơ sở dữ liệu Quan hệ** | PostgreSQL | 16.2 | Lưu trữ dữ liệu quan hệ, bảo đảm tính toàn vẹn giao dịch ACID |
| **Mở rộng Tìm kiếm Vector** | pgvector | 0.7+ | Lưu trữ vector 768 chiều và tăng tốc truy vấn qua chỉ mục HNSW |
| **Mở rộng Địa không gian** | PostGIS | 3.4+ | Lưu trữ hình học không gian (Geometry Point 4326), chỉ mục GiST |
| **Bộ nhớ đệm Tốc độ cao** | Redis | 7.2 | Bộ nhớ đệm phân tán trong bộ nhớ, quản lý phiên và hạn chế tần suất |
| **Mô hình Vector Embedding** | FastEmbed | `paraphrase-multilingual-mpnet-base-v2` | Sinh vector ngữ nghĩa 768 chiều tối ưu cho tiếng Việt và đa ngôn ngữ |
| **Trí tuệ Nhân tạo & LLM** | Google Gemini API | 1.5 / 2.0 | Trợ lý tư vấn hội thoại và AI Co-Pilot hỗ trợ tạo tin đăng |
| **Frontend Web** | Next.js (App Router) | 16.3.4 | Nền tảng React phục vụ kết xuất phía máy chủ (SSR) và tối ưu SEO |
| **Thư viện Giao diện Web** | React & React DOM | 19.2.5 | Xây dựng thành phần giao diện người dùng có tính tương tác cao |
| **Bộ định kiểu CSS** | Tailwind CSS | 4.2.3 | Định kiểu giao diện tiện ích hiện đại với hiệu năng biên dịch cao |
| **Frontend Mobile** | Flutter SDK | >= 3.13.2 | Ứng dụng di động đa nền tảng (iOS và Android) native |
| **Quản lý Trạng thái Mobile** | Riverpod | 2.5+ | Quản lý trạng thái và tiêm phụ thuộc (Dependency Injection) an toàn |
| **Kết nối Mạng Mobile** | Dio | 5.4+ | Thư viện HTTP Client nâng cao với Interceptor và tự động thử lại |
| **Quản lý Gói Python** | uv (Astral) | 0.5+ | Trình quản lý môi trường ảo và giải quyết xung đột thư viện cực nhanh |

---

## 2. Luận Chứng Lựa Chọn Kỹ Thuật Chi Tiết

### 2.1. Backend: FastAPI (Python 3.11+) kết hợp SQLAlchemy 2.0 Async
- **Lý do lựa chọn**:
  - Kiến trúc hướng bất đồng bộ (`async`/`await`) dựa trên chuẩn ASGI và `uvicorn`, giúp tối đa hóa thông lượng xử lý I/O trên một luồng CPU mà không gây nghẽn luồng.
  - Sử dụng trình điều khiển `asyncpg` - trình điều khiển PostgreSQL nhanh nhất hiện nay cho Python, tận dụng giao thức nhị phân trực tiếp với PostgreSQL.
  - Tích hợp chặt chẽ với Pydantic v2 (viết bằng Rust) cho khả năng tuần tự hóa và xác thực dữ liệu nhanh gấp 5-10 lần so với Pydantic v1.
  - Khả năng tự động sinh tài liệu Swagger UI và ReDoc chuẩn OpenAPI 3.0 mà không cần viết cấu hình phụ trợ.
- **Đánh đổi & Biện pháp khắc phục**:
  - Toàn bộ chuỗi gọi từ Route, Service đến Repository phải tuân thủ nghiêm ngặt mô hình `async`; bất kỳ lệnh I/O đồng bộ nào (blocking call) cũng phải được chuyển sang ThreadPool.

### 2.2. Lưu trữ Dữ liệu: PostgreSQL 16 + pgvector + PostGIS
- **Lý do lựa chọn**:
  - **Hợp nhất kiến trúc (Single Database Architecture)**: Thay vì phải vận hành đồng thời 3 hệ thống riêng biệt (PostgreSQL cho dữ liệu quan hệ, Pinecone/Milvus cho vector, Elasticsearch cho full-text), việc tích hợp `pgvector` và `PostGIS` trực tiếp vào PostgreSQL 16 giúp loại bỏ hoàn toàn bài toán phân tán dữ liệu, trễ sao chép (replication lag) và giao dịch phân tán.
  - **pgvector với HNSW (Hierarchical Navigable Small World)**: Cung cấp tốc độ tìm kiếm vector gần đúng (ANN) với độ chính xác cao và thông lượng lớn gấp hàng chục lần so với chỉ mục IVFFlat truyền thống.
  - **PostGIS**: Tiêu chuẩn vàng trong ngành Hệ thống thông tin địa lý (GIS). Cho phép thực hiện các phép tính khoảng cách hình học thực trên bề mặt Trái Đất (Ellipsoid WGS84 - EPSG:4326) qua các hàm không gian như `ST_DWithin`, `ST_DistanceSphere` và `ST_MakePolygon`.

### 2.3. Mô hình Nhúng Ngôn ngữ: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` qua FastEmbed
- **Lý do lựa chọn**:
  - Không gian biểu diễn vector 768 chiều cho độ sâu ngữ nghĩa vượt trội so với các mô hình 384 chiều mini, bảo đảm nắm bắt tốt các sắc thái ngôn ngữ tiếng Việt (bao gồm cả đại từ, từ ghép địa danh và mô tả phong cách sống).
  - Sử dụng thư viện `FastEmbed` chạy trực tiếp trên ONNX Runtime với bộ tăng tốc SIMD/AVX của CPU, cho phép suy luận vector cục bộ với độ trễ thấp (<30ms) mà không phụ thuộc vào đường truyền Internet hoặc hạn mức của các API bên ngoài.

### 2.4. Tầng Đệm: Redis 7
- **Lý do lựa chọn**:
  - Tốc độ phản hồi dưới 1 mili-giây (sub-millisecond) đối với các truy vấn đọc phổ biến.
  - Khả năng thiết lập TTL linh hoạt theo từng không gian khóa, tự động thu hồi bộ nhớ qua thuật toán LRU (Least Recently Used).
  - Giảm tải trực tiếp hơn 80% truy vấn nặng vào PostgreSQL trong các kịch bản người dùng tìm kiếm lặp lại cùng một tiêu chí.

### 2.5. Frontend Web: Next.js 16 (App Router) + React 19 + Tailwind CSS v4
- **Lý do lựa chọn**:
  - **Next.js App Router**: Cho phép kết xuất phía máy chủ (Server-Side Rendering) và nén tĩnh (Static Site Generation), yếu tố quyết định sống còn đối với các trang thông tin bất động sản cần tối ưu chỉ số tìm kiếm Google (SEO) và điểm Core Web Vitals (LCP, INP).
  - **React 19**: Hỗ trợ các tính năng mới nhất như Server Components, Server Actions và tối ưu hóa kết xuất giao diện.
  - **Tailwind CSS v4**: Được viết lại bằng Rust (Oxygen engine), loại bỏ tệp `tailwind.config.js` truyền thống, biên dịch CSS tức thì và giảm dung lượng CSS xuất xưởng về mức tối thiểu.

### 2.6. Frontend Mobile: Flutter 3.x + Riverpod
- **Lý do lựa chọn**:
  - Cung cấp trải nghiệm gốc (Native 60/120 FPS) trên cả hệ điều hành Android và iOS từ một cơ sở mã nguồn duy nhất.
  - Riverpod: Hệ thống quản lý trạng thái có tính an toàn cao tại thời điểm biên dịch (Compile-time safety), không phụ thuộc vào `BuildContext` như Provider cũ, dễ dàng thực hiện unit test và mock dữ liệu mạng.
