# Cẩm Nang Vận Hành & Xử Lý Sự Cố Hệ Thống (Operations Runbook)

Tài liệu này cung cấp các quy trình chuẩn (Standard Operating Procedures - SOP) dành cho đội ngũ kỹ thuật khi vận hành, chẩn đoán sự cố, khắc phục tắc nghẽn và phục hồi thảm họa trên nền tảng Space247.

---

## 1. Xử Lý Sự Cố Cơ Sở Dữ Liệu & Tiện Ích Không Gian / Vector

### 1.1. Chẩn Đoán Khóa Tiến Trình & Tắc Nghẽn Tài Nguyên (Deadlock & High CPU)

#### Triệu chứng:
- API phản hồi chậm bất thường (HTTP timeout > 10s hoặc mã lỗi 504 Gateway Timeout).
- Mức độ sử dụng CPU của container `postgres` tăng vọt tới 100%.

#### Quy trình xử lý từng bước:

**Bước 1: Kiểm tra danh sách các truy vấn đang thực thi kéo dài:**
```sql
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
  AND state != 'idle'
ORDER BY duration DESC;
```

**Bước 2: Phát hiện các khóa chặn lẫn nhau (Lock Contention / Deadlocks):**
```sql
SELECT blocked_locks.pid     AS blocked_pid,
       blocked_activity.usename  AS blocked_user,
       blocking_locks.pid    AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query    AS blocked_statement,
       blocking_activity.query   AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks         blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks         blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
   AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
   AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
   AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
   AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
   AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
   AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
   AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
   AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
   AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
   AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

**Bước 3: Ngắt tiến trình gây nghẽn an toàn:**
```sql
-- Hủy truy vấn một cách hòa nhã
SELECT pg_cancel_backend(<blocking_pid>);

-- Nếu tiến trình không phản hồi sau 10 giây, chấm dứt kết nối cưỡng chế
SELECT pg_terminate_backend(<blocking_pid>);
```

---

### 1.2. Sự Cố Extension PostGIS / pgvector hoặc Container Dừng Đột Ngột

#### Triệu chứng:
- Log backend báo lỗi: `type "vector" does not exist` hoặc `type "geometry" does not exist`.
- Container cơ sở dữ liệu bị khởi động lại liên tục (CrashLoopBackOff).

#### Quy trình xử lý:
1. **Kiểm tra trạng thái container và log chi tiết:**
   ```bash
   docker compose logs --tail=100 postgres
   ```
2. **Kiểm tra và kích hoạt lại extension:**
   Kết nối trực tiếp vào cơ sở dữ liệu qua `psql`:
   ```bash
   docker compose exec postgres psql -U postgres -d real_estate_db
   ```
   Thực thi lệnh kiểm tra và kích hoạt:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS postgis;
   
   -- Xác nhận phiên bản extension đã cài đặt
   SELECT name, default_version, installed_version 
   FROM pg_available_extensions 
   WHERE name IN ('vector', 'postgis');
   ```

---

### 1.3. Lập Lại Chỉ Mục Không Gây Gián Đoạn Dịch Vụ (Zero-Downtime Re-indexing)

Khi dữ liệu bản ghi thay đổi lớn hoặc chỉ mục vector/không gian bị suy hao hiệu năng (Index Bloat), cần lập lại chỉ mục. Luôn sử dụng tùy chọn `CONCURRENTLY` để không khóa bảng (tránh gây gián đoạn các thao tác ghi và đọc):

```sql
-- Lập lại chỉ mục vector HNSW
REINDEX INDEX CONCURRENTLY ix_properties_embedding_hnsw;

-- Lập lại chỉ mục không gian PostGIS GiST
REINDEX INDEX CONCURRENTLY idx_properties_geom;

-- Lập lại chỉ mục tìm kiếm toàn văn Full-Text Search GIN
REINDEX INDEX CONCURRENTLY ix_properties_fts;
```

> Lưu ý: Lệnh `CONCURRENTLY` đòi hỏi thêm dung lượng bộ nhớ đệm và thời gian thực thi dài hơn, nhưng bảo đảm ứng dụng vẫn tiếp tục phục vụ người dùng bình thường trong suốt quá trình xử lý.

---

