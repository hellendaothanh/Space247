import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/rental_property.dart';
import '../providers/app_providers.dart';

class VietQRPaymentScreen extends ConsumerStatefulWidget {
  final DepositTransaction initialTransaction;
  final VoidCallback? onPaymentSuccess;

  const VietQRPaymentScreen({
    super.key,
    required this.initialTransaction,
    this.onPaymentSuccess,
  });

  @override
  ConsumerState<VietQRPaymentScreen> createState() => _VietQRPaymentScreenState();
}

class _VietQRPaymentScreenState extends ConsumerState<VietQRPaymentScreen> {
  late DepositTransaction _transaction;
  Timer? _countdownTimer;
  Timer? _pollingTimer;
  int _secondsLeft = 15 * 60;
  bool _isSuccess = false;
  bool _isExpired = false;

  final NumberFormat _currencyFormat = NumberFormat.currency(
    locale: 'vi_VN',
    symbol: 'đ',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _transaction = widget.initialTransaction;
    _isSuccess = _transaction.status == 'success';
    _isExpired = _transaction.status == 'expired';

    _calculateInitialTimeLeft();
    _startCountdown();
    _startPolling();
  }

  void _calculateInitialTimeLeft() {
    try {
      final expiry = DateTime.parse(_transaction.expiresAt);
      final now = DateTime.now().toUtc();
      final diff = expiry.difference(now).inSeconds;
      _secondsLeft = diff > 0 ? diff : 0;
      if (_secondsLeft == 0 && !_isSuccess) {
        _isExpired = true;
      }
    } catch (_) {
      _secondsLeft = 15 * 60;
    }
  }

  void _startCountdown() {
    if (_isSuccess || _isExpired) return;

    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_secondsLeft <= 1) {
          _secondsLeft = 0;
          _isExpired = true;
          timer.cancel();
          _pollingTimer?.cancel();
        } else {
          _secondsLeft -= 1;
        }
      });
    });
  }

  void _startPolling() {
    if (_isSuccess || _isExpired) return;

    _pollingTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
      if (!mounted || _isSuccess || _isExpired) {
        timer.cancel();
        return;
      }

      try {
        final latest = await ref
            .read(hostServiceProvider)
            .getDepositTransaction(_transaction.referenceCode);

        if (!mounted) return;

        setState(() {
          _transaction = latest;
          if (latest.status == 'success') {
            _isSuccess = true;
            _countdownTimer?.cancel();
            timer.cancel();
            widget.onPaymentSuccess?.call();
          } else if (latest.status == 'expired') {
            _isExpired = true;
            _countdownTimer?.cancel();
            timer.cancel();
          }
        });
      } catch (_) {
        // Silently ignore temporary network poll hiccups
      }
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _pollingTimer?.cancel();
    super.dispose();
  }

  void _copyToClipboard(String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Đã sao chép $label'),
        duration: const Duration(seconds: 2),
        backgroundColor: const Color(0xFF1E293B),
      ),
    );
  }

  String _formatDuration(int totalSeconds) {
    final minutes = totalSeconds ~/ 60;
    final seconds = totalSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Thanh Toán Đặt Cọc VietQR'),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF0F172A),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            if (_isSuccess) _buildSuccessView() else if (_isExpired) _buildExpiredView() else _buildActivePaymentView(),
          ],
        ),
      ),
    );
  }

  Widget _buildActivePaymentView() {
    return Column(
      children: [
        // Countdown banner
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.amber.shade50,
            border: Border.all(color: Colors.amber.shade200),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.timer_outlined, color: Colors.amber.shade800, size: 20),
              const SizedBox(width: 8),
              Text(
                'Mã QR hết hạn trong: ',
                style: TextStyle(fontSize: 13, color: Colors.amber.shade900),
              ),
              Text(
                _formatDuration(_secondsLeft),
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.amber.shade900,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // QR Code Container
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 16,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: CachedNetworkImage(
                  imageUrl: _transaction.vietqrUrl,
                  width: 260,
                  height: 260,
                  fit: BoxFit.contain,
                  placeholder: (context, url) => const SizedBox(
                    width: 260,
                    height: 260,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                  errorWidget: (context, url, error) => const SizedBox(
                    width: 260,
                    height: 260,
                    child: Center(child: Icon(Icons.broken_image, size: 48, color: Colors.grey)),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Đang chờ xác nhận thanh toán...',
                    style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Transfer Information Card
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Thông tin chuyển khoản',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF0F172A),
                ),
              ),
              const Divider(height: 24),
              _buildInfoRow(
                'Số tiền cọc',
                _currencyFormat.format(_transaction.amount),
                isHighlight: true,
                onCopy: () => _copyToClipboard(_transaction.amount.toStringAsFixed(0), 'Số tiền'),
              ),
              const SizedBox(height: 12),
              _buildInfoRow(
                'Nội dung CK',
                _transaction.referenceCode,
                onCopy: () => _copyToClipboard(_transaction.referenceCode, 'Nội dung chuyển khoản'),
              ),
              const SizedBox(height: 12),
              _buildInfoRow('Cổng thanh toán', 'Napas 247 QuickLink (VietQR)'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isHighlight = false, VoidCallback? onCopy}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 13, color: Color(0xFF64748B)),
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: isHighlight ? 16 : 14,
                fontWeight: isHighlight ? FontWeight.bold : FontWeight.w600,
                color: isHighlight ? const Color(0xFF2563EB) : const Color(0xFF0F172A),
              ),
            ),
            if (onCopy != null) ...[
              const SizedBox(width: 6),
              GestureDetector(
                onTap: onCopy,
                child: const Icon(Icons.copy, size: 16, color: Color(0xFF2563EB)),
              ),
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildSuccessView() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Color(0xFFECFDF5),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.check_circle,
              color: Color(0xFF059669),
              size: 64,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Đặt Cọc Thành Công!',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Phòng trọ đã được giữ chỗ thành công cho bạn với mã giao dịch ${_transaction.referenceCode}.',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 14, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2563EB),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: const Text('Hoàn tất & Quay lại', style: TextStyle(color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExpiredView() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.error_outline,
            color: Color(0xFFDC2626),
            size: 64,
          ),
          const SizedBox(height: 20),
          const Text(
            'Mã QR Đã Hết Hạn',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Giao dịch giữ chỗ 15 phút đã quá hạn. Vui lòng quay lại màn hình yêu cầu để tạo giao dịch mới.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton(
              onPressed: () => Navigator.of(context).pop(false),
              style: OutlinedButton.styleFrom(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: const Text('Đóng'),
            ),
          ),
        ],
      ),
    );
  }
}
