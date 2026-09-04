import 'package:intl/intl.dart';

class Formatters {
  static final _currencyFormat = NumberFormat('#,###', 'vi_VN');

  static String formatPrice(num price, {String currency = 'VND'}) {
    if (currency.toUpperCase() == 'VND') {
      if (price >= 1000000000) {
        final billions = price / 1000000000;
        return '${billions.toStringAsFixed(billions.truncateToDouble() == billions ? 0 : 1)} tỷ VND';
      } else if (price >= 1000000) {
        final millions = price / 1000000;
        return '${millions.toStringAsFixed(millions.truncateToDouble() == millions ? 0 : 1)} triệu VND';
      }
    }
    return '${_currencyFormat.format(price)} $currency';
  }

  static String formatArea(num sqm) {
    return '${sqm.toStringAsFixed(sqm.truncateToDouble() == sqm ? 0 : 1)} m²';
  }

  static String propertyTypeLabel(String type) {
    switch (type.toLowerCase()) {
      case 'apartment':
        return 'Chung cư';
      case 'house':
        return 'Nhà phố';
      case 'villa':
        return 'Biệt thự';
      case 'land':
        return 'Đất nền';
      case 'commercial':
        return 'Thương mại / Mặt bằng';
      default:
        return type;
    }
  }

  static String listingTypeLabel(String type) {
    switch (type.toLowerCase()) {
      case 'sale':
        return 'Mua bán';
      case 'rent':
        return 'Cho thuê';
      default:
        return type;
    }
  }
}
