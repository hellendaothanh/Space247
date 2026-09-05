import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/agent_models.dart';

class AvmPriceAdvisorWidget extends StatefulWidget {
  final ApiClient apiClient;
  final String propertyType;
  final double areaSqm;
  final int? numBedrooms;
  final int? numBathrooms;
  final double? latitude;
  final double? longitude;
  final double? proposedPrice;
  final Function(double price)? onApplyPrice;

  const AvmPriceAdvisorWidget({
    Key? key,
    required this.apiClient,
    required this.propertyType,
    required this.areaSqm,
    this.numBedrooms,
    this.numBathrooms,
    this.latitude,
    this.longitude,
    this.proposedPrice,
    this.onApplyPrice,
  }) : super(key: key);

  @override
  State<AvmPriceAdvisorWidget> createState() => _AvmPriceAdvisorWidgetState();
}

class _AvmPriceAdvisorWidgetState extends State<AvmPriceAdvisorWidget> {
  bool _isLoading = false;
  String? _error;
  ValuationResponse? _data;

  Future<void> _fetchValuation() async {
    if (widget.areaSqm <= 0) {
      setState(() => _error = 'Vui lòng nhập diện tích hợp lệ');
      return;
    }
    if (widget.latitude == null || widget.longitude == null) {
      setState(() => _error = 'Vui lòng cung cấp tọa độ vị trí');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await widget.apiClient.dio.post(
        '/agent/valuation/estimate',
        data: {
          'property_type': widget.propertyType,
          'area_sqm': widget.areaSqm,
          'num_bedrooms': widget.numBedrooms,
          'num_bathrooms': widget.numBathrooms,
          'latitude': widget.latitude,
          'longitude': widget.longitude,
          'radius_km': 2.5,
          'user_proposed_price': widget.proposedPrice != null && widget.proposedPrice! > 0
              ? widget.proposedPrice
              : null,
        },
      );

      setState(() {
        _data = ValuationResponse.fromJson(response.data as Map<String, dynamic>);
      });
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      setState(() => _error = detail?.toString() ?? 'Lỗi định giá AVM');
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  String _formatPrice(double price) {
    if (price >= 1000000000) {
      return '${(price / 1000000000).toStringAsFixed(2)} tỷ';
    } else if (price >= 1000000) {
      return '${(price / 1000000).toStringAsFixed(1)} triệu';
    }
    return '${price.toStringAsFixed(0)} đ';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.blue.shade50.withOpacity(0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.blue.shade100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.query_stats, color: Colors.blue.shade700, size: 20),
                  const SizedBox(width: 8),
                  const Text(
                    'Định giá AVM AI',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                ],
              ),
              OutlinedButton.icon(
                onPressed: _isLoading ? null : _fetchValuation,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  visualDensity: VisualDensity.compact,
                ),
                icon: _isLoading
                    ? const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(strokeWidth: 1.5),
                      )
                    : const Icon(Icons.refresh, size: 14),
                label: Text(
                  _data == null ? 'Định giá' : 'Cập nhật',
                  style: const TextStyle(fontSize: 11),
                ),
              ),
            ],
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: TextStyle(color: Colors.amber.shade900, fontSize: 11)),
          ],
          if (_data != null) ...[
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Đơn giá đề xuất', style: TextStyle(fontSize: 10, color: Colors.grey)),
                    Text(
                      '${(_data!.estimatedPricePerSqm / 1000000).toStringAsFixed(1)} tr/m²',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text('Tổng giá thị trường', style: TextStyle(fontSize: 10, color: Colors.grey)),
                    Text(
                      _formatPrice(_data!.estimatedTotalPrice),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                        color: Colors.blue.shade800,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            if (_data!.pricingAdvice != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Text(
                  _data!.pricingAdvice!,
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade800),
                ),
              ),
            ],
            if (widget.onApplyPrice != null) ...[
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: () => widget.onApplyPrice!(_data!.estimatedTotalPrice),
                icon: const Icon(Icons.check, size: 14),
                label: Text('Áp dụng mức giá ${_formatPrice(_data!.estimatedTotalPrice)}'),
                style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
              ),
            ],
          ],
        ],
      ),
    );
  }
}
