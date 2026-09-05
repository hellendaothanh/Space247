# Tổng Quan Dự Án Space247 (Project Overview)

## 1. Bối Cảnh Bài Toán PropTech Tại Việt Nam

Thị trường bất động sản trực tuyến tại Việt Nam hiện nay đối mặt với nhiều thách thức mang tính cố hữu:
- **Dữ liệu phân mảnh và thiếu chuẩn hóa**: Các tin đăng thường chứa thông tin mô tả phi cấu trúc, văn phong tự do, sử dụng nhiều thuật ngữ địa phương hoặc từ lóng (như *"nhà hẻm ba gác"*, *"sổ hồng chính chủ"*, *"nở hậu"*, *"view thoáng ngắm pháo hoa"*).
- **Hạn chế của công cụ tìm kiếm truyền thống**: Đa số các cổng thông tin hiện hành dựa trên truy vấn từ khóa chính xác (Keyword Matching) hoặc lọc theo các trường cứng (Giá, Diện tích, Quận/Huyện). Khi người dùng tìm kiếm theo nhu cầu ngữ nghĩa phức tạp (ví dụ: *"căn hộ yên tĩnh gần trường quốc tế, ngân sách dưới 4 tỷ"*) hoặc tìm theo thời gian di chuyển thực tế (Isochrone), các công cụ truyền thống không thể đáp ứng hiệu quả, dẫn đến tỷ lệ bỏ rơi nền tảng cao.
- **Quy trình định giá và thẩm định phụ thuộc cảm tính**: Người bán và môi giới thiếu các công cụ định giá tự động (Automated Valuation Model - AVM) dựa trên vị trí địa lý và các bất động sản tương đồng lân cận, dẫn đến tình trạng loạn giá hoặc thời gian thanh khoản kéo dài.
- **Rào cản tạo nội dung tin đăng**: Môi giới tốn nhiều thời gian soạn bài, xử lý ảnh mặt bằng, sổ đỏ và tối ưu hóa từ khóa SEO.

Nền tảng **Space247** ra đời nhằm giải quyết triệt để các hạn chế trên thông qua sự kết hợp giữa mô hình ngôn ngữ lớn (LLM), công nghệ nhúng vector đa ngữ (Multilingual Embeddings), cơ sở dữ liệu không gian PostGIS và kiến trúc tìm kiếm lai (Hybrid Search).

---

## 2. Mục Tiêu Dự Án (Project Goals)

1. **Chuẩn hóa và thông minh hóa tìm kiếm bất động sản**:
   - Cung cấp tính năng tìm kiếm ngữ nghĩa (Semantic Search) hiểu được nhu cầu thực tế của người dùng bằng tiếng Việt tự nhiên.
   - Kết hợp thuật toán Reciprocal Rank Fusion (RRF) để hợp nhất kết quả giữa tìm kiếm ngữ nghĩa vector và tìm kiếm toàn văn (Full-Text Search).
   - Cho phép tìm kiếm theo bán kính di chuyển thực tế (Isochrone Search) từ 5 đến 30 phút theo các phương tiện giao thông phổ biến.
2. **Hỗ trợ tối đa cho lực lượng môi giới (Agent AI Co-Pilot)**:
   - Tự động sinh tiêu đề chuẩn SEO và mô tả tin đăng định dạng Markdown từ hình ảnh sổ đỏ hoặc thông số cơ bản.
   - Cung cấp công cụ định giá AVM Weighted K-Nearest Neighbors (KNN) hỗ trợ tư vấn giá bán sát với thực tế thị trường.
3. **Nâng cao trải nghiệm người dùng đa nền tảng**:
   - Trải nghiệm đồng nhất giữa Web (Next.js 16 App Router tối ưu SEO và tốc độ tải trang) và Mobile (Flutter phản hồi nhanh, hỗ trợ định vị).
   - Tích hợp công cụ tính toán tài chính và kế hoạch trả nợ ngân hàng trực quan.
   - Hệ thống cảnh báo tự động thông báo bất động sản mới phù hợp nhu cầu.

