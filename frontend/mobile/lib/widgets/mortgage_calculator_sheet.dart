import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../core/utils.dart';

class MortgageCalculatorSheet extends StatefulWidget {
  final double propertyPrice;

  const MortgageCalculatorSheet({
    super.key,
    required this.propertyPrice,
  });

  static void show(BuildContext context, double price) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => MortgageCalculatorSheet(propertyPrice: price),
    );
  }

  @override
  State<MortgageCalculatorSheet> createState() => _MortgageCalculatorSheetState();
}

class _MortgageCalculatorSheetState extends State<MortgageCalculatorSheet> {
  late double _price;
  double _downPaymentPercent = 30;
  int _loanTermYears = 20;
  double _interestRate = 7.5;
  String _calculationMethod = 'declining_balance'; // 'declining_balance' or 'fixed_payment'

  @override
  void initState() {
    super.initState();
    _price = widget.propertyPrice > 0 ? widget.propertyPrice : 3000000000;
  }

  double get _downPaymentAmount => (_price * _downPaymentPercent) / 100;
  double get _loanAmount => (_price - _downPaymentAmount).clamp(0, double.infinity);
  int get _totalMonths => _loanTermYears * 12;

  // Calculate first month payment
  double get _firstMonthPayment {
    if (_loanAmount <= 0 || _totalMonths <= 0) return 0;
    final monthlyRate = (_interestRate / 100) / 12;

    if (_calculationMethod == 'declining_balance') {
      final principal = _loanAmount / _totalMonths;
      final interest = _loanAmount * monthlyRate;
      return principal + interest;
    } else {
      // Fixed payment (annuity)
      if (monthlyRate <= 0) return _loanAmount / _totalMonths;
      final factor = (1 + monthlyRate);
      double powVal = 1.0;
      for (int i = 0; i < _totalMonths; i++) {
        powVal *= factor;
      }
      return _loanAmount * (monthlyRate * powVal) / (powVal - 1);
    }
  }

  String formatCurrency(num value) => Formatters.formatPrice(value);

  double get _totalInterest {
    if (_loanAmount <= 0 || _totalMonths <= 0) return 0;
    final monthlyRate = (_interestRate / 100) / 12;

    if (_calculationMethod == 'declining_balance') {
      double totalInt = 0;
      double balance = _loanAmount;
      final principal = _loanAmount / _totalMonths;
      for (int i = 0; i < _totalMonths; i++) {
        totalInt += balance * monthlyRate;
        balance -= principal;
      }
      return totalInt;
    } else {
      final monthlyPay = _firstMonthPayment;
      return (monthlyPay * _totalMonths) - _loanAmount;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Title
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Bảng tính vay mua nhà',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Method Selector
            Container(
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.all(4),
              child: Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _calculationMethod = 'declining_balance'),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        decoration: BoxDecoration(
                          color: _calculationMethod == 'declining_balance'
                              ? Colors.white
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: _calculationMethod == 'declining_balance'
                              ? [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4)]
                              : null,
                        ),
                        child: Text(
                          'Dư nợ giảm dần',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: _calculationMethod == 'declining_balance'
                                ? AppTheme.primaryColor
                                : Colors.grey.shade600,
                          ),
                        ),
                      ),
                    ),
                  ),
                  Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _calculationMethod = 'fixed_payment'),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        decoration: BoxDecoration(
                          color: _calculationMethod == 'fixed_payment'
                              ? Colors.white
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: _calculationMethod == 'fixed_payment'
                              ? [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4)]
                              : null,
                        ),
                        child: Text(
                          'Niên kim (Trả đều)',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: _calculationMethod == 'fixed_payment'
                                ? AppTheme.primaryColor
                                : Colors.grey.shade600,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Result summary banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.blue.shade900, Colors.indigo.shade800],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Ước tính trả tháng đầu tiên',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${formatCurrency(_firstMonthPayment)} / tháng',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Divider(color: Colors.white24, height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Cần vay', style: TextStyle(color: Colors.white70, fontSize: 11)),
                          Text(
                            formatCurrency(_loanAmount),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          const Text('Tổng lãi', style: TextStyle(color: Colors.white70, fontSize: 11)),
                          Text(
                            formatCurrency(_totalInterest),
                            style: TextStyle(color: Colors.amber.shade300, fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Down Payment Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Vốn tự có (Trả trước ${_downPaymentPercent.toInt()}%)',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                ),
                Text(
                  formatCurrency(_downPaymentAmount),
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.primaryColor),
                ),
              ],
            ),
            Slider(
              value: _downPaymentPercent,
              min: 0,
              max: 90,
              divisions: 18,
              activeColor: AppTheme.primaryColor,
              onChanged: (val) => setState(() => _downPaymentPercent = val),
            ),

            // Loan Term Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Thời hạn vay: $_loanTermYears năm ($_totalMonths tháng)',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            Slider(
              value: _loanTermYears.toDouble(),
              min: 1,
              max: 35,
              divisions: 34,
              activeColor: AppTheme.primaryColor,
              onChanged: (val) => setState(() => _loanTermYears = val.toInt()),
            ),

            // Interest rate
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Lãi suất ưu đãi: ${_interestRate.toStringAsFixed(1)}%/năm',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            Slider(
              value: _interestRate,
              min: 4.0,
              max: 15.0,
              divisions: 22,
              activeColor: AppTheme.primaryColor,
              onChanged: (val) => setState(() => _interestRate = val),
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}
