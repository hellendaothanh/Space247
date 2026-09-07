import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../models/rental_property.dart';
import '../providers/app_providers.dart';

class HostManagementScreen extends ConsumerStatefulWidget {
  const HostManagementScreen({super.key});

  @override
  ConsumerState<HostManagementScreen> createState() => _HostManagementScreenState();
}

class _HostManagementScreenState extends ConsumerState<HostManagementScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;
  String? _errorMessage;

  HostDashboardStats? _stats;
  List<RentalContract> _contracts = [];
  List<MonthlyInvoice> _invoices = [];
  String _invoiceFilter = 'all';

  final NumberFormat _currencyFormat = NumberFormat.currency(
    locale: 'vi_VN',
    symbol: 'đ',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final hostService = ref.read(hostServiceProvider);
      final results = await Future.wait([
        hostService.getHostStats(),
        hostService.getHostContracts(),
        hostService.getHostInvoices(),
      ]);

      if (!mounted) return;

      setState(() {
        _stats = results[0] as HostDashboardStats;
        _contracts = results[1] as List<RentalContract>;
        _invoices = results[2] as List<MonthlyInvoice>;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _sendReminder(String invoiceId) async {
    try {
      final hostService = ref.read(hostServiceProvider);
      final res = await hostService.sendInvoiceReminder(invoiceId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res['message'] as String? ?? 'Đã gửi thông báo nhắc nợ thành công!'),
          backgroundColor: const Color(0xFF059669),
        ),
      );
      _loadData();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lỗi gửi nhắc nợ: $e'),
          backgroundColor: const Color(0xFFDC2626),
        ),
      );
    }
  }

  void _showGenerateInvoiceSheet() {
    if (_contracts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Chưa có hợp đồng thuê hoạt động nào để lập hóa đơn')),
      );
      return;
    }

    String selectedContractId = _contracts.first.id;
    final now = DateTime.now();
    final billingMonth = '${now.year}-${now.month.toString().padLeft(2, '0')}';
    final elecPrevController = TextEditingController(text: '0');
    final elecCurrController = TextEditingController(text: '0');
    final waterPrevController = TextEditingController(text: '0');
    final waterCurrController = TextEditingController(text: '0');
    bool isSubmitting = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
            top: 20,
            left: 20,
            right: 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Chốt Điện Nước Tháng',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(ctx).pop(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'Kỳ thanh toán: Tháng $billingMonth',
                style: const TextStyle(fontSize: 13, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 12),

              // Contract selector
              DropdownButtonFormField<String>(
                value: selectedContractId,
                decoration: InputDecoration(
                  labelText: 'Hợp đồng / Khách thuê',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                ),
                items: _contracts.map((c) {
                  return DropdownMenuItem(
                    value: c.id,
                    child: Text('${c.tenantName} (${c.tenantPhone})'),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) {
                    setSheetState(() => selectedContractId = val);
                  }
                },
              ),
              const SizedBox(height: 16),

              // Electricity
              const Text('Chỉ số Điện (kWh)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: elecPrevController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Chỉ số cũ',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: elecCurrController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Chỉ số mới',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Water
              const Text('Chỉ số Nước (m³)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: waterPrevController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Chỉ số cũ',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: waterCurrController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Chỉ số mới',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: isSubmitting
                      ? null
                      : () async {
                          final elecPrev = double.tryParse(elecPrevController.text) ?? 0;
                          final elecCurr = double.tryParse(elecCurrController.text) ?? 0;
                          final waterPrev = double.tryParse(waterPrevController.text) ?? 0;
                          final waterCurr = double.tryParse(waterCurrController.text) ?? 0;

                          if (elecCurr < elecPrev) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Chỉ số điện mới phải >= chỉ số cũ')),
                            );
                            return;
                          }

                          if (waterCurr < waterPrev) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Chỉ số nước mới phải >= chỉ số cũ')),
                            );
                            return;
                          }

                          setSheetState(() => isSubmitting = true);
                          try {
                            await ref.read(hostServiceProvider).generateMonthlyInvoices(
                              billingMonth: billingMonth,
                              readings: [
                                {
                                  'contract_id': selectedContractId,
                                  'electricity_previous': elecPrev,
                                  'electricity_current': elecCurr,
                                  'water_previous': waterPrev,
                                  'water_current': waterCurr,
                                },
                              ],
                            );
                            if (!mounted) return;
                            if (ctx.mounted) {
                              Navigator.of(ctx).pop();
                            }
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Đã lập hóa đơn tháng $billingMonth thành công!'),
                                backgroundColor: const Color(0xFF059669),
                              ),
                            );
                            _loadData();
                          } catch (err) {
                            setSheetState(() => isSubmitting = false);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Lỗi: $err'), backgroundColor: const Color(0xFFDC2626)),
                            );
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2563EB),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: isSubmitting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white))
                      : const Text('Phát Hành Hóa Đơn', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Kênh Chủ Nhà Space247'),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF0F172A),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF2563EB),
          unselectedLabelColor: const Color(0xFF64748B),
          indicatorColor: const Color(0xFF2563EB),
          tabs: const [
            Tab(text: 'Hóa Đơn Thu Phí'),
            Tab(text: 'Hợp Đồng Thuê'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showGenerateInvoiceSheet,
        backgroundColor: const Color(0xFF2563EB),
        icon: const Icon(Icons.receipt_long, color: Colors.white),
        label: const Text('Chốt Điện Nước', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 12),
                      Text(_errorMessage!, textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(onPressed: _loadData, child: const Text('Thử lại')),
                    ],
                  ),
                )
              : NestedScrollView(
                  headerSliverBuilder: (context, innerBoxIsScrolled) => [
                    SliverToBoxAdapter(child: _buildKpiHeader()),
                  ],
                  body: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildInvoicesTab(),
                      _buildContractsTab(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildKpiHeader() {
    if (_stats == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _buildKpiCard(
                  title: 'Lấp đầy',
                  value: '${_stats!.occupancyRate.toStringAsFixed(0)}%',
                  subtitle: '${_stats!.occupiedUnits}/${_stats!.totalUnits} phòng',
                  icon: Icons.meeting_room,
                  color: const Color(0xFF059669),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildKpiCard(
                  title: 'Doanh thu tháng',
                  value: _currencyFormat.format(_stats!.estimatedMonthlyRevenue),
                  subtitle: 'Ước tính từ hợp đồng',
                  icon: Icons.account_balance_wallet,
                  color: const Color(0xFF2563EB),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildKpiCard(
                  title: 'Hóa đơn chưa thu',
                  value: '${_stats!.unpaidInvoicesCount}',
                  subtitle: _stats!.unpaidInvoicesCount > 0 ? 'Cần gửi nhắc nợ' : 'Đã thu đầy đủ',
                  icon: Icons.warning_amber_rounded,
                  color: _stats!.unpaidInvoicesCount > 0 ? const Color(0xFFD97706) : const Color(0xFF64748B),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildKpiCard(
                  title: 'Yêu cầu chờ duyệt',
                  value: '${_stats!.pendingInquiriesCount}',
                  subtitle: 'Khách muốn xem phòng',
                  icon: Icons.notifications_active,
                  color: const Color(0xFF7C3AED),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildKpiCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
              Icon(icon, size: 18, color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 2),
          Text(subtitle, style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
        ],
      ),
    );
  }

  Widget _buildInvoicesTab() {
    final filtered = _invoices.where((inv) {
      if (_invoiceFilter == 'all') return true;
      return inv.status == _invoiceFilter;
    }).toList();

    return Column(
      children: [
        // Filter Chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              _buildFilterChip('all', 'Tất cả (${_invoices.length})'),
              const SizedBox(width: 8),
              _buildFilterChip('pending', 'Chờ thu'),
              const SizedBox(width: 8),
              _buildFilterChip('overdue', 'Quá hạn'),
              const SizedBox(width: 8),
              _buildFilterChip('paid', 'Đã thu'),
            ],
          ),
        ),

        Expanded(
          child: filtered.isEmpty
              ? const Center(
                  child: Text('Không có hóa đơn nào', style: TextStyle(color: Color(0xFF64748B))),
                )
              : ListView.separated(
                  padding: const EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 80),
                  itemCount: filtered.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final inv = filtered[index];
                    final isPaid = inv.status == 'paid';
                    final isOverdue = inv.status == 'overdue';

                    return Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Tháng ${inv.billingMonth}',
                                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: isPaid
                                      ? const Color(0xFFECFDF5)
                                      : isOverdue
                                          ? Colors.red.shade50
                                          : Colors.amber.shade50,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  isPaid
                                      ? 'Đã thu'
                                      : isOverdue
                                          ? 'Quá hạn'
                                          : 'Chờ thu',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: isPaid
                                        ? const Color(0xFF059669)
                                        : isOverdue
                                            ? const Color(0xFFDC2626)
                                            : const Color(0xFFD97706),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('Tiền phòng: ${_currencyFormat.format(inv.roomAmount)}',
                                  style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                              Text('Điện: ${_currencyFormat.format(inv.electricityAmount)}',
                                  style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('Nước: ${_currencyFormat.format(inv.waterAmount)}',
                                  style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                              if (inv.serviceAmount > 0)
                                Text('Dịch vụ: ${_currencyFormat.format(inv.serviceAmount)}',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                            ],
                          ),
                          const Divider(height: 20),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('Tổng thanh toán', style: TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
                                  Text(
                                    _currencyFormat.format(inv.totalAmount),
                                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF2563EB)),
                                  ),
                                ],
                              ),
                              if (!isPaid)
                                ElevatedButton.icon(
                                  onPressed: () => _sendReminder(inv.id),
                                  icon: const Icon(Icons.notifications_outlined, size: 16),
                                  label: const Text('Nhắc nợ'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFFEFF6FF),
                                    foregroundColor: const Color(0xFF2563EB),
                                    elevation: 0,
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  ),
                                ),
                            ],
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _invoiceFilter == key;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _invoiceFilter = key),
      selectedColor: const Color(0xFFEFF6FF),
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        color: isSelected ? const Color(0xFF2563EB) : const Color(0xFF64748B),
      ),
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    );
  }

  Widget _buildContractsTab() {
    if (_contracts.isEmpty) {
      return const Center(
        child: Text('Chưa có hợp đồng nào đang kích hoạt', style: TextStyle(color: Color(0xFF64748B))),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _contracts.length,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final c = _contracts[index];
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    c.tenantName,
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: const BoxDecoration(
                      color: Color(0xFFECFDF5),
                      borderRadius: BorderRadius.all(Radius.circular(6)),
                    ),
                    child: Text(
                      c.status.toUpperCase(),
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF059669)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text('SĐT: ${c.tenantPhone}', style: const TextStyle(fontSize: 13, color: Color(0xFF64748B))),
              const SizedBox(height: 6),
              Text(
                'Giá thuê: ${_currencyFormat.format(c.rentalPrice)}/tháng',
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF2563EB)),
              ),
              const SizedBox(height: 4),
              Text(
                'Điện: ${c.electricityRate.toStringAsFixed(0)} đ/kWh | Nước: ${c.waterRate.toStringAsFixed(0)} đ',
                style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
              ),
            ],
          ),
        );
      },
    );
  }
}