---

## 3. Phạm Vi Dự Án (Project Scope)

### Trong phạm vi (In-Scope)
- **Hạ tầng dữ liệu và lưu trữ**:
  - PostgreSQL 16 với pgvector (chỉ mục HNSW) và PostGIS (chỉ mục GiST SRID 4326).
  - Tầng nhớ đệm Redis 7 Cache-aside hỗ trợ TTL và cơ chế vô hiệu hóa tự động.
- **Dịch vụ cốt lõi Backend**:
  - Xác thực người dùng qua JWT và phân quyền vai trò (User, Agent, Admin).
  - Quản lý toàn diện vòng đời bài đăng bất động sản kèm mảng ảnh và tọa độ địa lý.
  - Bộ máy tìm kiếm lai RRF kết hợp pgvector Cosine Distance và FTS GIN Index tiếng Việt.
  - Trợ lý AI tương tác tự nhiên (Chat Assistant) tự động phân tích ý định và trích xuất tiêu chí.
  - Công cụ định giá AVM theo thuật toán Weighted KNN theo tọa độ và diện tích.
  - Công cụ tính khoản vay ngân hàng (Mortgage Calculator) theo dư nợ giảm dần và niên kim.
  - Quản lý cảnh báo tìm kiếm (Saved Search Alerts) và thông báo nội bộ (In-app Notifications).
  - So sánh đối chiếu 2 đến 3 bất động sản theo tiêu chí đơn giá, vị trí và tiềm năng.
- **Giao diện người dùng Web & Mobile**:
  - Web Client: Next.js 16 (React 19, TypeScript, Tailwind CSS v4, Leaflet).
  - Mobile Client: Flutter 3.x (Riverpod, Dio, FlutterMap).
  - Hợp đồng dữ liệu dùng chung (Shared SDK TypeScript DTOs).

### Ngoài phạm vi (Out-of-Scope)
- Tích hợp cổng thanh toán trực tuyến xử lý giao dịch đặt cọc hoặc ký quỹ ngân hàng (giữ ở mức mô phỏng bảng tính vay tài chính).
- Ký hợp đồng điện tử có chữ ký số pháp lý (chỉ hỗ trợ liên hệ môi giới trực tiếp).
- Hệ thống tổng đài cuộc gọi thoại tự động VoIP (sử dụng chuyển hướng số điện thoại người đăng).

---

## 4. Chân Dung Người Dùng Mục Tiêu (Target User Personas)

### 4.1. Người Tìm Nhà / Khách Thuê (Home Seeker / Renter)
- **Đặc điểm**: Cá nhân hoặc gia đình có nhu cầu mua hoặc thuê nhà ở tại các đô thị lớn (Hà Nội, TP.HCM, Đà Nẵng).
- **Mục tiêu**:
  - Tìm kiếm nhanh căn nhà phù hợp với yêu cầu thực tế mà không cần lọc thủ công hàng chục tiêu chí cứng.
  - Biết rõ thời gian di chuyển từ nhà tới nơi làm việc hoặc trường học của con.
  - Nắm được bài toán tài chính, số tiền trả góp hàng tháng khi vay ngân hàng.
- **Hành vi trên hệ thống**:
  - Sử dụng khung tìm kiếm tự nhiên hoặc chat với Trợ lý AI.
  - Sử dụng bản đồ Isochrone để khoanh vùng bán kính di chuyển.
  - Lưu các căn nhà ưng ý vào danh sách yêu thích và sử dụng tính năng so sánh đa tiêu chí.
  - Đăng ký nhận cảnh báo khi có tin đăng mới phù hợp tầm giá.

### 4.2. Môi Giới Bất Động Sản (Real Estate Agent)
- **Đặc điểm**: Chuyên viên môi giới độc lập hoặc thuộc các sàn phân phối bất động sản.
- **Mục tiêu**:
  - Đăng tin nhanh chóng, nội dung chuyên nghiệp, thu hút người xem.
  - Định giá chính xác sản phẩm để tư vấn cho chủ nhà, tránh bị tồn kho tin đăng.
  - Tiếp cận đúng đối tượng khách hàng tiềm năng.