## 2. Xử Lý Sự Cố Bộ Nhớ Đệm (Redis Outage & Graceful Fallback)

### 2.1. Cơ Chế Tự Động Suy Giảm Tính Năng (Graceful Degradation)
Kiến trúc backend của Space247 được thiết kế chịu lỗi cao (Fault-tolerant) tại `src/core/cache.py`:
- Nếu dịch vụ Redis gặp sự cố dừng đột ngột, timeout kết nối hoặc nghẽn mạng, toàn bộ các hàm tiện ích (`get_cached_json`, `set_cached_json`, `cache_delete`) tự động bắt ngoại lệ, ghi log cảnh báo mức `WARNING` và trả về `None`.
- Luồng xử lý nghiệp vụ của FastAPI tự động chuyển hướng truy vấn trực tiếp vào PostgreSQL mà không làm gián đoạn hệ thống hoặc trả mã lỗi HTTP 500 cho người dùng cuối.

### 2.2. Quy Trình Khởi Động Lại & Làm Sạch Cache Cưỡng Chế

**Bước 1: Kiểm tra tình trạng hoạt động của dịch vụ Redis:**
```bash
docker compose ps redis
docker compose logs --tail=50 redis
```

**Bước 2: Khởi động lại dịch vụ Redis:**
```bash
docker compose restart redis
```

**Bước 3: Kiểm tra kết nối từ máy chủ ứng dụng:**
```bash
docker compose exec redis redis-cli ping
# Phản hồi mong đợi: PONG
```

**Bước 4: Xóa cache an toàn theo pattern (khi cần làm sạch dữ liệu tìm kiếm cũ):**
Nếu cần xóa toàn bộ cache tìm kiếm mà không làm mất các dữ liệu phiên đăng nhập:
```bash
# Xóa an toàn các khóa cache tìm kiếm
docker compose exec redis redis-cli --eval "for i, name in ipairs(redis.call('KEYS', 'cache:search:*')) do redis.call('DEL', name) end"

# Hoặc xóa toàn bộ bộ nhớ đệm thuộc database số 0 (nếu không dùng cho session)
docker compose exec redis redis-cli -n 0 FLUSHDB
```

---

## 3. Quy Trình Tái Sinh Dữ Liệu Vector (Vector Data Recovery & Batch Re-indexing)

### 3.1. Các Kịch Bản Cần Tái Sinh Toàn Bộ Vector:
1. **Chuyển đổi mô hình ngôn ngữ**: Khi nâng cấp từ mô hình hiện tại sang một mô hình embedding có trọng số hoặc cấu trúc từ điển mới.
2. **Khôi phục thảm họa (Disaster Recovery)**: Phục hồi cơ sở dữ liệu từ bản sao lưu dạng SQL Dump thô mà không chứa giá trị cột vector.
3. **Sửa đổi logic nối chuỗi đặc trưng**: Khi thêm thuộc tính mới của bất động sản vào văn bản đầu vào của hàm `build_property_text()`.

### 3.2. Lệnh Thực Thi Tái Sinh Vector Hàng Loạt:

Từ thư mục `backend/`:
```bash
# Kích hoạt môi trường và chạy script batch processing với cờ --reindex-vectors
cd backend
uv run python -m scripts.seed_properties --reindex-vectors
```

### 3.3. Các Bước Diễn Ra Trong Quá Trình Thực Thi:
1. Script thiết lập kết nối cơ sở dữ liệu thông qua SQLAlchemy AsyncEngine.
2. Truy vấn toàn bộ các bản ghi hiện có trong bảng `properties`.
3. Khởi tạo dịch vụ `EmbeddingService` cục bộ qua thư viện FastEmbed với mô hình `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`.
4. Duyệt qua từng bản ghi, tái tạo văn bản ngữ nghĩa từ các thuộc tính mới nhất (tiêu đề, địa chỉ, loại hình, giá, số phòng, mô tả).
5. Sinh vector 768 chiều và cập nhật trực tiếp vào cột `embedding`.
6. Thực hiện commit theo lô và ghi nhận log chi tiết tiến độ xử lý.

Sau khi hoàn tất, hệ thống tự động sẵn sàng phục vụ các truy vấn tìm kiếm ngữ nghĩa và tìm kiếm lai với độ chính xác tối đa.
