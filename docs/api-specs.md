# Đặc Tả Kỹ Thuật API RESTful Space247 (API Specifications)

Tất cả các endpoint của hệ thống Space247 đều tuân thủ kiến trúc RESTful, dữ liệu trao đổi dưới định dạng JSON với mã hóa UTF-8, và có tiền tố `/api/v1`.

---

## 1. Cơ Chế Xác Thực & Phân Quyền (Authentication & RBAC)

Hệ thống sử dụng cơ chế xác thực dựa trên JSON Web Token (JWT Bearer Token):
- **Header gửi kèm**: `Authorization: Bearer <access_token>`
- **Thuật toán ký**: HS256 với khóa bí mật cấu hình qua `SECRET_KEY`.
- **Thời hạn hiệu lực**: Mặc định 7 ngày (`ACCESS_TOKEN_EXPIRE_MINUTES=10080`).
- **Phân quyền vai trò (Role-Based Access Control)**:
  - `user`: Khách hàng tìm nhà, thuê nhà hoặc nhà đầu tư cá nhân.
  - `agent`: Môi giới bất động sản, được cấp quyền đăng tin, sửa tin và sử dụng bộ công cụ AI Co-Pilot.
  - `admin`: Quản trị viên nghiệp vụ hệ thống.
  - `superadmin`: Quản trị viên tối cao hệ thống, quản lý tài khoản người dùng, cấp phát vai trò và kiểm soát phân quyền RBAC toàn diện.

---

## 2. Danh Mục Endpoints Chi Tiết Theo Module

### 2.1. Module Xác Thực & Người Dùng (`/auth`)

#### 1. Đăng ký tài khoản
- **Endpoint**: `POST /api/v1/auth/register`
- **Xác thực**: Không yêu cầu
- **Request Body (`UserRegisterRequest`)**:
  ```json
  {
    "email": "agent@space247.vn",
    "password": "Password123@",
    "full_name": "Nguyễn Văn A",
    "phone": "0912345678",
    "role": "agent"
  }
  ```
