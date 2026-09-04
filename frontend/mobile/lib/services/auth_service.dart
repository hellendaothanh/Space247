import 'dart:convert';
import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/constants.dart';
import '../models/user.dart';

class AuthService {
  final ApiClient apiClient;

  AuthService(this.apiClient);

  Future<AuthTokenResponse> login(String email, String password) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      final authResponse = AuthTokenResponse.fromJson(response.data as Map<String, dynamic>);
      await apiClient.secureStorage.write(key: AppConstants.tokenKey, value: authResponse.accessToken);
      await apiClient.secureStorage.write(key: AppConstants.userKey, value: jsonEncode(authResponse.user.toJson()));
      return authResponse;
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Đăng nhập không thành công');
    }
  }

  Future<User?> getCurrentUser() async {
    try {
      final response = await apiClient.dio.get('/auth/me');
      final user = User.fromJson(response.data as Map<String, dynamic>);
      await apiClient.secureStorage.write(key: AppConstants.userKey, value: jsonEncode(user.toJson()));
      return user;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        // Token expired or invalid, purge stale credentials
        await logout();
        return null;
      }
      // Offline fallback to local stored user
      final userStr = await apiClient.secureStorage.read(key: AppConstants.userKey);
      if (userStr != null) {
        return User.fromJson(jsonDecode(userStr) as Map<String, dynamic>);
      }
      return null;
    }
  }

  Future<void> logout() async {
    await apiClient.secureStorage.delete(key: AppConstants.tokenKey);
    await apiClient.secureStorage.delete(key: AppConstants.userKey);
  }

  Future<bool> isAuthenticated() async {
    final token = await apiClient.secureStorage.read(key: AppConstants.tokenKey);
    return token != null && token.isNotEmpty;
  }
}
