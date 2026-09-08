# Media Suite Space247

Media Suite cung cấp bộ media dùng chung cho tin bất động sản và dự án, gồm ảnh, video review, tour ảo và bản đồ.

## Dữ liệu và API

Revision Alembic `0012_add_media_urls` bổ sung hai cột nullable vào `properties` và `projects`:

| Cột | Kiểu | Mục đích |
|---|---|---|
| `video_url` | `VARCHAR(500)` | Link YouTube, YouTube Shorts hoặc TikTok |
| `virtual_tour_url` | `VARCHAR(500)` | Link Matterport hoặc VR 360 |

`images` tiếp tục là `TEXT[]`, dùng để lưu danh sách URL ảnh không giới hạn số lượng ở cấp ứng dụng.

Backend parser `parse_video_metadata(url)` chỉ chấp nhận URL HTTP/HTTPS thuộc YouTube hoặc TikTok và trả về `platform`, `video_id` và `embed_url` an toàn. URL không nhận diện được vẫn được lưu theo giá trị gốc nhưng không được nhúng.

## Web

`MediaSuite` được dùng tại `/properties/[id]` và `/projects/[slug]` với các tab ảnh thực tế, video review, tour 360° và vị trí bản đồ. Gallery hỗ trợ mosaic responsive, fallback ảnh, lightbox carousel, YouTube 16:9, Shorts/TikTok 9:16 và iframe lazy-loaded.

Form tạo và chỉnh sửa tin đăng nhận `video_url` và `virtual_tour_url`, giới hạn 500 ký tự.

## Mobile Flutter

Model `Property` và `ProjectSummary` đã đồng bộ hai trường media. Trang chi tiết hỗ trợ carousel ảnh với `InteractiveViewer` để pinch-to-zoom, mở video review an toàn qua external player và mở tour Matterport qua domain allow-list.

## Seed và kiểm tra

Seed mẫu bao gồm Vinhomes Central Park, Sun Cosmo Residence Đà Nẵng và Nhà trọ Bách Khoa.

```bash
cd backend && uv run pytest
cd frontend/web && npx tsc --noEmit && npm run build
cd frontend/mobile && flutter analyze
```

Kết quả xác nhận gần nhất: 174 backend tests passed, TypeScript/build passed và Flutter analyze passed.
