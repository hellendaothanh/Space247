import 'package:flutter/material.dart';
import '../models/property.dart';
const rentalTypeLabels = { 'room': 'Phòng trọ', 'serviced_apartment': 'Căn hộ dịch vụ', 'house_share': 'Ở ghép', 'entire_house': 'Nhà nguyên căn' };
const rentalRuleLabels = { 'curfew': 'Có giờ đóng cửa', 'private_bathroom': 'Phòng tắm riêng', 'allow_pets': 'Cho nuôi thú cưng', 'has_mezzanine': 'Có gác lửng', 'has_washing_machine': 'Máy giặt', 'live_with_owner': 'Ở cùng chủ', 'has_elevator': 'Thang máy', 'fingerprint_lock': 'Khóa vân tay' };
class RentalBadges extends StatelessWidget {
 final Property property;
 const RentalBadges({super.key, required this.property});
 @override
 Widget build(BuildContext context) {
  if (property.listingType != 'rent') return const SizedBox.shrink();
  return Wrap(spacing: 8, children: [
   if (property.rentalType != null) Text(rentalTypeLabels[property.rentalType] ?? property.rentalType!),
   if (property.rentalRules?['has_mezzanine'] == true) const Text('Có gác lửng'),
   if (property.rentalRules?['allow_pets'] == true) const Text('Cho nuôi thú cưng'),
  ]);
 }
}
class RentalDetails extends StatelessWidget {
 final Property property;
 const RentalDetails({super.key, required this.property});
 @override
 Widget build(BuildContext context) {
  if (property.listingType != 'rent') return const SizedBox.shrink();
  final c = property.rentalCosts ?? <String, dynamic>{};
  final r = property.rentalRules ?? <String, dynamic>{};
  final waterUnit = c['water_unit'] == 'per_person' ? 'đ/người/tháng' : c['water_unit'] == 'per_m3' ? 'đ/m³' : 'chưa rõ đơn vị';
  final costs = { 'electricity_per_kwh': 'Điện (đ/kWh)', 'water_cost': 'Nước ($waterUnit)', 'parking_fee_monthly': 'Gửi xe (đ/tháng)', 'service_fee_monthly': 'Dịch vụ (đ/tháng)', 'deposit_months': 'Cọc (tháng)' };
  return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
   const Text('Chi phí & nội quy thuê', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
   RentalBadges(property: property),
   for (final entry in costs.entries) Text('${entry.value}: ${c[entry.key] ?? "Chưa cung cấp"}'),
   Text('Tiền đặt cọc: ${property.depositAmount == null ? "Chưa cung cấp" : "${property.depositAmount} đ"}'),
   Text('Tính điện: ${c["electricity_billing"] == "state_rate" ? "Giá nhà nước" : c["electricity_billing"] == "fixed" ? "Đơn giá cố định" : "Chưa cung cấp"}'),
   for (final entry in rentalRuleLabels.entries) Text('${entry.value}: ${r[entry.key] == null ? "Chưa cung cấp" : r[entry.key] == true ? "Có" : "Không"}'),
   if (r['curfew'] != false) Text('Giờ đóng cửa: ${r["curfew_time"] ?? "Chưa cung cấp"}'),
   Text('Số người tối đa: ${r["max_occupants"] ?? "Chưa cung cấp"}'),
   const Text('Điện, nước phụ thuộc lượng dùng hoặc số người. Chi phí chưa cung cấp không có nghĩa là miễn phí.'),
  ])));
 }
}
