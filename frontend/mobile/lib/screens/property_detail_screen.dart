import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/property.dart';
import '../providers/app_providers.dart';
import '../core/utils.dart';
import '../core/theme.dart';

class PropertyDetailScreen extends ConsumerStatefulWidget {
  final String propertyId;

  const PropertyDetailScreen({super.key, required this.propertyId});

  @override
  ConsumerState<PropertyDetailScreen> createState() => _PropertyDetailScreenState();
}

class _PropertyDetailScreenState extends ConsumerState<PropertyDetailScreen> {
  int _currentImageIndex = 0;

  @override
  Widget build(BuildContext context) {
    final propertyAsync = ref.watch(propertyDetailProvider(widget.propertyId));

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
          final displayImages = property.images.isNotEmpty
              ? property.images
              : const [
                  'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80',
                ];

          return CustomScrollView(
            slivers: [
              SliverAppBar(
                expandedHeight: 280.0,
                pinned: true,
                actions: [
                  // Native Share Action
                  CircleAvatar(
                    backgroundColor: Colors.black.withValues(alpha: 0.5),
                    child: IconButton(
                      icon: const Icon(Icons.share, color: Colors.white),
                      onPressed: () {
                        Share.share(
                          'Xem bất động sản: ${property.title}\nĐịa chỉ: ${property.address}, ${property.city}',
                          subject: property.title,
                        );
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Favorite Action
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
                  background: Stack(
                    fit: StackFit.expand,
                    children: [
                      PageView.builder(
                        itemCount: displayImages.length,
                        onPageChanged: (idx) {
                          setState(() {
                            _currentImageIndex = idx;
                          });
                        },
                        itemBuilder: (context, index) {
                          return CachedNetworkImage(
                            imageUrl: displayImages[index],
                            fit: BoxFit.cover,
                            placeholder: (_, _) => Container(color: Colors.grey.shade200),
                            errorWidget: (_, _, _) => Container(
                              color: Colors.grey.shade300,
                              child: const Icon(Icons.home_work, size: 64, color: Colors.grey),
                            ),
                          );
                        },
                      ),
                      if (displayImages.length > 1)
                        Positioned(
                          bottom: 16,
                          right: 16,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.65),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${_currentImageIndex + 1} / ${displayImages.length}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                    ],
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
                      // Description with Markdown
                      const Text('Mô tả bất động sản', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      MarkdownBody(
                        data: property.description,
                        styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
                          p: const TextStyle(fontSize: 15, height: 1.6, color: AppTheme.textPrimary),
                        ),
                      ),

                      // Dynamic Agent Card
                      const SizedBox(height: 24),
                      const Text('Thông tin người đăng tin', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      _buildAgentCard(context, property),

                      if (property.latitude != null && property.longitude != null) ...[
                        const SizedBox(height: 24),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Vị trí địa lý & Bản đồ', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                            Text(
                              '${property.latitude!.toStringAsFixed(4)}, ${property.longitude!.toStringAsFixed(4)}',
                              style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: SizedBox(
                            height: 220,
                            child: FlutterMap(
                              options: MapOptions(
                                initialCenter: LatLng(property.latitude!, property.longitude!),
                                initialZoom: 15.0,
                              ),
                              children: [
                                TileLayer(
                                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                                  userAgentPackageName: 'com.space247.mobile',
                                ),
                                MarkerLayer(
                                  markers: [
                                    Marker(
                                      point: LatLng(property.latitude!, property.longitude!),
                                      width: 40,
                                      height: 40,
                                      child: Container(
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryColor,
                                          shape: BoxShape.circle,
                                          border: Border.all(color: Colors.white, width: 2.5),
                                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                                        ),
                                        child: const Icon(Icons.home, color: Colors.white, size: 22),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                      const SizedBox(height: 100), // Bottom padding for contact button
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
      bottomNavigationBar: propertyAsync.maybeWhen(
        data: (property) {
          final agentPhone = property.agent?.phoneNumber ?? '1900247247';
          return Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.08),
                  offset: const Offset(0, -3),
                  blurRadius: 10,
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              bottom: true,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    // Cột giá tiền bên trái
                    Expanded(
                      flex: 2,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Giá niêm yết',
                            style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            Formatters.formatPrice(property.price, currency: property.currency),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Nút Liên Hệ Ngay bên phải
                    Expanded(
                      flex: 3,
                      child: ElevatedButton.icon(
                        onPressed: () => _callPhoneNumber(context, agentPhone),
                        icon: const Icon(Icons.phone_in_talk, size: 20),
                        label: const Text(
                          'Liên hệ ngay',
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryColor,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 2,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
        orElse: () => null,
      ),
    );
  }

  Widget _buildAgentCard(BuildContext context, Property property) {
    final agent = property.agent;
    final agentName = (agent?.fullName != null && agent!.fullName.isNotEmpty)
        ? agent.fullName
        : 'Chuyên viên Space247';
    final agentRole = agent?.role == 'agent'
        ? 'Chuyên viên tư vấn Space247'
        : agent?.role == 'admin'
            ? 'Quản trị viên Space247'
            : 'Người đăng tin Space247';
    final agentPhone = agent?.phoneNumber ?? '1900 247 247';
    final agentEmail = (agent?.email != null && agent!.email.isNotEmpty)
        ? agent.email
        : 'support@space247.vn';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              if (agent?.avatarUrl != null && agent!.avatarUrl!.isNotEmpty)
                ClipOval(
                  child: CachedNetworkImage(
                    imageUrl: agent.avatarUrl!,
                    width: 52,
                    height: 52,
                    fit: BoxFit.cover,
                    errorWidget: (_, _, _) => _defaultAvatar(agentName),
                  ),
                )
              else
                _defaultAvatar(agentName),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      agentName,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      agentRole,
                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 4),
                    const Row(
                      children: [
                        Icon(Icons.verified, size: 14, color: Colors.green),
                        SizedBox(width: 4),
                        Text('Đã xác minh', style: TextStyle(fontSize: 11, color: Colors.green, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _callPhoneNumber(context, agentPhone),
                  icon: const Icon(Icons.phone, size: 16),
                  label: Text(agentPhone),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primaryColor,
                    side: const BorderSide(color: AppTheme.primaryColor),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _sendEmail(context, agentEmail),
                  icon: const Icon(Icons.email_outlined, size: 16),
                  label: const Text('Email'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.textPrimary,
                    side: BorderSide(color: Colors.grey.shade300),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _defaultAvatar(String name) {
    final words = name.split(' ').where((w) => w.isNotEmpty).toList();
    final initials = words.isNotEmpty
        ? words.map((w) => w[0]).take(2).join('').toUpperCase()
        : 'SP';
    return CircleAvatar(
      radius: 26,
      backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.15),
      child: Text(
        initials,
        style: const TextStyle(color: AppTheme.primaryColor, fontWeight: FontWeight.bold, fontSize: 16),
      ),
    );
  }

  Future<void> _callPhoneNumber(BuildContext context, String phone) async {
    final cleanPhone = phone.replaceAll(RegExp(r'\s+'), '');
    final uri = Uri.parse('tel:$cleanPhone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không thể thực hiện cuộc gọi tới $phone')),
        );
      }
    }
  }

  Future<void> _sendEmail(BuildContext context, String email) async {
    final uri = Uri.parse('mailto:$email');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không thể mở ứng dụng email tới $email')),
        );
      }
    }
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
