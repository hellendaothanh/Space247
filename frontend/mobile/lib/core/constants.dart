import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class AppConstants {
  static const String appName = 'Space247';

  // Configurable via --dart-define=API_BASE_URL=...
  static const String _configuredBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
  static const String customBaseUrlKey = 'space247_custom_base_url';

  static String get defaultBaseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      return _configuredBaseUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8080/api/v1';
    }
    if (Platform.isAndroid) {
      // Khi dùng thiết bị thật cắm cáp: 'adb reverse tcp:8080 tcp:8080' cho phép gọi 'http://localhost:8080/api/v1'
      // Khi dùng Android Emulator: 10.0.2.2 trỏ về localhost máy tính.
      // Khi dùng thiết bị thật cắm cáp: 'adb reverse tcp:8080 tcp:8080' hoặc truyền --dart-define=API_BASE_URL=http://<IP>:8080/api/v1
      return 'http://10.0.2.2:8080/api/v1';
    }
    return 'http://localhost:8080/api/v1';
  }

  static const String tokenKey = 'space247_jwt_token';
  static const String userKey = 'space247_user_data';
}
