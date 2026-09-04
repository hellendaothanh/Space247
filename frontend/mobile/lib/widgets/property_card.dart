import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/search_result.dart';
import '../providers/app_providers.dart';
import '../core/utils.dart';
import '../core/theme.dart';
import '../screens/property_detail_screen.dart';

class PropertyCard extends ConsumerWidget {
  final SearchResultItem item;
  final bool showSimilarity;

  const PropertyCard({
    super.key,
    required this.item,
    this.showSimilarity = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final property = item.property;
    final matchScore = item.similarityPercentage;
    final favoriteIds = ref.watch(favoriteIdsProvider);
    final isFav = favoriteIds.contains(property.id);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (ctx) => PropertyDetailScreen(propertyId: property.id),
            ),
          );
        },
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image Stack with Badges
            Stack(
              children: [
                Container(
                  height: 180,
                  width: double.infinity,
                  color: Colors.grey.shade200,
                  child: CachedNetworkImage(
                    imageUrl: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80',
                    fit: BoxFit.cover,
                    placeholder: (context, url) => Container(
                      color: Colors.grey.shade100,
                      child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
                    ),
                    errorWidget: (context, url, error) => Container(
                      color: Colors.grey.shade300,
                      child: const Icon(Icons.home_work_outlined, size: 48, color: Colors.grey),
                    ),
                  ),
                ),
                // Top Right: Favorite Button & AI Similarity Badge
                Positioned(
                  top: 12,
                  right: 12,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (showSimilarity) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.75),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: Colors.greenAccent.withValues(alpha: 0.6), width: 1.5),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.auto_awesome, color: Colors.greenAccent, size: 14),
                              const SizedBox(width: 4),
                              Text(
                                '$matchScore% match',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 6),
                      ],
                      Material(
                        color: Colors.white.withValues(alpha: 0.9),
                        shape: const CircleBorder(),
                        clipBehavior: Clip.antiAlias,
                        child: InkWell(
                          onTap: () async {
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
                          child: Padding(
                            padding: const EdgeInsets.all(6.0),
                            child: Icon(
                              isFav ? Icons.favorite : Icons.favorite_border,
                              color: isFav ? Colors.redAccent : Colors.grey.shade700,
                              size: 18,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                // Listing Type Badge
                Positioned(
                  top: 12,
                  left: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: property.listingType == 'sale' ? AppTheme.primaryColor : AppTheme.secondaryColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      Formatters.listingTypeLabel(property.listingType).toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ),
              ],
            ),

            // Details
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    property.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        Formatters.formatPrice(property.price, currency: property.currency),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                      Text(
                        Formatters.formatArea(property.areaSqm),
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Specifications Row
                  Row(
                    children: [
                      if (property.numBedrooms != null) ...[
                        const Icon(Icons.bed_outlined, size: 16, color: AppTheme.textSecondary),
                        const SizedBox(width: 4),
                        Text('${property.numBedrooms} PN', style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                        const SizedBox(width: 14),
                      ],
                      if (property.numBathrooms != null) ...[
                        const Icon(Icons.bathtub_outlined, size: 16, color: AppTheme.textSecondary),
                        const SizedBox(width: 4),
                        Text('${property.numBathrooms} PT', style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                        const SizedBox(width: 14),
                      ],
                      const Icon(Icons.category_outlined, size: 16, color: AppTheme.textSecondary),
                      const SizedBox(width: 4),
                      Text(Formatters.propertyTypeLabel(property.propertyType), style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  // Address
                  Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 16, color: Colors.redAccent),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          '${property.address}, ${property.city}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