- **Response (`TokenResponse` - HTTP 201)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "c1f7a08b-7032-4d29-a78b-0c6778f658ba",
      "email": "agent@space247.vn",
      "full_name": "Nguyễn Văn A",
      "phone": "0912345678",
      "avatar_url": null,
      "role": "agent",
      "is_active": true
    }
  }
  ```

#### 2. Đăng nhập
- **Endpoint**: `POST /api/v1/auth/login`
- **Xác thực**: Không yêu cầu
- **Request Body (`UserLoginRequest`)**:
  ```json
  {
    "email": "agent@space247.vn",
    "password": "Password123@"
  }
  ```
- **Response (`TokenResponse` - HTTP 200)**: Tương tự cấu trúc token của đăng ký.

#### 3. Lấy thông tin tài khoản hiện tại
- **Endpoint**: `GET /api/v1/auth/me`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`UserResponse` - HTTP 200)**: Thông tin chi tiết người dùng.

#### 4. Cập nhật hồ sơ cá nhân
- **Endpoint**: `PUT /api/v1/auth/me`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Request Body (`UserUpdateRequest`)**:
  ```json
  {
    "full_name": "Nguyễn Văn A (Cập nhật)",
    "phone": "0988776655",
    "avatar_url": "https://space247.vn/avatars/agent_a.jpg"
  }
  ```
- **Response (`UserResponse` - HTTP 200)**: Dữ liệu hồ sơ sau khi cập nhật.

---

### 2.2. Module Hồ Sơ Người Dùng Cá Nhân (`/users`)

#### 1. Lấy thông tin hồ sơ chi tiết kèm số liệu tương tác
- **Endpoint**: `GET /api/v1/users/me`
- **Xác thực**: Bắt buộc (`user`, `agent`, `admin`, `superadmin`)
- **Response (`UserProfileDetailResponse` - HTTP 200)**:
  ```json
  {
    "id": "c1f7a08b-7032-4d29-a78b-0c6778f658ba",
    "email": "user@space247.vn",
    "full_name": "Nguyễn Văn A",
    "phone": "0912345678",
    "phone_verified": true,
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "user",
    "is_active": true,
    "last_login_at": "2026-09-05T09:30:00Z",
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-09-05T09:30:00Z",
    "total_properties": 0,
    "total_favorites": 12,
    "total_alerts": 3
  }
  ```

#### 2. Cập nhật thông tin định danh cá nhân
- **Endpoint**: `PUT /api/v1/users/me`
- **Xác thực**: Bắt buộc
- **Request Body (`UserProfileUpdateRequest`)**:
  ```json
  {
    "full_name": "Nguyễn Văn A (Cập nhật)",
    "phone": "0912345678",
    "avatar_url": "https://example.com/avatar.jpg"
  }
  ```
- **Response (`UserResponse` - HTTP 200)**: Dữ liệu hồ sơ sau khi cập nhật.

#### 3. Đổi mật khẩu tài khoản
- **Endpoint**: `POST /api/v1/users/me/change-password`
- **Xác thực**: Bắt buộc
- **Request Body (`ChangePasswordRequest`)**:
  ```json
  {
    "old_password": "OldPassword123@",
    "new_password": "NewSecurePassword456@"
  }
  ```
- **Validation Rules**: Mật khẩu cũ phải trùng khớp với hash trong DB; mật khẩu mới phải tối thiểu 8 ký tự.
- **Response (HTTP 200)**:
  ```json
  {
    "message": "Đổi mật khẩu thành công."
  }
  ```

---

### 2.3. Module Quản Trị Người Dùng & Phân Quyền RBAC (`/admin/users`)

Toàn bộ các endpoint trong module này yêu cầu quyền **`superadmin`** (xác thực qua dependency `get_current_superadmin_user`). Mọi vai trò khác sẽ nhận phản hồi HTTP 403 Forbidden.

#### 1. Tra cứu và phân trang danh sách người dùng
- **Endpoint**: `GET /api/v1/admin/users`
- **Xác thực**: Bắt buộc (`superadmin`)
- **Query Parameters**:
  - `q` (string, optional): Tìm kiếm theo email hoặc họ tên người dùng.
  - `role` (string, optional): Lọc theo vai trò (`superadmin`, `admin`, `agent`, `user`).
  - `is_active` (boolean, optional): Lọc theo trạng thái hoạt động (`true`, `false`).
  - `page` (int, default 1): Số thứ tự trang.
  - `page_size` (int, default 20, max 100): Kích thước trang.
- **Response (`UserPaginationResponse` - HTTP 200)**:
  ```json
  {
    "items": [
      {
        "id": "c1f7a08b-7032-4d29-a78b-0c6778f658ba",
        "email": "agent@space247.vn",
        "full_name": "Môi Giới Chuyên Nghiệp",
        "phone": "0988889999",
        "phone_verified": true,
        "avatar_url": null,
        "role": "agent",
        "is_active": true,
        "last_login_at": "2026-09-05T09:15:00Z",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-05T09:15:00Z"
      }
    ],
    "total": 4,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```

#### 2. Tạo tài khoản người dùng mới (chỉ định vai trò)
- **Endpoint**: `POST /api/v1/admin/users`
- **Xác thực**: Bắt buộc (`superadmin`)
- **Request Body (`UserCreateByAdminRequest`)**:
  ```json
  {
    "email": "agent.vip@space247.vn",
    "password": "InitialPassword123@",
    "full_name": "Môi Giới VIP Space247",
    "phone": "0933334444",
    "role": "agent",
    "is_active": true,
    "phone_verified": true
  }
  ```
- **Response (`UserResponse` - HTTP 201)**: Chi tiết người dùng mới được tạo.

#### 3. Xem chi tiết người dùng và số liệu hoạt động
- **Endpoint**: `GET /api/v1/admin/users/{user_id}`
- **Xác thực**: Bắt buộc (`superadmin`)
- **Response (`UserAdminDetailResponse` - HTTP 200)**: Chi tiết tài khoản kèm tổng số tin đăng, yêu thích và cảnh báo tìm kiếm.

#### 4. Cập nhật thông tin, đổi vai trò hoặc đặt lại mật khẩu người dùng
- **Endpoint**: `PUT /api/v1/admin/users/{user_id}`
- **Xác thực**: Bắt buộc (`superadmin`)
- **Request Body (`UserUpdateByAdminRequest`)**:
  ```json
  {
    "full_name": "Tên Người Dùng Cập Nhật",
    "phone": "0911223344",
    "role": "admin",
    "is_active": true,
    "phone_verified": true,
    "reset_password": "NewSecretPassword123@"
  }
  ```
- **Cơ chế an toàn**: Superadmin không thể tự giáng quyền hoặc tự vô hiệu hóa chính mình.
- **Response (`UserResponse` - HTTP 200)**: Hồ sơ sau khi cập nhật.

#### 5. Vô hiệu hóa tài khoản (Soft Delete)
- **Endpoint**: `DELETE /api/v1/admin/users/{user_id}`
- **Xác thực**: Bắt buộc (`superadmin`)
- **Cơ chế**: Thiết lập cờ `is_active = False` mà không xóa vật lý bản ghi để bảo toàn toàn vẹn dữ liệu quan hệ bài đăng và cảnh báo.
- **Response (HTTP 200)**:
  ```json
  {
    "message": "Đã vô hiệu hóa tài khoản người dùng thành công."
  }
  ```

---


### 2.4. Module Bất Động Sản (`/properties`)

#### 1. Lấy danh sách bất động sản (kèm phân trang và lọc)
- **Endpoint**: `GET /api/v1/properties`
- **Xác thực**: Không yêu cầu
- **Query Parameters**:
  - `page` (int, default 1): Trang hiện tại.
  - `page_size` (int, default 12, max 100): Số lượng bản ghi trên một trang.
  - `city` (string, optional): Lọc theo tỉnh/thành phố.
  - `district` (string, optional): Lọc theo quận/huyện.
  - `property_type` (string, optional): `apartment`, `house`, `villa`, `land`, `commercial`.
  - `listing_type` (string, optional): `sale`, `rent`.
  - `min_price` / `max_price` (float, optional): Khoảng giá (VNĐ).
  - `min_area_sqm` / `max_area_sqm` (float, optional): Khoảng diện tích (m²).
  - `sort_by` (string, default `created_at`): `created_at`, `price_asc`, `price_desc`, `area_asc`, `area_desc`.
- **Response (`PaginatedPropertyResponse` - HTTP 200)**:
  ```json
  {
    "items": [
      {
        "id": "e4b10b06-4078-43ec-a4ee-eb8b22a012ab",
        "title": "Căn hộ cao cấp 3PN Vinhomes Metropolis Liễu Giai",
        "description": "Căn góc tầng trung, ban công Đông Nam view trọn hồ Tây...",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 8500000000.0,
        "currency": "VND",
        "area_sqm": 115.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "29 Liễu Giai",
        "ward": "Ngọc Khánh",
        "district": "Ba Đình",
        "city": "Hà Nội",
        "latitude": 21.0326,
        "longitude": 105.8152,
        "images": [
          "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80"
        ],
        "status": "active",
        "agent": {
          "id": "c1f7a08b-7032-4d29-a78b-0c6778f658ba",
          "full_name": "Nguyễn Văn A",
          "email": "agent@space247.vn",
          "phone": "0912345678",
          "avatar_url": null,
          "role": "agent"
        },
        "created_at": "2026-09-01T10:00:00Z"
      }
    ],
    "total": 28,
    "page": 1,
    "page_size": 12,
    "total_pages": 3
  }
  ```

#### 2. Đăng tin bất động sản mới
- **Endpoint**: `POST /api/v1/properties`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Request Body (`PropertyCreateRequest`)**:
  ```json
  {
    "title": "Nhà phố thương mại Shophouse Cầu Giấy 120m2",
    "description": "Mặt tiền 6m thuận tiện kinh doanh hoặc cho thuê văn phòng đại diện",
    "property_type": "house",
    "listing_type": "sale",
    "price": 28000000000.0,
    "area_sqm": 120.0,
    "num_bedrooms": 5,
    "num_bathrooms": 5,
    "address": "Số 45 Trần Thái Tông",
    "ward": "Dịch Vọng",
    "district": "Cầu Giấy",
    "city": "Hà Nội",
    "latitude": 21.0315,
    "longitude": 105.7874,
    "images": [
      "https://example.com/shophouse1.jpg",
      "https://example.com/shophouse2.jpg"
    ]
  }
  ```
- **Xử lý ngầm**: Hệ thống tự động sinh vector embedding 768 chiều từ nội dung bài đăng, thiết lập điểm hình học PostGIS `geom`, và xóa bộ nhớ đệm tìm kiếm.
- **Response (`PropertyResponse` - HTTP 201)**: Chi tiết bất động sản vừa tạo.

#### 3. Lấy chi tiết một bất động sản
- **Endpoint**: `GET /api/v1/properties/{id}`
- **Xác thực**: Không yêu cầu
- **Response (`PropertyDetailResponse` - HTTP 200)**: Trả về đầy đủ thông số BĐS kèm mảng ảnh và thông tin thẻ môi giới đăng tin.

#### 4. Cập nhật tin bất động sản
- **Endpoint**: `PUT /api/v1/properties/{id}`
- **Xác thực**: Bắt buộc (Chủ sở hữu hoặc Admin)
- **Request Body (`PropertyUpdateRequest`)**: Cập nhật các trường thông tin thay đổi.

#### 5. Danh sách tin đăng của người dùng hiện tại
- **Endpoint**: `GET /api/v1/properties/my`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`list[PropertyResponse]` - HTTP 200)**.

#### 6. Đánh dấu hoặc hủy đánh dấu yêu thích
- **Endpoint**: `POST /api/v1/properties/{id}/favorite`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`ToggleFavoriteResponse` - HTTP 200)**:
  ```json
  {
    "property_id": "e4b10b06-4078-43ec-a4ee-eb8b22a012ab",
    "is_favorite": true,
    "message": "Property added to favorites"
  }
  ```

#### 7. Danh sách bất động sản yêu thích của tôi
- **Endpoint**: `GET /api/v1/properties/favorites`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`list[PropertyResponse]` - HTTP 200)**.

#### 8. So sánh đa chiều 2-3 bất động sản qua AI
- **Endpoint**: `POST /api/v1/properties/compare`
- **Xác thực**: Không yêu cầu
- **Request Body (`ComparePropertiesRequest`)**:
  ```json
  {
    "property_ids": [
      "e4b10b06-4078-43ec-a4ee-eb8b22a012ab",
      "86e680a9-25f0-46eb-aeb9-923f7c1d7bb6"
    ]
  }
  ```
- **Response (`ComparePropertiesResponse` - HTTP 200)**:
  ```json
  {
    "properties": [
      {
        "property_id": "e4b10b06-4078-43ec-a4ee-eb8b22a012ab",
        "title": "Căn hộ Vinhomes Metropolis 115m2",
        "price": 8500000000.0,
        "area_sqm": 115.0,
        "price_per_sqm": 73913043.48
      },
      {
        "property_id": "86e680a9-25f0-46eb-aeb9-923f7c1d7bb6",
        "title": "Căn hộ Golden Park Cầu Giấy 98m2",
        "price": 5200000000.0,
        "area_sqm": 98.0,
        "price_per_sqm": 53061224.49
      }
    ],
    "analysis_markdown": "### Báo Cáo So Sánh Chi Tiết\n\n1. **Về Đơn Giá / m²**: Căn hộ Golden Park có đơn giá cạnh tranh hơn..."
  }
  ```

---

### 2.5. Module Dự Án Bất Động Sản (`/projects`)

#### 1. Lấy danh sách dự án với bộ lọc và phân trang
- **Endpoint**: `GET /api/v1/projects`
- **Xác thực**: Không yêu cầu
- **Query Parameters**:
  - `skip`: Offset phân trang (mặc định 0).
  - `limit`: Số lượng dự án mỗi trang (mặc định 20, tối đa 100).
  - `city`: Lọc theo tỉnh/thành phố (ví dụ: "Hồ Chí Minh", "Hà Nội").
  - `district`: Lọc theo quận/huyện.
  - `status`: Lọc theo trạng thái xây dựng (`upcoming`, `under_construction`, `handing_over`, `completed`).
  - `developer`: Lọc theo tên chủ đầu tư.
  - `min_price`: Lọc dự án có mức giá trần >= `min_price`.
  - `max_price`: Lọc dự án có mức giá sàn <= `max_price`.
  - `q`: Từ khóa tìm kiếm theo tên dự án hoặc chủ đầu tư.
- **Bộ nhớ đệm (Cache)**: Tự động đệm Redis theo khóa truy vấn `cache:project_list:{hash}` với thời gian sống TTL 30 phút (1.800 giây).
- **Response (`PaginatedProjectResponse` - HTTP 200)**:
  ```json
  {
    "items": [
      {
        "id": "77777777-7777-7777-7777-777777777777",
        "name": "Vinhomes Grand Park",
        "slug": "vinhomes-grand-park",
        "developer": "Vingroup",
        "description": "Đại đô thị thông minh đẳng cấp quốc tế phía Đông TP.HCM...",
        "status": "under_construction",
        "total_units": 44000,
        "launch_year": 2019,
        "handover_year": 2024,
        "address": "Nguyễn Xiển, Long Thạnh Mỹ",
        "ward": "Long Thạnh Mỹ",
        "district": "Quận 9",
        "city": "Hồ Chí Minh",
        "latitude": 10.845,
        "longitude": 106.838,
        "images": [
          "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00"
        ],
        "master_plan_url": "https://images.unsplash.com/photo-masterplan",
        "legal_status": "Sổ hồng lâu dài",
        "price_range_min": 1500000000.0,
        "price_range_max": 8000000000.0,
        "amenities": [
          "Hồ bơi",
          "Công viên 36ha",
          "TTTM Vincom Mega Mall"
        ],
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-01T08:00:00Z",
        "active_properties_count": 28,
        "for_sale_count": 20,
        "for_rent_count": 8,
        "average_price_per_sqm": 48500000.0
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20,
    "pages": 1
  }
  ```

#### 2. Tạo dự án mới
- **Endpoint**: `POST /api/v1/projects`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Request Body (`ProjectCreate`)**: Các trường thông tin dự án. Trường `slug` có thể bỏ qua để hệ thống tự động sinh slug tiếng Việt chuẩn SEO.
- **Xử lý ngầm**: Tự động sinh vector nhúng 768 chiều từ tên, chủ đầu tư, địa chỉ và tiện ích thông qua FastEmbed; tạo điểm hình học PostGIS `geom` khi có tọa độ; xóa đệm danh sách dự án.
- **Response (`ProjectResponse` - HTTP 201)**: Chi tiết dự án vừa khởi tạo.

#### 3. Lấy chi tiết dự án theo ID hoặc Slug
- **Endpoint**: `GET /api/v1/projects/{id_or_slug}`
- **Xác thực**: Không yêu cầu
- **Mô tả**: Hỗ trợ tra cứu linh hoạt bằng chuỗi UUID hoặc đường dẫn thân thiện URL `slug` (ví dụ: `/projects/vinhomes-grand-park`).
- **Bộ nhớ đệm (Cache)**: Tự động lưu Redis theo khóa `cache:project:{id_or_slug}` với TTL 1.800 giây.
- **Response (`ProjectDetailResponse` - HTTP 200)**: Toàn bộ thông tin dự án cùng số liệu thống kê tin đăng thực tế và đơn giá m² bình quân.

#### 4. Cập nhật thông tin dự án
- **Endpoint**: `PUT /api/v1/projects/{project_id}`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Xử lý ngầm**: Tái tạo vector ngữ nghĩa nếu thay đổi các trường nội dung cốt lõi; xóa triệt để bộ nhớ đệm chi tiết dự án cũ/mới và bộ nhớ đệm danh sách dự án.
- **Response (`ProjectResponse` - HTTP 200)**.

#### 5. Lấy danh sách căn hộ thuộc dự án
- **Endpoint**: `GET /api/v1/projects/{id_or_slug}/properties`
- **Xác thực**: Không yêu cầu
- **Query Parameters**: `skip`, `limit`, `listing_type` (`sale` | `rent`), `property_type`, `min_price`, `max_price`, `num_bedrooms`.
- **Response (`list[PropertyResponse]` - HTTP 200)**: Danh sách các tin đăng đang hoạt động (`active`) thuộc về dự án chỉ định.

---

### 2.4. Module Tìm Kiếm Lai & Ngữ Nghĩa (`/properties/search` & `/search`)

#### 1. Tìm kiếm lai kết hợp Reciprocal Rank Fusion (RRF)
- **Endpoint**: `POST /api/v1/properties/search`
- **Xác thực**: Không yêu cầu
- **Request Body (`PropertySearchQuery`)**:
  ```json
  {
    "query": "căn hộ 3 phòng ngủ gần đại sứ quán Nhật view hồ",
    "listing_type": "sale",
    "city": "Hà Nội",
    "min_price": 5000000000.0,
    "max_price": 10000000000.0,
    "limit": 10,
    "enable_hybrid": true,
    "rrf_k": 60
  }
  ```
- **Response (`PropertySearchResponse` - HTTP 200)**:
  ```json
  {
    "total": 3,
    "vector_dim": 768,
    "query": "căn hộ 3 phòng ngủ gần đại sứ quán Nhật view hồ",
    "results": [
      {
        "property": { "id": "...", "title": "..." },
### 2.6. Module Tìm Kiếm Lai & Ngữ Nghĩa (`/properties/search` & `/search`)

#### 1. Tìm kiếm lai kết hợp (Hybrid Search RRF)
- **Endpoint**: `GET /api/v1/properties/search`
- **Xác thực**: Không yêu cầu
- **Query Parameters**:
  - `q` (string, required): Câu truy vấn tìm kiếm bằng ngôn ngữ tự nhiên.
  - `limit` (int, default 10): Số lượng kết quả trả về.
  - `vector_weight` (float, default 0.6): Trọng số điểm cosine tương đồng ngữ nghĩa.
  - `text_weight` (float, default 0.4): Trọng số điểm toàn văn (Full-Text Search).
- **Response (`PropertySearchResponse` - HTTP 200)**: Danh sách kết quả được xếp hạng theo thuật toán Reciprocal Rank Fusion (RRF).

#### 2. Tìm kiếm thuần vector ngữ nghĩa
- **Endpoint**: `POST /api/v1/search/semantic`
- **Xác thực**: Không yêu cầu
- **Request Body (`SemanticSearchQuery`)**:
  ```json
  {
    "query": "căn hộ ban công hướng đông nam gần công viên thoáng mát",
    "top_k": 5
  }
  ```
- **Response (`SemanticSearchResponse` - HTTP 200)**: Danh sách kết quả xếp hạng theo khoảng cách cosine.

---

### 2.7. Module Trợ Lý Trí Tuệ Nhân Tạo (`/chat`)

#### 1. Tương tác đa vòng với trợ lý AI Co-Pilot
- **Endpoint**: `POST /api/v1/chat/assistant`
- **Xác thực**: Không yêu cầu (Hỗ trợ định danh tùy chọn qua Bearer Token)
- **Request Body (`ChatAssistantRequest`)**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "Tôi muốn tìm căn hộ 3 phòng ngủ ở Cầu Giấy tầm tài chính dưới 6 tỷ"
      }
    ]
  }
  ```
- **Response (`ChatAssistantResponse` - HTTP 200)**:
  ```json
  {
    "message": {
      "role": "assistant",
      "content": "Dạ, em đã tìm thấy một số căn hộ 3 phòng ngủ tại khu vực Cầu Giấy trong ngân sách của anh/chị..."
    },
    "extracted_criteria": {
      "listing_type": "sale",
      "property_type": "apartment",
      "district": "Cầu Giấy",
      "city": "Hà Nội",
      "max_price": 6000000000.0,
      "min_bedrooms": 3
    },
    "suggested_properties": []
  }
  ```

---

### 2.8. Module Tiện Ích Môi Giới AI Co-Pilot (`/agent`)

#### 1. Tạo bài viết tin đăng chuẩn SEO từ thông số kỹ thuật
- **Endpoint**: `POST /api/v1/agent/generate-listing`
- **Xác thực**: Bắt buộc (`agent` hoặc `admin`)
- **Request Body (`GenerateListingRequest`)**:
  ```json
  {
    "property_type": "apartment",
    "listing_type": "sale",
    "address": "29 Liễu Giai, Ba Đình, Hà Nội",
    "area_sqm": 115.0,
    "num_bedrooms": 3,
    "num_bathrooms": 2,
    "highlights": ["View hồ Tây", "Nội thất nhập khẩu Ý", "Cửa khóa vân tay cao cấp"],
    "target_audience": "Gia đình thượng lưu, chuyên gia nước ngoài"
  }
  ```
- **Response (`GenerateListingResponse` - HTTP 200)**:
  ```json
  {
    "title": "Bán Căn Hộ Cao Cấp 3PN Vinhomes Metropolis Liễu Giai - View Trọn Hồ Tây",
    "description_markdown": "### Điểm Nhấn Không Gian Sống Thượng Lưu...",
    "suggested_tags": ["vinhomes-metropolis", "lieu-giai", "view-ho-tay", "can-ho-cao-cap"]
  }
  ```

#### 2. Mô hình định giá tự động AVM (Automated Valuation Model)
- **Endpoint**: `POST /api/v1/agent/valuation`
- **Xác thực**: Bắt buộc (`agent` hoặc `admin`)
- **Request Body (`ValuationRequest`)**:
  ```json
  {
    "property_type": "apartment",
    "city": "Hà Nội",
    "district": "Ba Đình",
    "ward": "Ngọc Khánh",
    "area_sqm": 115.0,
    "num_bedrooms": 3,
    "num_bathrooms": 2
  }
  ```
- **Response (`ValuationResponse` - HTTP 200)**:
  ```json
  {
    "estimated_price": 8250000000.0,
    "confidence_score": 0.88,
    "price_range_low": 7800000000.0,
    "price_range_high": 8700000000.0,
    "price_per_sqm": 71739130.43,
    "comparable_properties_count": 8,
    "methodology": "Hedonic pricing regression kết hợp khoảng cách PostGIS và tương đồng vector phân khúc"
  }
  ```

---

### 2.9. Module Địa Không Gian & Bản Đồ (`/spatial`)

#### 1. Tìm kiếm theo vùng di chuyển đẳng thời (Isochrone Search)
- **Endpoint**: `POST /api/v1/spatial/isochrone-search`
- **Xác thực**: Không yêu cầu
- **Request Body (`IsochroneSearchRequest`)**:
  ```json
  {
    "latitude": 21.0326,
    "longitude": 105.8142,
    "max_duration_minutes": 15,
    "travel_mode": "driving"
  }
  ```
- **Response (`IsochroneSearchResponse` - HTTP 200)**:
  ```json
  {
    "center": { "latitude": 21.0326, "longitude": 105.8142 },
    "max_duration_minutes": 15,
    "travel_mode": "driving",
    "properties": [],
    "total_found": 12
  }
  ```

#### 2. Bản đồ nhiệt mật độ tiện ích (Amenity Heatmap)
- **Endpoint**: `POST /api/v1/spatial/amenity-heatmap`
- **Xác thực**: Không yêu cầu
- **Request Body (`AmenityHeatmapQuery`)**:
  ```json
  {
    "city": "Hà Nội",
    "district": "Ba Đình",
    "amenity_types": ["school", "hospital", "supermarket", "park"]
  }
  ```
- **Response (`AmenityHeatmapResponse` - HTTP 200)**: Tập hợp các điểm nhiệt kèm trọng số mật độ phục vụ hiển thị lớp phủ Leaflet/MapLibre.

---

### 2.10. Module Công Cụ Tài Chính (`/financial`)

#### 1. Tính toán lịch trả góp vay mua nhà (Mortgage Calculator)
- **Endpoint**: `POST /api/v1/financial/mortgage-calc`
- **Xác thực**: Không yêu cầu
- **Request Body (`MortgageCalcRequest`)**:
  ```json
  {
    "property_price": 5000000000.0,
    "down_payment_percent": 30.0,
    "loan_term_years": 20,
    "interest_rate_percent": 8.5,
    "amortization_type": "reducing_balance"
  }
  ```
- **Response (`MortgageCalcResponse` - HTTP 200)**:
  ```json
  {
    "loan_amount": 3500000000.0,
    "down_payment": 1500000000.0,
    "monthly_payment": 30373500.0,
    "total_payment": 7289640000.0,
    "total_interest": 3789640000.0,
    "amortization_schedule": []
  }
  ```

---

### 2.11. Module Cảnh Báo & Thông Báo (`/alerts` & `/notifications`)

#### 1. Tạo cảnh báo tìm kiếm mới (Saved Search Alert)
- **Endpoint**: `POST /api/v1/alerts`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Request Body (`CreateAlertRequest`)**:
  ```json
  {
    "title": "Chung cư Cầu Giấy dưới 5 tỷ",
    "criteria": {
      "city": "Hà Nội",
      "district": "Cầu Giấy",
      "property_type": "apartment",
      "max_price": 5000000000.0
    },
    "frequency": "instant"
  }
  ```
- **Response (`SavedSearchAlert` - HTTP 201)**

#### 2. Lấy danh sách cảnh báo của tôi
- **Endpoint**: `GET /api/v1/alerts/my`
- **Xác thực**: Bắt buộc (Bearer Token)

#### 3. Xóa cảnh báo tìm kiếm
- **Endpoint**: `DELETE /api/v1/alerts/{alert_id}`
- **Xác thực**: Bắt buộc (Bearer Token)

#### 4. Lấy danh sách thông báo người dùng
- **Endpoint**: `GET /api/v1/notifications`
- **Xác thực**: Bắt buộc (Bearer Token)

#### 5. Đánh dấu tất cả thông báo đã đọc
- **Endpoint**: `PUT /api/v1/notifications/read-all`
- **Xác thực**: Bắt buộc (Bearer Token)

---

### 2.12. Module Giám Sát Hệ Thống (`/health`)

#### 1. Kiểm tra trạng thái sức khỏe dịch vụ
- **Endpoint**: `GET /api/v1/health`
- **Xác thực**: Không yêu cầu
- **Response (`HealthResponse` - HTTP 200)**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "database": {
      "status": "connected",
      "postgis_enabled": true,
      "pgvector_enabled": true
    },
    "redis": {
      "status": "connected"
    }
  }
  ```
