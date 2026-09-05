# Space247 Mobile Client

Ứng dụng di động quản lý và tra cứu bất động sản Space247, được phát triển trên nền tảng Flutter, sử dụng Riverpod cho việc quản lý trạng thái (State Management) và thư viện Dio cho kết nối mạng API.

---

## 1. Yêu Cầu Tiên Quyết (Prerequisites)

Trước khi tiến hành cài đặt và chạy ứng dụng, hệ thống cần đáp ứng các điều kiện sau:

1. **Flutter SDK**: Phiên bản `>= 3.13.2` (khuyến nghị phiên bản Flutter ổn định mới nhất).
   - Kiểm tra bằng lệnh:
     ```bash
     flutter --version
     flutter doctor
     ```
2. **Android Studio & Android SDK** (dành cho máy ảo Android Emulator hoặc thiết bị Android thực tế):
   - Đã cài đặt Android SDK Platform 34 hoặc mới hơn.
   - Đã cài đặt Android SDK Command-line Tools và Platform-Tools (`adb`).
   - Đã cài đặt CMake và Ninja (phục vụ biên dịch các thành phần native C/C++):
     ```bash
     # macOS (qua Homebrew)
     brew install ninja
     ```
3. **Xcode** (dành cho macOS chạy iOS Simulator hoặc thiết bị iPhone):
   - Phiên bản Xcode mới nhất kèm Command Line Tools (`xcode-select --install`).
   - Quản lý phụ thuộc CocoaPods (nếu áp dụng):
     ```bash
     sudo gem install cocoapods
     ```
4. **Dịch vụ Backend API Space247**:
   - Máy chủ Backend FastAPI cần đang chạy trên cổng `8080`.

---

## 2. Cài Đặt và Khởi Tạo

Di chuyển vào thư mục mobile và tải các gói thư viện phụ thuộc:

```bash
cd frontend/mobile
flutter pub get
```

Nếu chạy trên môi trường iOS Simulator hoặc thiết bị iOS:

```bash
cd ios
pod install
cd ..
```

---

## 3. Cấu Hình Địa Chỉ API Backend

Địa chỉ API được cấu hình tập trung trong `lib/core/constants.dart`:
- **Android Emulator**: `http://10.0.2.2:8080/api/v1` (địa chỉ loopback kết nối tới `localhost:8080` của máy tính).
- **iOS Simulator / macOS / Web**: `http://localhost:8080/api/v1`.
- **Thiết bị thật (Physical Device)**: Sử dụng địa chỉ IP nội bộ của máy chủ (ví dụ `http://192.168.1.50:8080/api/v1`) hoặc cơ chế chuyển tiếp cổng của adb.

### Cấu hình qua tham số dòng lệnh (--dart-define)
Có thể chỉ định trực tiếp địa chỉ API tại thời điểm khởi chạy:

```bash
flutter run --dart-define=API_BASE_URL=http://<IP_MAY_CHU>:8080/api/v1
```

### Sử dụng chuyển tiếp cổng với adb (Áp dụng cho Android qua cáp USB)
Khi kết nối thiết bị thật qua cáp USB, có thể ánh xạ cổng trực tiếp:

```bash
adb reverse tcp:8080 tcp:8080
```
Lúc này thiết bị di động có thể kết nối trực tiếp đến `http://localhost:8080/api/v1`.

---

## 4. Hướng Dẫn Thực Thi Ứng Dụng

### 1. Kiểm tra danh sách thiết bị khả dụng
```bash
flutter devices
```

### 2. Chạy ứng dụng trên môi trường phát triển (Debug Mode)
```bash
# Khởi chạy trên thiết bị mặc định
flutter run

# Khởi chạy trên thiết bị cụ thể theo mã định danh (DeviceId)
flutter run -d emulator-5554
flutter run -d iPhone
```

### 3. Khởi chạy ở chế độ kiểm thử hiệu năng (Profile) hoặc phát hành (Release)
```bash
# Đo lường hiệu năng
flutter run --profile

# Môi trường phát hành
flutter run --release
```

---

## 5. Các Lệnh Kiểm Chuẩn Chất Lượng (Quality Gate)

```bash
# Kiểm tra phân tích tĩnh mã nguồn và quy chuẩn linter
flutter analyze

# Thực thi các ca kiểm thử tự động
flutter test

# Dọn dẹp bộ nhớ đệm và các tệp biên dịch trung gian
flutter clean
flutter pub get

# Đóng gói bộ cài đặt APK cho hệ điều hành Android
flutter build apk --release

# Đóng gói ứng dụng cho hệ điều hành iOS
flutter build ipa --release
```

---

## 6. Xử Lý Các Sự Cố Thường Gặp (Troubleshooting)

1. **Sự cố không thể kết nối Backend từ Android Emulator**:
   - Kiểm tra Backend API đã khởi động và lắng nghe trên `0.0.0.0:8080`.
   - Đảm bảo ứng dụng đang trỏ về `10.0.2.2:8080` thay vì `localhost:8080`.

2. **Cảnh báo thiếu công cụ Ninja hoặc CMake khi biên dịch Android**:
   - Cài đặt Ninja thông qua trình quản lý gói hệ thống (Homebrew trên macOS hoặc nạp biến môi trường PATH của SDK).

3. **Xung đột bộ nhớ đệm CocoaPods trên môi trường iOS**:
   ```bash
   cd ios
   rm -rf Pods Podfile.lock
   pod repo update
   pod install
   cd ..
   ```