- **Hành vi trên hệ thống**:
  - Sử dụng công cụ AI Listing Generator để tạo bài viết chuẩn SEO từ thông số hoặc ảnh chụp sổ đỏ.
  - Sử dụng công cụ AVM Price Advisor để tham khảo khoảng giá đề xuất của các bất động sản tương đồng xung quanh trước khi công bố giá bán.
  - Quản lý danh mục các bài đăng của mình thông qua màn hình My Properties.

### 4.3. Quản Trị Viên Hệ Thống (Administrator)
- **Đặc điểm**: Đội ngũ vận hành hệ thống kỹ thuật của Space247.
- **Mục tiêu**:
  - Giám sát tình trạng hoạt động của các dịch vụ, kết nối cơ sở dữ liệu và chỉ mục vector.
  - Kiểm duyệt nội dung bài đăng, quản lý tài khoản người dùng và môi giới.
  - Theo dõi hiệu năng hệ thống bộ nhớ đệm và thời gian phản hồi của các truy vấn tìm kiếm.
- **Hành vi trên hệ thống**:
  - Kiểm tra trạng thái hệ thống qua endpoint `/api/v1/health`.
  - Quản trị dữ liệu người dùng và danh mục tin đăng.

---

## 5. Trung Tâm Tài Liệu Kỹ Thuật (Technical Documentation Hub)

Hệ thống tài liệu kỹ thuật chuẩn Enterprise của Space247 được phân bổ chi tiết trong thư mục `docs/`:

| Tệp tài liệu | Nội dung chuyên môn chính |
|---|---|
| [`docs/project-overview.md`](file:///Users/hautp/Documents/project/Space247/docs/project-overview.md) | Bối cảnh thị trường PropTech, mục tiêu dự án, phạm vi và chân dung người dùng |
| [`docs/system-architecture.md`](file:///Users/hautp/Documents/project/Space247/docs/system-architecture.md) | Kiến trúc phân tầng, luồng dữ liệu Shared SDK, chiến lược Cache-aside và Hybrid Search RRF |
| [`docs/tech-stack.md`](file:///Users/hautp/Documents/project/Space247/docs/tech-stack.md) | Bảng phiên bản công nghệ chính xác và các biên bản quyết định kiến trúc (ADRs) |
| [`docs/database-design.md`](file:///Users/hautp/Documents/project/Space247/docs/database-design.md) | Sơ đồ thực thể ERD, chi tiết 5 bảng, kiểu `VECTOR(768)`, `geometry(Point)` và chỉ mục HNSW/GiST/GIN |
| [`docs/api-specs.md`](file:///Users/hautp/Documents/project/Space247/docs/api-specs.md) | Đặc tả chi tiết toàn bộ RESTful API theo 9 module nghiệp vụ kèm DTO request/response |
| [`docs/coding-standards-and-git-rules.md`](file:///Users/hautp/Documents/project/Space247/docs/coding-standards-and-git-rules.md) | Quy chuẩn Conventional Commits, Git Flow, an toàn bảo mật và cổng kiểm chuẩn Quality Gate |
| [`docs/performance-sla.md`](file:///Users/hautp/Documents/project/Space247/docs/performance-sla.md) | Cam kết SLA độ trễ P95/P99, giám sát thời gian xử lý, tỷ lệ Cache Hit và kiểm thử tải k6 |
| [`docs/runbook.md`](file:///Users/hautp/Documents/project/Space247/docs/runbook.md) | Cẩm nang xử lý sự cố Deadlock, lỗi container, REINDEX CONCURRENTLY, suy giảm Redis và tái sinh vector |
| [`docs/security-privacy.md`](file:///Users/hautp/Documents/project/Space247/docs/security-privacy.md) | Quản lý định danh Bcrypt cost 12, JWT 24h, RBAC, che số điện thoại, Rate Limiting và Nghị định 13/2023/NĐ-CP |

