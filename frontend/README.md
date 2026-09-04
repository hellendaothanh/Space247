# Space247 — Frontend Architecture

Kiến trúc frontend đa nền tảng phục vụ Web và Mobile với unified backend API contracts.

## Cấu Trúc Thư Mục

\`\`\`
frontend/
├── shared/                   # Universal TypeScript SDK — dùng chung Web & Mobile
│   ├── types.ts              # Toàn bộ DTOs phản chiếu Pydantic backend schemas
│   ├── api-client.ts         # Fetch-based API client cho tất cả REST endpoints
│   └── constants.ts          # Enums, filter limits, vector dimensions (768)
│
├── web/                      # Next.js 16.3.4 — App Router (SSR + Dynamic Routes)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                     # Trang chủ — danh sách BĐS + AI Chat Widget
│   │   │   ├── properties/
│   │   │   │   ├── [id]/page.tsx            # Chi tiết BĐS (SSR, dynamic)
│   │   │   │   ├── [id]/edit/page.tsx       # Chỉnh sửa bài đăng
│   │   │   │   ├── create/page.tsx          # Tạo tin đăng mới
│   │   │   │   └── my/page.tsx              # Bài đăng của tôi
│   │   │   ├── favorites/page.tsx           # BĐS yêu thích
│   │   │   ├── profile/alerts/page.tsx      # Quản lý cảnh báo tìm kiếm
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── components/
│   │   │   ├── PropertyGallery.tsx          # Carousel ảnh + thumbnail strip + counter
│   │   │   ├── PropertyShareButton.tsx      # Web Share API + clipboard fallback + toast
│   │   │   ├── PropertyDetailMap.tsx        # OpenStreetMap / Leaflet tương tác
│   │   │   ├── PropertyFavoriteButton.tsx   # Toggle yêu thích
│   │   │   ├── PropertyCard.tsx             # Card danh sách BĐS
│   │   │   ├── MortgageCalculator.tsx       # Bảng tính vay mua nhà tương tác
│   │   │   ├── ChatAssistantWidget.tsx      # Floating AI Chat (mở rộng / thu nhỏ)
│   │   │   ├── NotificationBell.tsx         # Badge chưa đọc + dropdown thông báo
│   │   │   ├── IsochroneSearchWidget.tsx    # Tìm kiếm theo vùng di chuyển
│   │   │   ├── AmenityHeatmapLayer.tsx      # Leaflet heatmap tiện ích
│   │   │   └── Navbar.tsx
│   │   └── lib/
│   │       ├── api.ts                       # apiClient singleton (từ shared/)
│   │       └── utils.ts                     # formatPrice, formatPropertyType, ...
│   └── package.json
│
└── mobile/                   # Flutter — cross-platform iOS & Android
    ├── lib/
    │   ├── core/
    │   │   ├── api_client.dart              # Dio-based HTTP client
    │   │   ├── theme.dart                   # AppTheme colors & typography
    │   │   └── utils.dart                   # Formatters (price, type, listing)
    │   ├── models/
    │   │   ├── property.dart                # Property + PropertyAgent fromJson/toJson
    │   │   └── user.dart
    │   ├── providers/
    │   │   └── app_providers.dart           # Riverpod providers (auth, properties, favorites)
    │   └── screens/
    │       ├── home_screen.dart
    │       ├── property_detail_screen.dart  # Gallery PageView, MarkdownBody, share_plus, url_launcher
    │       ├── property_list_screen.dart
    │       ├── login_screen.dart
    │       ├── register_screen.dart
    │       └── profile_screen.dart
    └── pubspec.yaml
\`\`\`

## Nguyên Tắc Kiến Trúc

1. **Decoupled Client Boundaries** — Web (`frontend/web`) và Mobile (`frontend/mobile`) độc lập về rendering pipeline, build config và navigation.

2. **Single Source of Truth — `frontend/shared/`** — DTOs, API contracts và network client dùng chung, tránh drift giữa Web và Mobile.

3. **Rendering Strategy**
   - **Web (Next.js App Router)**: SSR cho trang chi tiết BĐS (`/properties/[id]`) — SEO, social preview meta tags. Static pages (`/login`, `/register`, ...) được prerendered.
   - **Mobile (Flutter + Riverpod)**: Client-side rendering tối ưu gesture, map clustering, offline cache.

4. **Shared TypeScript Types** — `PropertyResponse`, `PropertyAgent`, `PropertyDetailResponse`, `AlertResponse`, `NotificationResponse`, ... phản chiếu trực tiếp Pydantic backend schemas.

## Các Package Phụ Thuộc Quan Trọng

### Web (`frontend/web`)
| Package | Phiên bản | Mục đích |
|---|---|---|
| `next` | 16.3.4 | App Router SSR framework |
| `react` | 19 | UI library |
| `tailwindcss` | v4 | Utility CSS framework |
| `react-markdown` | ^10.1.0 | Render mô tả BĐS Markdown |
| `remark-gfm` | Latest | GitHub Flavored Markdown plugin |
| `leaflet` / `react-leaflet` | Latest | Bản đồ tương tác |
| `lucide-react` | Latest | Icon library |

### Mobile (`frontend/mobile`)
| Package | Phiên bản | Mục đích |
|---|---|---|
| `flutter_riverpod` | ^3.4.3 | State management |
| `dio` | ^5.11.1 | HTTP client |
| `cached_network_image` | ^4.0.0 | Ảnh BĐS với cache |
| `flutter_markdown` | ^0.7.4 | Render mô tả Markdown |
| `flutter_map` | ^7.0.2 | Bản đồ OpenStreetMap |
| `share_plus` | ^13.3.0 | Native Share API |
| `url_launcher` | ^6.3.2 | Mở URL (tel:, mailto:) |
| `flutter_secure_storage` | ^11.0.0 | Lưu JWT an toàn |

## TypeScript Types Quan Trọng (`shared/types.ts`)

\`\`\`typescript
// Thông tin agent/môi giới phụ trách bài đăng
interface PropertyAgent {
  id: string;
  full_name: string;
  email: string;
  phone_number?: string | null;
  avatar_url?: string | null;
  role: string;
}

// Chi tiết BĐS — trả về từ GET /api/v1/properties/{id}
interface PropertyDetailResponse extends PropertyResponse {
  images: string[];           // URLs ảnh thực tế từ DB
  agent?: PropertyAgent | null;
}
\`\`\`

## Kiểm Thử & Build

\`\`\`bash
# Web — TypeScript check
cd frontend/web && npx tsc --noEmit

# Web — Production build
cd frontend/web && npm run build
# Output: 9/9 routes SUCCESS

# Mobile
cd frontend/mobile && flutter pub get && flutter run
\`\`\`

## API Client Usage (`shared/api-client.ts`)

\`\`\`typescript
import { apiClient } from "@/lib/api";

// Lấy chi tiết BĐS kèm images và agent
const property = await apiClient.getProperty(id);
// property.images: string[]
// property.agent: PropertyAgent | null

// Hybrid Search
const results = await apiClient.searchProperties({ query: "căn hộ 2PN Hà Nội" });

// Tạo cảnh báo tìm kiếm
await apiClient.createAlert({
  title: "Căn hộ Hà Nội",
  criteria: { city: "Hà Nội", property_type: "apartment", max_price: 3e9 },
  frequency: "daily"
});
\`\`\`
