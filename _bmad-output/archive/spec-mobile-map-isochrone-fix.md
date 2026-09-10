---
route: oneshot
status: done
title: "Fix Flutter Mobile Interactive Map Isochrone 404 & UI null issue"
created: 2026-09-05
completed: 2026-09-05
---

# Spec: Sửa lỗi màn hình Bản đồ tương tác trên Flutter Mobile (DioException 404 khi tính Isochrone)

## 1. Problem Statement
- Trên ứng dụng Flutter Mobile (`frontend/mobile`), khi mở màn hình Bản đồ tương tác (`MapExplorerScreen`):
  1. Header hiển thị: `"null • 15 phút (motorcycle)"` do `_landmarkName` và `_landmarkLocation` ban đầu là `null`.
  2. Khi gửi request tính toán vùng di chuyển (Isochrone), app gặp lỗi `DioException [bad response]: 404 Not Found`. Nguyên nhân do:
     - `map_explorer_screen.dart` gọi path `/api/v1/spatial/isochrone-search` với leading slash kết hợp cùng `baseUrl = 'http://localhost:8080/api/v1'`. Dio ghép chuỗi tạo thành `/api/v1/api/v1/spatial/isochrone-search` gây lỗi 404.
     - Android emulator cần trỏ về `http://10.0.2.2:8080/api/v1` thay vì `http://localhost:8080/api/v1`.
     - Thiếu logic chuẩn hóa URL trong `ApiClient` để luôn đảm bảo request path giữ nguyên prefix `/api/v1`.
  3. Backend `POST /api/v1/spatial/isochrone-search` khi không tìm thấy địa danh chưa trả về 404 với thông báo hướng dẫn rõ ràng ("Không tìm thấy địa danh '...'. Vui lòng chọn điểm mốc khác hoặc nhập tọa độ dạng 'vĩ_độ, kinh_độ'.").

## 2. Implemented Solution & Changes

### A. Flutter Mobile (`frontend/mobile`):
1. **`lib/core/constants.dart`**:
   - Cập nhật `defaultBaseUrl` đối với Android emulator trả về `http://10.0.2.2:8080/api/v1`.
2. **`lib/core/api_client.dart`**:
   - Thêm interceptor chuẩn hóa URL trong `InterceptorsWrapper.onRequest`:
     Tự động xử lý prefix và leading slash để bất kể request gọi `spatial/isochrone-search` hay `/spatial/isochrone-search` hay `/api/v1/spatial/isochrone-search`, URL cuối cùng luôn là `${baseUrl}/spatial/isochrone-search`.
3. **`lib/screens/map_explorer_screen.dart`**:
   - Khởi tạo giá trị mặc định hợp lệ:
     - `_landmark = 'Keangnam'`
     - `_landmarkName = 'Keangnam Landmark 72 (Hà Nội)'`
     - `_landmarkLocation = const LatLng(21.0167, 105.7839)`
   - Cập nhật banner hiển thị tên điểm mốc: kiểm tra nếu rỗng hiển thị placeholder `"Vui lòng chọn điểm mốc di chuyển"`, tránh hiển thị "null".
   - Guard `_runIsochroneSearch`: Nếu `_landmark.trim().isEmpty`, hiển thị thông báo hướng dẫn `"Vui lòng chọn điểm mốc di chuyển"` và không gọi API.
   - Sửa endpoint gọi API thành `'/spatial/isochrone-search'` và `'/spatial/amenities/heatmap'`.
4. **`lib/screens/profile_screen.dart` & `lib/services/auth_service.dart`**:
   - Dọn sạch unused import và lint warning để `flutter analyze` đạt chuẩn 0 issue / 0 warning.

### B. Backend (`backend/src/api/v1/endpoints/spatial.py` & tests):
1. **`endpoints/spatial.py`**:
   - Khi `loc_info` là `None`, trả về `HTTPException(status_code=404, detail=f"Không tìm thấy địa danh '{request.target_landmark}'. Vui lòng chọn điểm mốc khác hoặc nhập tọa độ dạng 'vĩ_độ, kinh_độ'.")`.
2. **`tests/api/v1/test_spatial.py`**:
   - Cập nhật test case unknown landmark kiểm tra status code 404 và message mới.

## 3. Verification Evidence
- `flutter analyze` trong `frontend/mobile`: Chạy sạch, `No issues found!`.
- `uv run pytest` trong `backend`: `129 passed, 8 warnings in 55.09s` (100% pass).
