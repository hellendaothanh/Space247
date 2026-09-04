import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'constants.dart';

class ApiClient {
  late final Dio dio;
  final FlutterSecureStorage secureStorage;
  final String baseUrl;

  ApiClient({
    FlutterSecureStorage? secureStorage,
    String? baseUrl,
  })  : secureStorage = secureStorage ?? const FlutterSecureStorage(),
        baseUrl = baseUrl ?? AppConstants.defaultBaseUrl {
    dio = Dio(
      BaseOptions(
        baseUrl: this.baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await this.secureStorage.read(key: AppConstants.tokenKey);
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) {
          // Log or handle centralized errors if needed
          return handler.next(error);
        },
      ),
    );
  }

  void updateBaseUrl(String newUrl) {
    dio.options.baseUrl = newUrl;
  }
}
