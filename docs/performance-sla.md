# Cam Kết Mức Dịch Vụ & Định Chuẩn Hiệu Năng (SLA & Performance Benchmarks)

Tài liệu này xác định các cam kết chất lượng dịch vụ (Service Level Agreement - SLA), định chuẩn độ trễ mục tiêu (Latency Targets), cơ chế đo lường và phương pháp kiểm thử tải trọng (Load Testing) áp dụng cho hệ thống Space247.

---

## 1. Chỉ Số Hiệu Năng Mục Tiêu (SLA Latency Targets)

Các định chuẩn dưới đây được áp dụng trên môi trường sản xuất với cấu hình phần cứng tiêu chuẩn (4 vCPU, 8 GB RAM, ổ lưu trữ NVMe SSD) trên quy mô dữ liệu 10.000 bất động sản:

| Loại tác vụ | Phân vị P50 | Phân vị P95 | Phân vị P99 | Điều kiện & Tiêu chí đo lường |
|---|---|---|---|---|
| **Bộ nhớ đệm Redis (Cache Hit)** | < 5 ms | < 15 ms | < 30 ms | Kết quả tìm kiếm hoặc chi tiết BĐS có sẵn trong Redis 7 |
| **Tìm kiếm Vector Cosine (HNSW)** | < 45 ms | < 80 ms | < 120 ms | Truy vấn ANN qua pgvector HNSW `m=16, ef=64` không lọc |
| **Tìm kiếm Lai RRF (Hybrid Search)** | < 110 ms | < 200 ms | < 350 ms | Kết hợp Vector ANN + GIN FTS tiếng Việt + Reciprocal Rank Fusion |
| **Truy vấn Đọc/Ghi CSDL (CRUD)** | < 25 ms | < 50 ms | < 90 ms | Lấy danh sách phân trang hoặc cập nhật 1 bản ghi bất động sản |
| **Tìm kiếm Địa không gian (Isochrone)**| < 120 ms | < 250 ms | < 400 ms | Phép toán PostGIS `ST_DWithin` và lọc đa giác vùng di chuyển |
| **Định giá AVM AI (Weighted KNN)** | < 80 ms | < 180 ms | < 300 ms | Thuật toán Weighted KNN quét bán kính 2.5 km - 8.0 km |
| **Thời gian Tải trang Web (LCP)** | < 1.2 s | < 2.0 s | < 2.5 s | Largest Contentful Paint trên Next.js 16 SSR |

---

## 2. Chiến Lược Giám Sát & Đo Lường (Monitoring & Profiling)

### 2.1. Middleware Đo Lường Thời Gian Xử Lý Yêu Cầu (HTTP Request Profiling)
Mỗi yêu cầu gửi đến hệ thống đều được gắn mã định danh tương quan `X-Request-ID` và tính toán tổng thời gian thực thi (Round-Trip Latency) thông qua HTTP Middleware:

```python
# Cấu trúc ghi nhận header thời gian phản hồi
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time-Ms"] = f"{process_time * 1000:.2f}"
    return response
```

Hệ thống nhật ký (Logging) ghi lại cấu trúc phân tích thời gian theo định dạng chuẩn:
```json
{
  "timestamp": "2026-09-05T07:30:00Z",
  "request_id": "req-9f2b8c1a",
  "method": "POST",
  "endpoint": "/api/v1/properties/search",
  "status_code": 200,
  "duration_ms": 118.4,
  "db_query_ms": 62.1,
  "embedding_ms": 28.3,
  "cache_status": "MISS"
}
```

### 2.2. Chỉ Số Hiệu Quả Bộ Nhớ Đệm (Cache Hit Ratio Monitoring)
- **Mục tiêu cam kết**: Tỷ lệ Cache Hit của các truy vấn tìm kiếm phổ biến và chi tiết bất động sản phải đạt **>= 80%** trong điều kiện vận hành ổn định.
- **Công thức tính**:
  $$\text{Cache Hit Ratio} = \frac{\text{Tổng số lượt Cache Hit}}{\text{Tổng số lượt yêu cầu}} \times 100\%$$
- **Cơ chế cảnh báo (Alert Triggers)**:
  - Cảnh báo mức **Warning**: Khi Cache Hit Ratio giảm xuống dưới **70%** liên tục trong 15 phút.
  - Cảnh báo mức **Critical**: Khi Cache Hit Ratio giảm xuống dưới **50%** hoặc số lỗi kết nối Redis tăng đột biến (> 5 lỗi/phút).

---

## 3. Kế Hoạch & Phương Pháp Kiểm Thử Tải Trọng (Load Testing Methodology)

### 3.1. Kịch Bản Tải Trọng Mục Tiêu (Target Scenarios)
1. **Kịch bản Tải thông thường (Baseline Concurrency)**:
   - 20 kết nối đồng thời (20 Virtual Users).
   - Tần suất: 50 requests/giây (RPS) trải đều trên các endpoint `/properties`, `/search/semantic`, `/spatial/amenities/heatmap`.
   - Tiêu chuẩn chấp thuận: Tỷ lệ lỗi 0%, P95 < 100 ms.
2. **Kịch bản Tải cao điểm (Stress Concurrency)**:
   - 100 kết nối đồng thời (100 Virtual Users) gửi yêu cầu liên tục trong thời gian 5 phút.
   - Tần suất: 200 - 300 RPS.
   - Tỷ trọng truy vấn: 60% Hybrid Search, 25% Chi tiết BĐS, 10% Isochrone Map, 5% Tạo tin đăng/Định giá.
   - Tiêu chuẩn chấp thuận: Tỷ lệ lỗi < 0.1%, P95 < 300 ms, không xuất hiện hiện tượng rò rỉ bộ nhớ (Memory Leak) hoặc nghẽn luồng kết nối cơ sở dữ liệu (Connection Pool Exhaustion).

### 3.2. Quy Trình Thực Thi Kiểm Thử Tải Nội Bộ
Kiểm thử tải định kỳ có thể thực thi thông qua kịch bản kiểm chuẩn hoặc công cụ mã nguồn mở (như Locust / k6):

```bash
# Ví dụ cấu hình kiểm thử k6 mô phỏng 100 người dùng đồng thời
k6 run --vus 100 --duration 5m scripts/load_test_search.js
```

Các chỉ số thu thập sau kiểm thử:
- Tổng số yêu cầu hoàn thành (Total Completed Requests).
- Thông lượng trung bình (Throughput in req/s).
- Phân phối độ trễ (P50, P90, P95, P99).
- Tỷ lệ lỗi HTTP 5xx / 4xx (Error Rate).
- Mức độ chiếm dụng tài nguyên CPU/RAM của container `postgres` và `uvicorn`.
