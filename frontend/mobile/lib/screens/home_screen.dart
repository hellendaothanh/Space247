import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/app_providers.dart';
import '../widgets/search_and_filter.dart';
import '../widgets/property_card.dart';
import '../core/theme.dart';
import 'login_screen.dart';
import 'favorites_screen.dart';
import 'comparison_screen.dart';
import '../providers/comparison_notifier.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchResultsAsync = ref.watch(searchResultsProvider);
    final authState = ref.watch(authStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.apartment, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 8),
            RichText(
              text: const TextSpan(
                text: 'Space',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.textPrimary,
                ),
                children: [
                  TextSpan(
                    text: '247',
                    style: TextStyle(color: AppTheme.primaryColor),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.favorite_outline, color: Colors.redAccent),
            tooltip: 'Tin đã lưu',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (ctx) => const FavoritesScreen()),
              );
            },
          ),
          authState.when(
            data: (user) {
              if (user != null) {
                return PopupMenuButton<String>(
                  icon: CircleAvatar(
                    backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.2),
                    child: Text(
                      user.fullName.isNotEmpty ? user.fullName[0].toUpperCase() : 'U',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryColor),
                    ),
                  ),
                  onSelected: (value) {
                    if (value == 'logout') {
                      ref.read(authStateProvider.notifier).logout();
                    }
                  },
                  itemBuilder: (ctx) => [
                    PopupMenuItem(
                      enabled: false,
                      child: Text(user.fullName, style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                    ),
                    PopupMenuItem(
                      enabled: false,
                      child: Text(user.email, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                    ),
                    const PopupMenuDivider(),
                    const PopupMenuItem(
                      value: 'logout',
                      child: Row(
                        children: [
                          Icon(Icons.logout, size: 18, color: Colors.red),
                          SizedBox(width: 8),
                          Text('Đăng xuất', style: TextStyle(color: Colors.red)),
                        ],
                      ),
                    ),
                  ],
                );
              }
              return TextButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (ctx) => const LoginScreen()),
                  );
                },
                icon: const Icon(Icons.login, size: 18),
                label: const Text('Đăng nhập'),
              );
            },
            loading: () => const Padding(
              padding: EdgeInsets.all(12.0),
              child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
            ),
            error: (_, _) => IconButton(
              icon: const Icon(Icons.login),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (ctx) => const LoginScreen()),
                );
              },
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          const SearchAndFilterHeader(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => ref.refresh(searchResultsProvider.future),
              child: searchResultsAsync.when(
                data: (response) {
                  if (response.results.isEmpty) {
                    return ListView(
                      children: [
                        const SizedBox(height: 80),
                        Center(
                          child: Column(
                            children: [
                              Icon(Icons.search_off_rounded, size: 64, color: Colors.grey.shade400),
                              const SizedBox(height: 16),
                              const Text(
                                'Không tìm thấy bất động sản phù hợp',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Hãy thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm',
                                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }

                  return ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: response.results.length,
                    itemBuilder: (context, index) {
                      final item = response.results[index];
                      return PropertyCard(item: item);
                    },
                  );
                },
                loading: () => const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text(
                        'Đang phân tích ngữ nghĩa và tìm kiếm...',
                        style: TextStyle(color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
                error: (err, stack) => ListView(
                  children: [
                    const SizedBox(height: 80),
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          children: [
                            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
                            const SizedBox(height: 12),
                            const Text(
                              'Đã xảy ra lỗi kết nối',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              err.toString(),
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: () => ref.invalidate(searchResultsProvider),
                              icon: const Icon(Icons.refresh),
                              label: const Text('Thử lại'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: Consumer(
        builder: (context, ref, child) {
          final selectedProperties = ref.watch(comparisonProvider);
          if (selectedProperties.isEmpty) return const SizedBox.shrink();

          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Đã chọn ${selectedProperties.length}/3',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      GestureDetector(
                        onTap: () => ref.read(comparisonProvider.notifier).clearComparison(),
                        child: const Text(
                          'Xóa tất cả',
                          style: TextStyle(color: Colors.redAccent, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                  ElevatedButton(
                    onPressed: selectedProperties.length >= 2
                        ? () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (ctx) => const ComparisonScreen(),
                              ),
                            );
                          }
                        : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryColor,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('So sánh ngay'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
