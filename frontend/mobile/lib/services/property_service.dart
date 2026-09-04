import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/property.dart';
import '../models/search_result.dart';

class PropertyService {
  final ApiClient apiClient;

  PropertyService(this.apiClient);

  Future<PropertySearchResponse> searchProperties({
    required String query,
    String? listingType,
    String? propertyType,
    double? minPrice,
    double? maxPrice,
    int limit = 20,
  }) async {
    try {
      final Map<String, dynamic> payload = {
        'query': query,
        'limit': limit,
        'enable_hybrid': true,
      };

      if (listingType != null && listingType.isNotEmpty) {
        payload['listing_type'] = listingType;
      }
      if (propertyType != null && propertyType.isNotEmpty) {
        payload['property_type'] = propertyType;
      }
      if (minPrice != null) {
        payload['min_price'] = minPrice;
      }
      if (maxPrice != null) {
        payload['max_price'] = maxPrice;
      }

      final response = await apiClient.dio.post(
        '/properties/search',
        data: payload,
      );

      return PropertySearchResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi tìm kiếm bất động sản');
    }
  }

  Future<Property> getPropertyById(String id) async {
    try {
      final response = await apiClient.dio.get('/properties/$id');
      return Property.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Không thể tải thông tin bất động sản');
    }
  }

  Future<List<Property>> getMyProperties() async {
    try {
      final response = await apiClient.dio.get('/properties/my');
      final list = (response.data as List<dynamic>?) ?? [];
      return list.map((item) => Property.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Không thể lấy danh sách tin đăng của bạn');
    }
  }
}
