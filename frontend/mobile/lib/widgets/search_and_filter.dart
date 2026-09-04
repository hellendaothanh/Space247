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
          // Semantic Search Bar
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  onSubmitted: (_) => _submitSearch(),
                  decoration: InputDecoration(
                    hintText: 'Tìm kiếm AI: "chung cư 2 phòng ngủ gần Q1"...',
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
}
