# Chính Sách Bảo Mật & Quyền Riêng Tư Dữ Liệu (Security & Data Privacy)

Tài liệu này xác lập các tiêu chuẩn kỹ thuật về xác thực, phân quyền, bảo vệ dữ liệu cá nhân theo quy định pháp luật Việt Nam (Nghị định 13/2023/NĐ-CP) và các biện pháp kỹ thuật chống thu thập dữ liệu trái phép (Anti-Scraping) trên nền tảng Space247.

---

## 1. Quản Lý Định Danh & Phiên Đăng Nhập (Identity & Session Management)

### 1.1. Cơ Chế Lưu Trữ Mật Khẩu (Password Hashing)
- **Thuật toán**: `bcrypt` (thông qua thư viện `passlib`).
- **Hệ số chi phí tính toán (Work Factor / Cost Factor)**: Cấu hình mặc định là **12**.
  - Hệ số 12 bảo đảm thời gian băm xấp xỉ 250–350 ms trên mỗi lần xác thực, làm tê liệt hoàn toàn các hình thức tấn công vét cạn (Brute-force) hoặc tấn công bảng cầu vồng (Rainbow Table).
- **Quy tắc mật khẩu tối thiểu**:
  - Độ dài tối thiểu 8 ký tự.
  - Bắt buộc chứa ít nhất 1 chữ cái in hoa, 1 chữ số và 1 ký tự đặc biệt.

### 1.2. Cơ Chế Token Xác Thực (JWT Architecture)
Hệ thống sử dụng mô hình mã thông báo không trạng thái (Stateless JSON Web Tokens):
- **Access Token**:
  - Thuật toán ký: HMAC SHA-256 (`HS256`).
  - Thời hạn hiệu lực: Tối đa 24 giờ đối với phiên đăng nhập thông thường trên môi trường sản xuất.
  - Nội dung Payload chuẩn:
    ```json
    {
      "sub": "c1f7a08b-7032-4d29-a78b-0c6778f658ba",
      "role": "agent",
      "email": "agent@space247.vn",
      "exp": 1788595200,
      "iat": 1788508800
    }
    ```
- **Phân tách Refresh Token**:
  - Được lưu trữ dưới dạng Cookie bảo mật có cờ `HttpOnly`, `Secure` và `SameSite=Strict`.
  - Được sử dụng để cấp mới Access Token mà không yêu cầu người dùng nhập lại thông tin mật khẩu.

### 1.3. Mô Hình Phân Quyền Vai Trò (Role-Based Access Control - RBAC)
Phân quyền được thực thi ở tầng middleware và dependency injection của FastAPI (`get_current_user`, `require_role`):

| Vai trò | Phạm vi quyền hạn chi tiết |
|---|---|
| **`user`** | Tra cứu bất động sản, sử dụng bản đồ và công cụ tài chính, lưu danh sách yêu thích, quản lý hồ sơ cá nhân và đổi mật khẩu (`/profile`), đăng ký cảnh báo tìm kiếm, nhận thông báo in-app. Không có quyền đăng tin hoặc gọi API AI Co-Pilot. |
| **`agent`** | Thừa hưởng toàn bộ quyền của `user`, được phép đăng tin bất động sản mới, cập nhật và quản lý danh mục tin đăng của mình (`/properties/my`), sử dụng công cụ Agent AI Co-Pilot (tạo bài viết Markdown và định giá AVM). |
| **`admin`** | Quản trị viên nghiệp vụ: Toàn quyền kiểm duyệt, chỉnh sửa hoặc quản lý bất kỳ bài đăng bất động sản hoặc dự án nào trong hệ thống, giám sát các chỉ số vận hành. |
| **`superadmin`** | Quản trị viên tối cao: Toàn quyền quản trị phân quyền RBAC (`/api/v1/admin/users`), tạo người dùng mới với mọi vai trò, thay đổi vai trò, mở/khóa tài khoản (soft delete), đặt lại mật khẩu của người dùng. Hệ thống có cơ chế bảo vệ ngăn Superadmin tự giáng quyền hoặc tự vô hiệu hóa tài khoản của chính mình. |

---

## 2. Bảo Vệ Thông Tin Cá Nhân & Chống Thu Thập Trái Phép (Anti-Scraping)

