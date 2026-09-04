import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/comparison_notifier.dart';
import '../providers/app_providers.dart';
import '../core/theme.dart';
import '../core/utils.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ComparisonScreen extends ConsumerStatefulWidget {
  const ComparisonScreen({super.key});

  @override
  ConsumerState<ComparisonScreen> createState() => _ComparisonScreenState();
}

class _ComparisonScreenState extends ConsumerState<ComparisonScreen> {
  bool _isLoading = true;
  String _error = '';
  Map<String, dynamic>? _comparisonData;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fetchComparison();
    });
  }

  Future<void> _fetchComparison() async {
    final properties = ref.read(comparisonProvider);
    final propertyIds = properties.map((p) => p.id).toList();
    final dio = ref.read(apiClientProvider).dio;

    try {
      final response = await dio.post(
        '/properties/compare',
        data: {'property_ids': propertyIds},
      );

      if (response.statusCode == 200) {
        setState(() {
          _comparisonData = response.data;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Lỗi API: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Lỗi kết nối: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('So sánh Bất động sản'),
        backgroundColor: Colors.white,
        foregroundColor: AppTheme.textPrimary,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error, style: const TextStyle(color: Colors.red)))
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final props = _comparisonData!['properties'] as List;
    final markdown = _comparisonData!['analysis_markdown'] as String;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: [
                const DataColumn(label: Text('Tiêu chí', style: TextStyle(fontWeight: FontWeight.bold))),
                ...props.map((p) => DataColumn(
                  label: SizedBox(
                    width: 100,
                    child: Text(
                      p['title'],
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                )),
              ],
              rows: [
                DataRow(cells: [
                  const DataCell(Text('Giá tổng')),
                  ...props.map((p) => DataCell(Text(
                    Formatters.formatPrice(p['price'].toDouble()),
                    style: const TextStyle(color: AppTheme.primaryColor, fontWeight: FontWeight.bold),
                  ))),
                ]),
                DataRow(cells: [
                  const DataCell(Text('Diện tích')),
                  ...props.map((p) => DataCell(Text('${p['area_sqm']} m²'))),
                ]),
                DataRow(cells: [
                  const DataCell(Text('Đơn giá')),
                  ...props.map((p) => DataCell(Text(
                    '${Formatters.formatPrice(p['price_per_sqm'].toDouble())}/m²',
                    style: const TextStyle(color: Colors.green),
                  ))),
                ]),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade100),
              ),
              child: MarkdownBody(
                data: markdown,
              ),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
