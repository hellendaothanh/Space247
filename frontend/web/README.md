# Space247 Web Client

Ứng dụng giao diện web cho nền tảng bất động sản Space247, được phát triển trên nền tảng Next.js 16 (App Router), React 19, TypeScript và Tailwind CSS v4. Ứng dụng cung cấp trải nghiệm tìm kiếm tương tác, bản đồ địa không gian, tính toán tài chính và tích hợp Trợ lý AI trực tiếp.

---

## 1. Yêu Cầu Kỹ Thuật

- Node.js >= 20 LTS
- npm >= 10 hoặc pnpm / yarn tương đương
- Dịch vụ Backend API Space247 đang hoạt động trên cổng 8080 (hoặc URL tương ứng)

---

## 2. Cài Đặt và Khởi Chạy

### Bước 1: Di chuyển vào thư mục web
```bash
cd frontend/web
```

### Bước 2: Cấu hình biến môi trường
Sao chép tệp mẫu sang `.env.local`:
```bash
cp .env.example .env.local
```

Nội dung cấu hình trong `.env.local`:
```ini
# Địa chỉ Backend API Space247
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

### Bước 3: Cài đặt các gói phụ thuộc
```bash
npm install
```

### Bước 4: Khởi chạy môi trường phát triển (Development)
```bash
npm run dev
```
Ứng dụng sẽ khả dụng tại địa chỉ: `http://localhost:3000`.

---

## 3. Các Lệnh Kiểm Tra Chất Lượng Mã Nguồn (Quality Gate)

Trước khi đóng gói hoặc tích hợp, mã nguồn cần vượt qua các bước kiểm tra nghiêm ngặt:

```bash
# 1. Kiểm tra an toàn kiểu dữ liệu TypeScript (0 lỗi yêu cầu)
npx tsc --noEmit

# 2. Kiểm tra định dạng và quy chuẩn mã nguồn
npm run lint

# 3. Biên dịch và đóng gói sản phẩm phục vụ môi trường thực tế (Production Build)
npm run build

# 4. Khởi chạy ứng dụng bản đóng gói sản phẩm
npm run start
```

---

## 4. Cấu Trúc Thư Mục

```
frontend/web/
├── public/                     # Tệp tĩnh, hình ảnh mẫu, favicon
├── src/
│   ├── app/                    # Next.js 16 App Router (các tuyến đường)
│   │   ├── (auth)/             # Nhóm định tuyến xác thực
│   │   │   ├── login/          # Trang đăng nhập
│   │   │   └── register/       # Trang đăng ký
│   │   ├── favorites/          # Danh sách BĐS đã đánh dấu yêu thích
│   │   ├── profile/            # Trang quản lý cá nhân
│   │   │   └── alerts/         # Quản lý cảnh báo tìm kiếm tự động
│   │   ├── properties/
│   │   │   ├── create/         # Trang đăng tin BĐS mới kèm AI Co-Pilot
│   │   │   ├── my/             # Danh sách BĐS do người dùng hiện tại đăng
│   │   │   └── [id]/           # Trang chi tiết BĐS
│   │   │       └── edit/       # Chỉnh sửa tin đăng BĐS
│   │   ├── layout.tsx          # Bố cục giao diện chung toàn ứng dụng
│   │   ├── page.tsx            # Trang chủ: tìm kiếm ngữ nghĩa, lọc và bản đồ
│   │   └── globals.css         # Cấu hình Tailwind CSS v4 toàn cục
│   ├── components/             # Các thành phần giao diện tái sử dụng
│   │   ├── auth/               # Biểu mẫu đăng nhập, đăng ký
│   │   ├── chat/               # ChatAssistantWidget (cửa sổ trợ lý AI nổi)
│   │   ├── common/             # Navbar, Footer, Modal, Toast notification
│   │   ├── map/                # Bản đồ tương tác Leaflet và Isochrone Heatmap
│   │   └── property/           # PropertyCard, PropertyGallery, MortgageCalculator,
│   │                           # PropertyShareButton, AIComparisonModal, AVMAdvisor
│   └── lib/                    # Cấu hình nội bộ, tiện ích format dữ liệu, cookie helper
├── package.json
├── tsconfig.json
├── next.config.ts
└── README.md
```

Thư viện dùng chung từ thư mục cấp cha:
- `../shared/types.ts`: Khai báo kiểu dữ liệu chung (Property, User, SearchCriteria, Mortgage, v.v.).
- `../shared/api-client.ts`: Lớp đóng gói gọi API RESTful chuẩn hóa.
- `../shared/constants.ts`: Các hằng số phân loại bất động sản và tiện ích.

---

## 5. Các Tính Năng Nổi Bật

1. **Điều Hướng & Lọc Dữ Liệu Đồng Bộ (URL Query State Routing)**:
   - Thanh điều hướng chuẩn hóa hỗ trợ các bộ lọc mục tiêu qua URL: `/?listing_type=sale` (Mua bán), `/?listing_type=rent` (Cho thuê), `/projects` (Dự án), và `/?view=map#map-view` (Bản đồ số).
   - Tự động đồng bộ trạng thái giữa thanh điều hướng, thanh tìm kiếm nhanh và danh sách bài đăng mà không làm tải lại trang.
   - Bọc toàn bộ các thành phần xử lý URL trong Next.js `<Suspense>` boundary đảm bảo khả năng tối ưu hóa tĩnh (SSG/ISR) tuyệt đối.
2. **Bản đồ Bất động sản Địa không gian GIS & Heatmap (Leaflet & PostGIS)**:
   - Bản đồ tương tác hiển thị ghim bài đăng theo tọa độ địa lý chuẩn WGS84, tự động điều chỉnh khung nhìn và phân cụm trực quan.
   - Bản đồ nhiệt tiện ích (Amenity Heatmap) phân lớp: Trường học, Bệnh viện, Ga Metro, Siêu thị với thuật toán ước lượng mật độ mượt mà.
   - Lớp phủ phân tích ranh giới di chuyển theo thời gian (Isochrone Reachability Polygon) và ghim định vị chuẩn GIS SVG.
   - Toàn bộ giao diện bản đồ tuân thủ tiêu chuẩn đồ họa chuyên nghiệp (Enterprise GIS), loại bỏ hoàn toàn các emoji không chuẩn mực.
3. **Bộ sưu tập hình ảnh (PropertyGallery)**: Trình diễn ảnh dạng lưới kèm thanh trượt thu nhỏ (thumbnail strip) và bộ đếm ảnh.
4. **Bảng tính vay mua nhà (MortgageCalculator)**: Tích hợp ngay trên trang chi tiết, cho phép tính số tiền trả góp theo dư nợ giảm dần hoặc niên kim cố định.
5. **Cửa sổ Trợ lý AI (ChatAssistantWidget)**: Khung chat nổi hỗ trợ tương tác tự nhiên, trích xuất nhu cầu và gợi ý thẻ bài đăng trực quan.
6. **So sánh Bất động sản AI**: Cho phép đối chiếu từ 2 đến 3 căn nhà theo đơn giá trên một mét vuông, vị trí địa lý, tiện ích và tiềm năng tăng trưởng.
7. **Công cụ Định giá Thông minh (AVM Price Advisor)**: Hỗ trợ môi giới ước tính khoảng giá thị trường tối ưu khi đăng tin.