### 2.1. Chính Sách Che Số Điện Thoại Môi Giới (Phone Number Masking)
Nhằm ngăn chặn các công cụ cào dữ liệu (Bot Scrapers) thu thập số điện thoại môi giới để gửi tin nhắn rác hoặc quấy rối:
- **Trên giao diện công khai**: Số điện thoại mặc định được che một phần ở các chữ số giữa, chỉ hiển thị dạng `0912***678`.
- **Cơ chế mở số (Click-to-Reveal / Click-to-Call)**:
  - Khi người dùng bấm vào nút "Xem số điện thoại" hoặc "Gọi ngay", ứng dụng phía client gửi yêu cầu ghi nhận lượt tương tác (Lead Tracking) và yêu cầu đăng nhập đối với tài khoản chưa xác thực trước khi hiển thị đầy đủ số điện thoại.
  - Tần suất bấm mở số điện thoại được giới hạn để phát hiện hành vi cào dữ liệu tự động.

### 2.2. Giới Hạn Tần Suất Truy Cập (Rate Limiting)
Hệ thống triển khai giới hạn tốc độ truy cập dựa trên địa chỉ IP và mã người dùng thông qua bộ đệm Redis (thuật toán Token Bucket hoặc Fixed Window):

| Phân nhóm Endpoint | Ngưỡng giới hạn cho phép | Hành động khi vượt ngưỡng |
|---|---|---|
| **Xác thực (`/auth/login`, `/auth/register`)** | Tối đa 5 yêu cầu / phút trên mỗi IP | Khóa tạm thời 15 phút (HTTP 429 Too Many Requests) |
| **Danh sách BĐS (`/properties`, `/properties/search`)** | Tối đa 60 yêu cầu / phút trên mỗi IP/User | Phản hồi mã lỗi HTTP 429 |
| **AI Co-Pilot & Chatbot (`/agent/*`, `/chat/*`)** | Tối đa 15 yêu cầu / phút trên mỗi tài khoản | Phản hồi HTTP 429 kèm thông báo giới hạn lưu lượng |
| **Địa không gian (`/spatial/*`)** | Tối đa 30 yêu cầu / phút | Phản hồi HTTP 429 |

---

## 3. Tuân Thủ Quy Định Bảo Vệ Dữ Liệu Cá Nhân (Nghị Định 13/2023/NĐ-CP)

Dự án Space247 thiết lập các biện pháp kỹ thuật và vận hành nhằm tuân thủ nghiêm ngặt Nghị định số 13/2023/NĐ-CP của Chính phủ về Bảo vệ dữ liệu cá nhân:

### 3.1. Quyền Yêu Cầu Xóa Dữ Liệu (Right to Erasure / Data Deletion)
- Chủ thể dữ liệu (người dùng) có quyền yêu cầu chấm dứt tài khoản và xóa toàn bộ dữ liệu cá nhân.
- Khi người dùng gửi yêu cầu xóa tài khoản:
  1. Bản ghi trong bảng `users` được xóa hoặc đánh dấu vô hiệu hóa hoàn toàn (`is_active = False`).
  2. Toàn bộ thông tin định danh trực tiếp (`email`, `phone`, `full_name`, `avatar_url`) được ghi đè bằng chuỗi băm ngẫu nhiên hoặc ẩn danh hóa (`deleted_user_<uuid>@space247.vn`).
  3. Các bài đăng bất động sản do người dùng đăng tải sẽ được chuyển khóa ngoại `user_id` thành `NULL` (`ON DELETE SET NULL`) hoặc chuyển quyền quản trị cho hệ thống nếu tin đăng vẫn còn hiệu lực giao dịch.
  4. Các bản ghi yêu thích và cảnh báo tìm kiếm liên quan sẽ được tự động xóa bỏ hoàn toàn (`ON DELETE CASCADE`).

### 3.2. Quy Trình Ẩn Danh Hóa Nhật Ký Hệ Thống (Log Anonymization)
- **Không ghi dữ liệu nhạy cảm vào log**:
  - Nghiêm cấm ghi nhận mật khẩu thô (plaintext passwords), token JWT đầy đủ, hoặc thông tin thẻ/tài khoản ngân hàng vào bất kỳ tệp log nào (`sys.stdout`, Sentry, Datadog).
  - Địa chỉ IP người dùng trong log truy cập được băm hoặc ẩn đi byte cuối cùng (IP Masking: `192.168.1.xxx`) đối với các log phục vụ phân tích dài hạn.
- **Thời hạn lưu giữ nhật ký**:
  - Nhật ký truy cập (Access Logs) được tự động xoay vòng và lưu giữ tối đa 90 ngày phục vụ điều tra an ninh, sau đó được tự động xóa bỏ.
