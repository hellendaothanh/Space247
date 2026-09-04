import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/app_providers.dart';
import '../widgets/property_card.dart';
import '../models/search_result.dart';
import '../core/theme.dart';
import 'login_screen.dart';

class FavoritesScreen extends ConsumerWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final favoritesAsync = ref.watch(favoritePropertiesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bất động sản đã lưu'),
      ),
      body: authState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text('Lỗi tải thông tin đăng nhập: $err'),
        ),
        data: (user) {
          if (user == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.favorite_border, size: 64, color: Colors.grey.shade400),
                    const SizedBox(height: 16),
                    const Text(
                      'Đăng nhập để xem danh sách yêu thích',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Lưu lại các bất động sản bạn quan tâm để dễ dàng so sánh và theo dõi.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (ctx) => const LoginScreen()),
                        );
                      },
                      child: const Text('Đăng nhập ngay'),
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.refresh(favoritePropertiesProvider.future),
            child: favoritesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => ListView(
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
                            'Không thể tải danh sách yêu thích',
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
                            onPressed: () => ref.invalidate(favoritePropertiesProvider),
                            icon: const Icon(Icons.refresh),
                            label: const Text('Thử lại'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              data: (properties) {
                if (properties.isEmpty) {
                  return ListView(
                    children: [
                      const SizedBox(height: 100),
                      Center(
                        child: Column(
                          children: [
                            Icon(Icons.favorite_border, size: 64, color: Colors.grey.shade400),
                            const SizedBox(height: 16),
                            const Text(
                              'Chưa có bất động sản yêu thích nào',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Nhấn vào biểu tượng trái tim trên các bài đăng để lưu lại.',
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
                  itemCount: properties.length,
                  itemBuilder: (context, index) {
                    final prop = properties[index];
                    final searchItem = SearchResultItem(
                      property: prop,
                      similarityScore: 1.0,
                    );
                    return PropertyCard(
                      item: searchItem,
                      showSimilarity: false,
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}
