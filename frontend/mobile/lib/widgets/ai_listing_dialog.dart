import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/agent_models.dart';

class AiListingDialog extends StatefulWidget {
  final ApiClient apiClient;
  final String initialPropertyType;
  final Function(GenerateListingResponse response) onApply;

  const AiListingDialog({
    Key? key,
    required this.apiClient,
    this.initialPropertyType = 'apartment',
    required this.onApply,
  }) : super(key: key);

  @override
  State<AiListingDialog> createState() => _AiListingDialogState();
}

class _AiListingDialogState extends State<AiListingDialog> {
  final TextEditingController _notesController = TextEditingController();
  final TextEditingController _targetAudienceController = TextEditingController();
  late String _propertyType;
  bool _isLoading = false;
  String? _errorMessage;
  GenerateListingResponse? _result;

  @override
  void initState() {
    super.initState();
    _propertyType = widget.initialPropertyType;
  }

  @override
  void dispose() {
    _notesController.dispose();
    _targetAudienceController.dispose();
    super.dispose();
  }

  Future<void> _generateListing() async {
    final notes = _notesController.text.trim();
    if (notes.isEmpty) {
      setState(() {
        _errorMessage = 'Vui lòng nhập ghi chú nhanh về bất động sản.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final bullets = notes.split('\n').where((l) => l.trim().isNotEmpty).toList();
      final response = await widget.apiClient.dio.post(
        '/agent/listing/generate',
        data: {
          'text_prompts': bullets.isNotEmpty ? bullets : [notes],
          'property_type': _propertyType,
          'target_audience': _targetAudienceController.text.trim().isNotEmpty
              ? _targetAudienceController.text.trim()
              : null,
        },
      );

      setState(() {
        _result = GenerateListingResponse.fromJson(response.data as Map<String, dynamic>);
      });
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      setState(() {
        _errorMessage = detail?.toString() ?? 'Lỗi khi tạo tin đăng bằng AI.';
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        width: MediaQuery.of(context).size.width * 0.9,
        padding: const EdgeInsets.all(20),
        constraints: const BoxConstraints(maxHeight: 650),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Colors.blue, size: 22),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'AI Listing Co-Pilot',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Tự động soạn tin & trích xuất thông số',
                          style: TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const Divider(height: 24),
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.red.shade200),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: Colors.red.shade800, fontSize: 12),
                  ),
                ),
                const SizedBox(height: 12),
              ],
              DropdownButtonFormField<String>(
                value: _propertyType,
                decoration: InputDecoration(
                  labelText: 'Loại hình BĐS',
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
                items: const [
                  DropdownMenuItem(value: 'apartment', child: Text('Căn hộ chung cư')),
                  DropdownMenuItem(value: 'house', child: Text('Nhà riêng / Nhà phố')),
                  DropdownMenuItem(value: 'villa', child: Text('Biệt thự cao cấp')),
                  DropdownMenuItem(value: 'land', child: Text('Đất nền')),
                  DropdownMenuItem(value: 'commercial', child: Text('Mặt bằng kinh doanh')),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => _propertyType = val);
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _notesController,
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: 'Ghi chú nhanh (Bullet notes)',
                  hintText: 'VD: Căn góc 3PN 95m2, view hồ, nội thất cao cấp, sổ hồng...',
                  hintStyle: const TextStyle(fontSize: 12),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _targetAudienceController,
                decoration: InputDecoration(
                  labelText: 'Khách hàng mục tiêu (Tùy chọn)',
                  hintText: 'VD: Gia đình trẻ, chuyên gia nước ngoài...',
                  hintStyle: const TextStyle(fontSize: 12),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _generateListing,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade600,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                icon: _isLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.auto_awesome, size: 18),
                label: Text(_isLoading ? 'AI đang soạn thảo...' : 'Tạo bài đăng bằng AI'),
              ),
              if (_result != null) ...[
                const SizedBox(height: 20),
                const Divider(),
                const Text(
                  'Tiêu đề SEO đề xuất:',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _result!.titleSeo,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Thông số AI trích xuất:',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    if (_result!.extractedSpecs.areaSqm != null)
                      Chip(
                        label: Text('${_result!.extractedSpecs.areaSqm} m²'),
                        backgroundColor: Colors.grey.shade100,
                      ),
                    if (_result!.extractedSpecs.numBedrooms != null)
                      Chip(
                        label: Text('${_result!.extractedSpecs.numBedrooms} PN'),
                        backgroundColor: Colors.grey.shade100,
                      ),
                    if (_result!.extractedSpecs.legalStatus != null)
                      Chip(
                        label: Text(_result!.extractedSpecs.legalStatus!),
                        backgroundColor: Colors.grey.shade100,
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () {
                    widget.onApply(_result!);
                    Navigator.of(context).pop();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF059669),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text('Áp dụng vào Form đăng tin'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
