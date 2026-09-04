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
2. **Android Studio & Android SDK** (nếu chạy Android Emulator / Thiết bị thật):
   - Đã cài **Android SDK Platform 37** (API Level 37) qua SDK Manager.
   - Đã cài **Android SDK Command-line Tools** và **Android SDK Platform-Tools**.
   - Đã cài **CMake (3.22.1)** và **Ninja** (yêu cầu để biên dịch các thư viện native C/C++ / JNI):
     ```bash
     # Cài đặt CMake 3.22.1 qua sdkmanager
     sdkmanager --install "cmake;3.22.1"
     
     # Hoặc cài đặt Ninja độc lập qua Homebrew (nếu dùng macOS)
     brew install ninja
     ```
3. **Xcode** (dành riêng cho macOS nếu chạy iOS Simulator / Thiết bị iOS):
   - Cài đặt thông qua Mac App Store và cài đặt Xcode Command Line Tools (`xcode-select --install`).
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
# Ví dụ chạy trên Android Emulator / thiết bị thật
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

1. **Lỗi `Dependency ':flutter_secure_storage' requires libraries... to compile against version 37 or later`:**
   - Đảm bảo trong `android/app/build.gradle.kts` đã đặt `compileSdk = 37`.
   - Cài đặt SDK 37 trong Android Studio: `Settings -> Languages & Frameworks -> Android SDK -> SDK Platforms -> Tích chọn Android 37`.

2. **Lỗi `[CXX1416] Could not find Ninja on PATH or in SDK CMake bin folders`:**
   - Lỗi này do CMake 3.22.1 của Android SDK thiếu binary Ninja hoặc chưa cài đặt hoàn chỉnh.
   - Khắc phục bằng lệnh tải lại CMake kèm Ninja chính thức:
     ```bash
     rm -rf ~/Library/Android/sdk/cmake/3.22.1
     ~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager --install "cmake;3.22.1"
     ```
   - Hoặc cài đặt Ninja toàn hệ thống qua Homebrew:
     ```bash
     brew install ninja
     ```

3. **Lỗi không kết nối được Backend trên Android Emulator:**
   - Đảm bảo bạn đang dùng địa chỉ loopback `10.0.2.2:8080` thay vì `localhost:8080`.
   - Kiểm tra xem API Gateway của dự án đã khởi động thành công trên cổng 8080 hay chưa.

4. **Lỗi `CocoaPods' specs repository is out-of-date` trên iOS:**
   ```bash
   cd ios
   pod repo update
   pod install
   cd ..
   ```

5. **Lỗi CocoaPods / Podfile lock trên iOS:**
   ```bash
   cd ios
   rm -rf Pods Podfile.lock
   pod install
   cd ..
   ```

Giải pháp 1: Đổi trực tiếp trên giao diện App (Không cần sửa code) ✨
Tôi vừa tích hợp nút Cài đặt Server ngay trên góc trên cùng của ứng dụng (biểu tượng ⚙️ cạnh nút yêu thích):

Khi bạn đổi sang máy tính khác hoặc mạng Wi-Fi khác, chỉ cần bấm vào biểu tượng ⚙️.
Một hộp thoại hiện ra cho phép bạn nhập bất kỳ IP / Domain nào (hoặc bấm chọn nhanh localhost:8080 / 10.0.2.2:8080).
Bấm "Lưu & Kết nối lại", ứng dụng sẽ tự động chuyển hướng API và tải lại dữ liệu tức thì mà không cần build lại app!
Giải pháp 2: Chuẩn localhost với lệnh adb reverse (Khuyên dùng khi cắm cáp USB)
Nếu bạn cắm cáp điện thoại vào bất kỳ máy tính nào (Mac, Windows, Linux), chạy lệnh này 1 lần duy nhất:

bash
adb reverse tcp:8080 tcp:8080
Lệnh này sẽ map cổng 8080 của điện thoại thẳng vào cổng 8080 của máy tính. Khi đó:

Trên điện thoại thật, app gọi http://localhost:8080/api/v1 hoạt động ngay lập tức trên mọi máy tính mà không cần biết IP của máy là gì!
Tôi đã đưa http://localhost:8080/api/v1 làm mặc định trong 

constants.dart
.
Giải pháp 3: Truyền IP động qua cờ khi chạy lệnh flutter run
Nếu bạn chạy trên máy khác với địa chỉ IP khác qua Wi-Fi, bạn chỉ cần truyền biến môi trường mà không cần chỉnh sửa code:

bash
flutter run --dart-define=API_BASE_URL=http://<IP_MÁY_MỚI>:8080/api/v1
Tóm tắt thay đổi vừa thực hiện:


lib/core/constants.dart
: Đã bỏ hoàn toàn IP fix cứng 192.168.1.3, chuyển về chuẩn localhost:8080 hỗ trợ adb reverse và --dart-define.


lib/core/api_client.dart
: Thêm phương thức updateBaseUrl(newUrl) giúp cập nhật địa chỉ API ngay lập tức lúc runtime.


lib/screens/home_screen.dart
: Bổ sung icon ⚙️ và Dialog cấu hình IP máy chủ trực quan, tiện lợi.