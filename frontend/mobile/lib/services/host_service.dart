import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/rental_property.dart';

class HostService {
  final ApiClient apiClient;

  HostService(this.apiClient);

  Future<HostDashboardStats> getHostStats() async {
    try {
      final response = await apiClient.dio.get('/host/dashboard/stats');
      return HostDashboardStats.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi tải thống kê chủ nhà');
    }
  }

  Future<List<RentalContract>> getHostContracts() async {
    try {
      final response = await apiClient.dio.get('/host/contracts');
      final list = (response.data as List<dynamic>?) ?? [];
      return list.map((item) => RentalContract.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi tải danh sách hợp đồng');
    }
  }

  Future<List<MonthlyInvoice>> getHostInvoices({String? status, String? billingMonth}) async {
    try {
      final Map<String, dynamic> params = {};
      if (status != null && status.isNotEmpty) params['status'] = status;
      if (billingMonth != null && billingMonth.isNotEmpty) params['billing_month'] = billingMonth;

      final response = await apiClient.dio.get('/host/invoices', queryParameters: params);
      final list = (response.data as List<dynamic>?) ?? [];
      return list.map((item) => MonthlyInvoice.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi tải danh sách hóa đơn');
    }
  }

  Future<List<MonthlyInvoice>> generateMonthlyInvoices({
    required String billingMonth,
    required List<Map<String, dynamic>> readings,
    int dueDays = 5,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/host/invoices/generate-monthly',
        data: {
          'billing_month': billingMonth,
          'readings': readings,
          'due_days': dueDays,
        },
      );
      final list = (response.data as List<dynamic>?) ?? [];
      return list.map((item) => MonthlyInvoice.fromJson(item as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi phát hành hóa đơn');
    }
  }

  Future<Map<String, dynamic>> sendInvoiceReminder(String invoiceId) async {
    try {
      final response = await apiClient.dio.post('/host/invoices/$invoiceId/remind');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi khi gửi thông báo nhắc nợ');
    }
  }

  Future<DepositTransaction> approveInquiryAndDeposit({
    required String inquiryId,
    required double depositAmount,
  }) async {
    try {
      final response = await apiClient.dio.post(
        '/rentals/inquiries/$inquiryId/approve-and-deposit',
        data: {'deposit_amount': depositAmount},
      );
      return DepositTransaction.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi tạo liên kết đặt cọc');
    }
  }

  Future<DepositTransaction> getDepositTransaction(String referenceCode) async {
    try {
      final response = await apiClient.dio.get('/payments/deposit-transactions/$referenceCode');
      return DepositTransaction.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception(detail ?? 'Lỗi kiểm tra giao dịch đặt cọc');
    }
  }
}
