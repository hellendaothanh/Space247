# Space247 Mobile App

Ứng dụng di động quản lý bất động sản và không gian làm việc **Space247**, được xây dựng bằng **Flutter**, sử dụng **Riverpod** cho State Management và **Dio** cho API networking.

---

## 📋 Yêu cầu tiên quyết (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:

1. **Flutter SDK**: Phiên bản `>= 3.13.2` (Khuyến nghị `3.22.x` trở lên)
   - Kiểm tra bằng lệnh:
     ```bash
     flutter --version
     flutter doctor
     ```
2. **Android Studio** (nếu chạy Android Emulator / Android Device):
   - Đã cài Android SDK, Command-line Tools và cấu hình Android Emulator.
3. **Xcode** (dành riêng cho macOS nếu chạy iOS Simulator / Thiết bị iOS):
   - Cài đặt thông qua Mac App Store và cài đặt Xcode Command Line Tools.
   - Cài đặt CocoaPods (nếu cần):
     ```bash
     sudo gem install cocoapods
     ```
4. **Backend Services (API Gateway)**:
   - Đảm bảo Backend (API Gateway) đang chạy trên cổng `8080`.

---

## 🚀 Cài đặt & Chuẩn bị

Di chuyển vào thư mục mobile:

```bash
cd frontend/mobile
```

Cài đặt các thư viện phụ thuộc (dependencies):

```bash
flutter pub get
```

Nếu chạy trên **iOS Simulator/Thiết bị iOS**, cài đặt CocoaPods:

```bash
cd ios
pod install
cd ..
```

---

## 🌐 Cấu hình API Backend (API Base URL)

Mặc định ứng dụng đã cấu hình tự động ánh xạ Base URL trong `lib/core/constants.dart`:
- **Android Emulator**: `http://10.0.2.2:8080/api/v1` (ánh xạ về `localhost:8080` của máy host)
- **iOS Simulator / macOS / Web**: `http://localhost:8080/api/v1`
- **Thiết bị thật (Physical Device)**: Cần trỏ đến địa chỉ IP nội bộ của máy chủ (ví dụ `http://192.168.1.50:8080/api/v1`)

### Tùy chỉnh API URL khi chạy:
Bạn có thể truyền trực tiếp biến môi trường qua cờ `--dart-define`:

```bash
flutter run --dart-define=API_BASE_URL=http://<IP_MAY_TINH_CUA_BAN>:8080/api/v1
```

---

## 📱 Hướng dẫn chạy ứng dụng (Running the App)

### 1. Kiểm tra danh sách thiết bị khả dụng

```bash
flutter devices
```

### 2. Chạy trên Android Emulator hoặc iOS Simulator

Khởi động Emulator / Simulator trước (hoặc mở trực tiếp từ VS Code / Android Studio), sau đó chạy:

```bash
flutter run
```

Nếu bạn có nhiều thiết bị đang bật, chỉ định mã thiết bị bằng tham số `-d`:

```bash
# Ví dụ chạy trên Android Emulator
flutter run -d emulator-5554

# Ví dụ chạy trên iOS Simulator
flutter run -d iPhone
```

### 3. Chạy ở chế độ Profile hoặc Release

- **Chế độ Profile** (đo đạc hiệu năng):
  ```bash
  flutter run --profile
  ```
- **Chế độ Release**:
  ```bash
  flutter run --release
  ```

---

## 🛠️ Các lệnh hữu ích khác

- **Kiểm tra linter và lỗi cú pháp**:
  ```bash
  flutter analyze
  ```
- **Chạy unit tests**:
  ```bash
  flutter test
  ```
- **Xóa cache và build artifacts (khi gặp lỗi build lạ)**:
  ```bash
  flutter clean
  flutter pub get
  ```
- **Build file cài đặt APK (Android)**:
  ```bash
  flutter build apk --release
  ```
- **Build cho iOS**:
  ```bash
  flutter build ipa --release
  ```

---

## ⚠️ Khắc phục sự cố thường gặp (Troubleshooting)

1. **Lỗi không kết nối được Backend trên Android Emulator:**
   - Đảm bảo bạn đang dùng địa chỉ loopback `10.0.2.2:8080` thay vì `localhost:8080`.
   - Kiểm tra xem API Gateway của dự án đã khởi động thành công trên cổng 8080 hay chưa.
2. **Lỗi `CocoaPods' specs repository is out-of-date` trên iOS:**
   ```bash
   cd ios
   pod repo update
   pod install
   cd ..
   ```
3. **Lỗi CocoaPods / Podfile lock:**
   ```bash
   cd ios
   rm -rf Pods Podfile.lock
   pod install
   cd ..
   ```

