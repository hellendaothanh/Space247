import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/theme.dart';
import '../providers/app_providers.dart';
import 'property_detail_screen.dart';
import 'login_screen.dart';

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  bool _isLoading = false;
  List<Map<String, dynamic>> _notifications = [];

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  Future<void> _fetchNotifications() async {
    setState(() => _isLoading = true);
    // Simulated/demo fetch or API fetch
    await Future.delayed(const Duration(milliseconds: 300));
    if (mounted) {
      setState(() {
        _notifications = [
          {
            'id': '1',
            'title': 'Bất động sản mới phù hợp: Vinhomes Smart City',
            'message': 'Căn hộ 2PN tại Nam Từ Liêm, Hà Nội với mức giá 3.5 tỷ phù hợp với tiêu chí tìm kiếm của bạn.',
            'created_at': DateTime.now().subtract(const Duration(minutes: 45)),
            'is_read': false,
            'property_id': null,
          },
          {
            'id': '2',
            'title': 'Bất động sản mới: Nhà phố Bình Thạnh',
            'message': 'Nhà phố 3 tầng hẻm xe hơi tại Bình Thạnh, TP.HCM phù hợp tiêu chí nhà bán dưới 6 tỷ.',
            'created_at': DateTime.now().subtract(const Duration(hours: 3)),
            'is_read': true,
            'property_id': null,
          },
        ];
        _isLoading = false;
      });
    }
  }

  void _markAllRead() {
    setState(() {
      for (var n in _notifications) {
        n['is_read'] = true;
      }
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Đã đánh dấu tất cả thông báo là đã đọc')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Thông báo'),
        actions: [
          if (_notifications.any((n) => n['is_read'] == false))
            IconButton(
              icon: const Icon(Icons.done_all),
              tooltip: 'Đã đọc tất cả',
              onPressed: _markAllRead,
            ),
        ],
      ),
      body: authState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Lỗi: $err')),
        data: (user) {
          if (user == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.notifications_none, size: 64, color: Colors.grey.shade400),
                    const SizedBox(height: 16),
                    const Text(
                      'Đăng nhập để xem thông báo',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Nhận thông báo ngay khi có bất động sản mới phù hợp với tiêu chí của bạn.',
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

          if (_isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (_notifications.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_off_outlined, size: 64, color: Colors.grey.shade300),
                  const SizedBox(height: 16),
                  const Text(
                    'Chưa có thông báo nào',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Lưu tiêu chí tìm kiếm để nhận cảnh báo bất động sản mới!',
                    style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: _fetchNotifications,
            child: ListView.separated(
              itemCount: _notifications.length,
              separatorBuilder: (ctx, idx) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final notif = _notifications[index];
                final bool isRead = notif['is_read'] == true;

                return InkWell(
                  onTap: () {
                    setState(() => notif['is_read'] = true);
                    if (notif['property_id'] != null) {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (ctx) => PropertyDetailScreen(
                            propertyId: notif['property_id'],
                          ),
                        ),
                      );
                    }
                  },
                  child: Container(
                    color: isRead ? Colors.transparent : Colors.blue.withOpacity(0.04),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        CircleAvatar(
                          radius: 18,
                          backgroundColor: isRead ? Colors.grey.shade200 : AppTheme.primaryColor.withOpacity(0.1),
                          child: Icon(
                            Icons.notifications_active,
                            size: 18,
                            color: isRead ? Colors.grey.shade600 : AppTheme.primaryColor,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      notif['title'],
                                      style: TextStyle(
                                        fontSize: 14,
                                        fontWeight: isRead ? FontWeight.w500 : FontWeight.bold,
                                        color: Colors.black87,
                                      ),
                                    ),
                                  ),
                                  if (!isRead)
                                    Container(
                                      width: 8,
                                      height: 8,
                                      margin: const EdgeInsets.only(left: 4),
                                      decoration: BoxDecoration(
                                        color: AppTheme.primaryColor,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(
                                notif['message'],
                                style: const TextStyle(fontSize: 12, color: Colors.black54, height: 1.3),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${(notif['created_at'] as DateTime).hour}:${(notif['created_at'] as DateTime).minute.toString().padLeft(2, '0')}',
                                style: TextStyle(fontSize: 11, color: Colors.grey.shade400),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
