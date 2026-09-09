import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/rental_property.dart';

class ViewingService {
  final ApiClient apiClient;
  ViewingService(this.apiClient);

  Future<List<ViewingSlot>> getAvailableSlots({required String unitId, required DateTime date}) async {
    try {
      final response = await apiClient.dio.get('/rentals/$unitId/available-slots', queryParameters: {'date': _date(date)});
      return ((response.data as List<dynamic>?) ?? []).map((item) => ViewingSlot.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (error) {
      throw Exception(_detail(error, 'Không thể tải khung giờ trống'));
    }
  }

  Future<RentalInquiry> bookAppointment({required String unitId, required ViewingSlot slot, String? message}) async {
    try {
      final response = await apiClient.dio.post('/rentals/units/$unitId/book-appointment', data: {'date': slot.date, 'start_time': slot.startTime, 'message': message});
      return RentalInquiry.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      throw Exception(_detail(error, 'Khung giờ vừa được người khác đặt'));
    }
  }

  Future<String> getCalendarIcs(String inquiryId) async {
    try {
      final response = await apiClient.dio.get('/rentals/appointments/$inquiryId/calendar.ics', options: Options(responseType: ResponseType.plain));
      return response.data.toString();
    } on DioException catch (error) {
      throw Exception(_detail(error, 'Không thể tải lịch hẹn'));
    }
  }

  static String _date(DateTime value) => '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  static String _detail(DioException error, String fallback) => error.response?.data is Map ? (error.response!.data['detail']?.toString() ?? fallback) : fallback;
}
