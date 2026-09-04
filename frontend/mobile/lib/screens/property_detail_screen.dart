import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../providers/app_providers.dart';
import '../core/utils.dart';
import '../core/theme.dart';

class PropertyDetailScreen extends ConsumerWidget {
  final String propertyId;

  const PropertyDetailScreen({super.key, required this.propertyId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final propertyAsync = ref.watch(propertyDetailProvider(propertyId));

    return Scaffold(
      appBar: propertyAsync.hasError
          ? AppBar(title: const Text('Chi tiết bất động sản'))
          : null,
      body: propertyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
                const SizedBox(height: 12),
                Text('Không thể tải bài đăng', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(error.toString(), textAlign: TextAlign.center),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Quay lại'),
                ),
              ],
            ),
          ),
        ),
        data: (property) {
          return CustomScrollView(
            slivers: [
              SliverAppBar(
                expandedHeight: 280.0,
                pinned: true,
                actions: [
                  Consumer(
                    builder: (context, ref, _) {
                      final favoriteIds = ref.watch(favoriteIdsProvider);
                      final isFav = favoriteIds.contains(property.id);
                      return CircleAvatar(
                        backgroundColor: Colors.black.withValues(alpha: 0.5),
                        child: IconButton(
                          icon: Icon(
                            isFav ? Icons.favorite : Icons.favorite_border,
                            color: isFav ? Colors.redAccent : Colors.white,
                          ),
                          onPressed: () async {
                            final auth = ref.read(authStateProvider);
                            if (auth.value == null) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Vui lòng đăng nhập để lưu bất động sản yêu thích')),
                              );
                              return;
                            }
                            try {
                              await ref.read(favoriteIdsProvider.notifier).toggleFavorite(property.id);
                            } catch (_) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Không thể cập nhật danh sách yêu thích')),
                                );
                              }
                            }
                          },
                        ),
                      );
                    },
                  ),
                  const SizedBox(width: 8),
                ],
                flexibleSpace: FlexibleSpaceBar(
                  background: CachedNetworkImage(
                    imageUrl: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80',
                    fit: BoxFit.cover,
                    placeholder: (_, _) => Container(color: Colors.grey.shade200),
                    errorWidget: (_, _, _) => Container(
                      color: Colors.grey.shade300,
                      child: const Icon(Icons.home_work, size: 64, color: Colors.grey),
                    ),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Badge & Listing Type
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: property.listingType == 'sale' ? AppTheme.primaryColor : AppTheme.secondaryColor,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              Formatters.listingTypeLabel(property.listingType).toUpperCase(),
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: Colors.grey.shade300),
                            ),
                            child: Text(
                              Formatters.propertyTypeLabel(property.propertyType),
                              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      // Title
                      Text(
                        property.title,
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      // Address
                      Row(
                        children: [
                          const Icon(Icons.location_on, size: 18, color: Colors.redAccent),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              '${property.address}, ${property.city}',
                              style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      // Price & Area Box
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryColor.withValues(alpha: 0.05),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.2)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            Column(
                              children: [
                                const Text('Mức giá', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                const SizedBox(height: 4),
                                Text(
                                  Formatters.formatPrice(property.price, currency: property.currency),
                                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.primaryColor),
                                ),
                              ],
                            ),
                            Container(height: 36, width: 1, color: Colors.grey.shade300),
                            Column(
                              children: [
                                const Text('Diện tích', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                const SizedBox(height: 4),
                                Text(
                                  Formatters.formatArea(property.areaSqm),
                                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Features / Specs
                      const Text('Thông tin chi tiết', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          if (property.numBedrooms != null)
                            Expanded(
                              child: _buildSpecCard(Icons.bed_outlined, '${property.numBedrooms} Phòng ngủ'),
                            ),
                          if (property.numBedrooms != null && property.numBathrooms != null)
                            const SizedBox(width: 12),
                          if (property.numBathrooms != null)
                            Expanded(
                              child: _buildSpecCard(Icons.bathtub_outlined, '${property.numBathrooms} Phòng tắm'),
                            ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      // Description
                      const Text('Mô tả bất động sản', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(
                        property.description,
                        style: const TextStyle(fontSize: 15, height: 1.6, color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 100), // Bottom padding for contact button
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
      bottomSheet: propertyAsync.hasValue
          ? Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.08),
                    offset: const Offset(0, -4),
                    blurRadius: 12,
                  ),
                ],
              ),
              child: SafeArea(
                child: Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Chức năng liên hệ người đăng tin đang kết nối...')),
                          );
                        },
                        icon: const Icon(Icons.phone),
                        label: const Text('Liên hệ ngay'),
                      ),
                    ),
                  ],
                ),
              ),
            )
          : null,
    );
  }

  Widget _buildSpecCard(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppTheme.primaryColor, size: 20),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
            ),
          ),
        ],
      ),
    );
  }
}
