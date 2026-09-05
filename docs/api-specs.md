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
  - `admin`: Quản trị viên toàn quyền hệ thống.

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

### 2.2. Module Bất Động Sản (`/properties`)

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

### 2.3. Module Tìm Kiếm Lai & Ngữ Nghĩa (`/properties/search` & `/search`)

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
        "score": 0.0328,
        "rank": 1
      }
    ]
  }
  ```

#### 2. Tìm kiếm thuần vector ngữ nghĩa
- **Endpoint**: `POST /api/v1/search/semantic`
- **Xác thực**: Không yêu cầu
- **Request Body (`PropertySearchQuery`)**: Tương tự cấu trúc tìm kiếm lai, thực thi tìm kiếm qua khoảng cách vector cosine.

---

### 2.4. Module Trợ Lý Trí Tuệ Nhân Tạo (`/chat`)

#### Tương tác với Trợ lý AI Chatbot
- **Endpoint**: `POST /api/v1/chat/assistant`
- **Xác thực**: Không yêu cầu
- **Request Body (`ChatRequest`)**:
  ```json
  {
    "message": "Tôi đang tìm căn hộ 2 phòng ngủ ở quận Cầu Giấy tầm tài chính 4.5 tỷ, có trường mầm non gần đó không?",
    "conversation_history": [
      { "role": "user", "content": "Xin chào" },
      { "role": "assistant", "content": "Dạ chào bạn, Space247 có thể hỗ trợ bạn tìm kiếm bất động sản nào ạ?" }
    ]
  }
  ```
- **Response (`ChatResponse` - HTTP 200)**:
  ```json
  {
    "response_text": "Dựa trên yêu cầu của bạn, Space247 xin giới thiệu 2 căn hộ phù hợp tại Cầu Giấy...",
    "extracted_criteria": {
      "city": "Hà Nội",
      "district": "Cầu Giấy",
      "property_type": "apartment",
      "max_price": 4500000000.0,
      "num_bedrooms": 2
    },
    "suggested_properties": [
      { "id": "...", "title": "Căn hộ Golden Park Cầu Giấy...", "price": 4300000000.0 }
    ],
    "financial_advice": "Với căn hộ 4.3 tỷ, nếu vay ngân hàng 70% (3 tỷ) trong 20 năm, số tiền trả tháng đầu khoảng 28.5 triệu VNĐ."
  }
  ```

---

### 2.5. Module Tiện Ích Môi Giới AI Co-Pilot (`/agent`)

#### 1. AI sinh tiêu đề SEO và bài mô tả tin đăng
- **Endpoint**: `POST /api/v1/agent/listing/generate`
- **Xác thực**: Bắt buộc (Vai trò `agent` hoặc `admin`)
- **Request Body (`GenerateListingRequest`)**:
  ```json
  {
    "text_prompts": [
      "Căn góc 3PN D'Capitale Trần Duy Hưng 95m2",
      "Tầng trung view hồ điều hòa thoáng mát",
      "Full nội thất gỗ tự nhiên cao cấp",
      "Sổ đỏ cất két sẵn sàng giao dịch"
    ],
    "property_type": "apartment",
    "target_audience": "Gia đình trẻ thành đạt"
  }
  ```
- **Response (`GenerateListingResponse` - HTTP 200)**:
  ```json
  {
    "title_seo": "Bán Căn Góc 3PN D'Capitale Trần Duy Hưng 95m² View Hồ Điều Hòa Đẹp Nhất Dự Án",
    "description_markdown": "### Điểm Nhấn Bất Động Sản\n\n- **Vị trí**: Nằm tại tòa tháp trung tâm...",
    "extracted_specs": {
      "area_sqm": 95.0,
      "num_bedrooms": 3,
      "num_bathrooms": 2,
      "orientation": "Đông Nam",
      "legal_status": "Sổ đỏ cất két",
      "amenities": ["Hồ bơi", "Hồ điều hòa", "Khu vui chơi trẻ em"]
    }
  }
  ```

#### 2. Mô hình định giá tự động AVM (Automated Valuation Model)
- **Endpoint**: `POST /api/v1/agent/valuation/estimate`
- **Xác thực**: Bắt buộc (Vai trò `agent` hoặc `admin`)
- **Request Body (`ValuationRequest`)**:
  ```json
  {
    "property_type": "apartment",
    "area_sqm": 85.0,
    "num_bedrooms": 2,
    "num_bathrooms": 2,
    "latitude": 21.0169,
    "longitude": 105.7839,
    "radius_km": 2.5,
    "user_proposed_price": 5200000000.0
  }
  ```
- **Response (`ValuationResponse` - HTTP 200)**:
  ```json
  {
    "estimated_price_per_sqm": 58500000.0,
    "estimated_total_price": 4972500000.0,
    "price_range_low": 4723875000.0,
    "price_range_high": 5221125000.0,
    "confidence_score": 0.88,
    "market_trend": "up",
    "radius_used_km": 2.5,
    "comparable_properties": [ ... ],
    "deviation_percentage": 4.57,
    "pricing_advice": "Giá bạn đề xuất (5.2 tỷ) đang cao hơn 4.57% so với mức trung bình 4.97 tỷ của 5 căn tương đồng trong bán kính 2.5 km..."
  }
  ```

---

### 2.6. Module Địa Không Gian & Bản Đồ (`/spatial`)

#### 1. Tìm kiếm theo vùng di chuyển (Isochrone Search)
- **Endpoint**: `POST /api/v1/spatial/isochrone-search`
- **Xác thực**: Không yêu cầu
- **Request Body (`IsochroneSearchRequest`)**:
  ```json
  {
    "target_landmark": "Keangnam Hanoi Landmark Tower",
    "max_duration_minutes": 15,
    "transport_mode": "motorcycle",
    "property_type": "apartment",
    "max_price": 6000000000.0,
    "limit": 20
  }
  ```
- **Response (`IsochroneSearchResponse` - HTTP 200)**:
  ```json
  {
    "target_location": {
      "name": "Keangnam Hanoi Landmark Tower",
      "latitude": 21.0169,
      "longitude": 105.7839,
      "formatted_address": "Phạm Hùng, Mễ Trì, Nam Từ Liêm, Hà Nội"
    },
    "max_duration_minutes": 15,
    "transport_mode": "motorcycle",
    "isochrone_geojson": {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [ ... ] }
    },
    "total": 5,
    "properties": [
      {
        "property": { "id": "...", "title": "..." },
        "estimated_travel_minutes": 8.5,
        "distance_km": 2.8
      }
    ]
  }
  ```

#### 2. Bản đồ nhiệt mật độ tiện ích (Amenity Heatmap)
- **Endpoint**: `GET /api/v1/spatial/amenities/heatmap`
- **Xác thực**: Không yêu cầu
- **Query Parameters**:
  - `category` (string, default `all`): `school`, `hospital`, `metro`, `supermarket`, `all`.
  - `city` (string, default `Hà Nội`).
- **Response (`AmenityHeatmapResponse` - HTTP 200)**: Mảng điểm `[lat, lng, weight]` sẵn sàng dùng cho thư viện `leaflet.heat`.

---

### 2.7. Module Công Cụ Tài Chính (`/financial`)

#### Bảng tính vay mua nhà và lịch trả góp (Mortgage Calculator)
- **Endpoint**: `POST /api/v1/financial/mortgage-calc`
- **Xác thực**: Không yêu cầu
- **Request Body (`MortgageCalcRequest`)**:
  ```json
  {
    "property_price": 5000000000.0,
    "down_payment_percent": 30.0,
    "loan_term_years": 20,
    "annual_interest_rate": 7.5,
    "preferential_period_months": 12,
    "post_preferential_rate": 10.5,
    "calculation_method": "declining_balance"
  }
  ```
- **Response (`MortgageCalcResponse` - HTTP 200)**:
  ```json
  {
    "property_price": 5000000000.0,
    "down_payment_amount": 1500000000.0,
    "down_payment_percent": 30.0,
    "loan_amount": 3500000000.0,
    "loan_term_years": 20,
    "loan_term_months": 240,
    "calculation_method": "declining_balance",
    "monthly_payment_first_month": 36458333.33,
    "monthly_payment_max": 45208333.33,
    "monthly_payment_min": 14710069.44,
    "total_interest": 3574375000.0,
    "total_payment": 7074375000.0,
    "schedule": [
      {
        "month": 1,
        "principal_payment": 14583333.33,
        "interest_payment": 21875000.0,
        "total_payment": 36458333.33,
        "remaining_balance": 3485416666.67,
        "interest_rate": 7.5
      }
    ]
  }
  ```

---

### 2.8. Module Cảnh Báo & Thông Báo (`/alerts` & `/notifications`)

#### 1. Tạo cảnh báo tìm kiếm
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
- **Response (`AlertResponse` - HTTP 201)**: Chi tiết cảnh báo vừa tạo.

#### 2. Lấy danh sách cảnh báo của tôi
- **Endpoint**: `GET /api/v1/alerts`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`list[AlertResponse]` - HTTP 200)**.

#### 3. Cập nhật bật/tắt cảnh báo
- **Endpoint**: `PATCH /api/v1/alerts/{id}`
- **Xác thực**: Bắt buộc (Chủ sở hữu)
- **Request Body (`UpdateAlertRequest`)**: `{"is_active": false}`.

#### 4. Xóa cảnh báo
- **Endpoint**: `DELETE /api/v1/alerts/{id}`
- **Xác thực**: Bắt buộc (Chủ sở hữu)
- **Response**: HTTP 204 No Content.

#### 5. Danh sách thông báo in-app
- **Endpoint**: `GET /api/v1/notifications`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response (`NotificationListResponse` - HTTP 200)**: Danh sách các thông báo nhận được kèm số lượng chưa đọc (`unread_count`).

#### 6. Đánh dấu tất cả đã đọc
- **Endpoint**: `POST /api/v1/notifications/read-all`
- **Xác thực**: Bắt buộc (Bearer Token)
- **Response**: `{"message": "Marked all notifications as read"}`.

---

### 2.9. Module Giám Sát Hệ Thống (`/health`)

#### Kiểm tra tình trạng hoạt động (Healthcheck)
- **Endpoint**: `GET /api/v1/health`
- **Xác thực**: Không yêu cầu
- **Response (HTTP 200)**:
  ```json
  {
    "status": "ok",
    "app_name": "Space247",
    "version": "0.1.0",
    "database": "connected",
    "pgvector": "available",
    "redis": "connected"
  }
  ```
