import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class AppConstants {
  static const String appName = 'Space247';

  // Configurable via --dart-define=API_BASE_URL=...
  static const String _configuredBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');

  static String get defaultBaseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      return _configuredBaseUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8080/api/v1';
    }
    if (Platform.isAndroid) {
      // 10.0.2.2 is Android emulator loopback to host machine localhost
      return 'http://10.0.2.2:8080/api/v1';
    }
    return 'http://localhost:8080/api/v1';
  }

  static const String tokenKey = 'space247_jwt_token';
  static const String userKey = 'space247_user_data';
}
