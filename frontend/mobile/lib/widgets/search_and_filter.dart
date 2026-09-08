import 'rental_details.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/app_providers.dart';
import '../core/theme.dart';

class SearchAndFilterHeader extends ConsumerStatefulWidget {
  const SearchAndFilterHeader({super.key});

  @override
  ConsumerState<SearchAndFilterHeader> createState() => _SearchAndFilterHeaderState();
}

class _SearchAndFilterHeaderState extends ConsumerState<SearchAndFilterHeader> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _controller.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submitSearch() {
    ref.read(searchFilterProvider.notifier).setQuery(_controller.text);
  }

  @override
  Widget build(BuildContext context) {
    final filterState = ref.watch(searchFilterProvider);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            offset: const Offset(0, 4),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (filterState.listingType == 'rent') Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () => _showRentalFilterModal(context),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.2)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.tune, size: 16, color: AppTheme.primaryColor),
                        const SizedBox(width: 6),
                        Text(
                          filterState.rentalFilters.isNotEmpty
                              ? 'Bộ lọc phòng (${filterState.rentalFilters.length} tiêu chí)'
                              : 'Bộ lọc nâng cao (Phòng trọ, CHDV, Homestay)',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryColor),
                        ),
                      ],
                    ),
                    const Icon(Icons.chevron_right, size: 18, color: AppTheme.primaryColor),
                  ],
                ),
              ),
            ),
          ),
          // Semantic Search Bar
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  onSubmitted: (_) => _submitSearch(),
                  decoration: InputDecoration(
                    hintText: 'Nhập mong muốn của bạn (Ví dụ: Căn hộ 2 phòng ngủ gần Metro view thoáng dưới 4 tỷ)...',
                    hintStyle: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                    prefixIcon: const Icon(Icons.auto_awesome, color: AppTheme.primaryColor, size: 20),
                    suffixIcon: _controller.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _controller.clear();
                              _submitSearch();
                            },
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: _submitSearch,
                icon: const Icon(Icons.search),
                style: IconButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Filter Chips Scrollable Row
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip(
                  label: 'Tất cả',
                  isSelected: filterState.listingType == null && filterState.propertyType == null && filterState.query.isEmpty,
                  onSelected: () {
                    _controller.clear();
                    ref.read(searchFilterProvider.notifier).resetFilters();
                  },
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: 'Mua bán',
                  isSelected: filterState.listingType == 'sale',
                  onSelected: () => ref.read(searchFilterProvider.notifier).setListingType('sale'),
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: 'Cho thuê',
                  isSelected: filterState.listingType == 'rent',
                  onSelected: () => ref.read(searchFilterProvider.notifier).setListingType('rent'),
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: 'Chung cư',
                  isSelected: filterState.propertyType == 'apartment',
                  onSelected: () => ref.read(searchFilterProvider.notifier).setPropertyType('apartment'),
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: 'Nhà phố',
                  isSelected: filterState.propertyType == 'house',
                  onSelected: () => ref.read(searchFilterProvider.notifier).setPropertyType('house'),
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: 'Biệt thự',
                  isSelected: filterState.propertyType == 'villa',
                  onSelected: () => ref.read(searchFilterProvider.notifier).setPropertyType('villa'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip({
    required String label,
    required bool isSelected,
    required VoidCallback onSelected,
  }) {
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => onSelected(),
      selectedColor: AppTheme.primaryColor.withValues(alpha: 0.15),
      labelStyle: TextStyle(
        fontSize: 13,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        color: isSelected ? AppTheme.primaryColor : AppTheme.textPrimary,
      ),
      side: BorderSide(
        color: isSelected ? AppTheme.primaryColor : const Color(0xFFE2E8F0),
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      showCheckmark: false,
    );
  }

  void _showRentalFilterModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (modalCtx) {
        final filterState = ref.watch(searchFilterProvider);
        return DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.75,
          maxChildSize: 0.9,
          builder: (_, scrollController) {
            return SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Bộ lọc phòng nâng cao',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.pop(modalCtx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: filterState.rentalFilters['rental_type'] as String?,
                    decoration: const InputDecoration(labelText: 'Loại hình chỗ ở'),
                    items: [
                      const DropdownMenuItem(value: '', child: Text('Tất cả')),
                      ...rentalTypeLabels.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))),
                    ],
                    onChanged: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter('rental_type', v == '' ? null : v),
                  ),
                  const SizedBox(height: 8),
                  for (final entry in {'min_price': 'Giá từ (đ/tháng)', 'max_price': 'Giá đến (đ/tháng)', 'max_deposit': 'Cọc tối đa (tháng)'}.entries)
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: TextFormField(
                        key: ValueKey(entry.key),
                        initialValue: filterState.rentalFilters[entry.key]?.toString() ?? '',
                        decoration: InputDecoration(labelText: entry.value),
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        onChanged: (v) {
                          final number = double.tryParse(v);
                          if (v.isEmpty || (number != null && number.isFinite && number >= 0)) {
                            ref.read(searchFilterProvider.notifier).setRentalFilter(entry.key, number);
                          }
                        },
                      ),
                    ),
                  const SizedBox(height: 12),
                  for (final entry in rentalRuleLabels.entries)
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: DropdownButtonFormField<String>(
                        decoration: InputDecoration(labelText: entry.value),
                        initialValue: filterState.rentalFilters[entry.key]?.toString() ?? '',
                        items: const [
                          DropdownMenuItem(value: '', child: Text('Không giới hạn')),
                          DropdownMenuItem(value: 'true', child: Text('Có')),
                          DropdownMenuItem(value: 'false', child: Text('Không')),
                        ],
                        onChanged: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter(entry.key, v == '' ? null : v == 'true'),
                      ),
                    ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryColor,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      onPressed: () => Navigator.pop(modalCtx),
                      child: const Text('Áp dụng bộ lọc', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
