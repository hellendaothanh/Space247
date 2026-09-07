import 'package:flutter/material.dart';
import 'package:space247_mobile/widgets/rental_details.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:space247_mobile/models/user.dart';
import 'package:space247_mobile/models/property.dart';
import 'package:space247_mobile/models/rental_property.dart';
import 'package:space247_mobile/models/search_result.dart';
import 'package:space247_mobile/models/favorite.dart';
import 'package:space247_mobile/widgets/property_card.dart';
import 'package:space247_mobile/core/utils.dart';
import 'package:space247_mobile/providers/app_providers.dart';

class FakeFavoriteIdsNotifier extends FavoriteIdsNotifier {
  @override
  Set<String> build() => <String>{};
}

void main() {
  test('Rental metadata preserves zero, false, unknown and deposit units', () {
    final property = Property.fromJson({'id': 'rent', 'listing_type': 'rent', 'price': 3000000, 'rental_type': 'room', 'rental_costs': {'deposit_months': 2, 'service_fee_monthly': 0}, 'rental_rules': {'allow_pets': false, 'has_mezzanine': true}});
    expect(property.depositAmount, 6000000);
    expect(property.toJson()['rental_costs']['service_fee_monthly'], 0);
    expect(property.toJson()['rental_rules']['allow_pets'], false);
    expect(property.rentalCosts?['water_cost'], isNull);
  });
  test('Two-sided RentalProperty and RentalUnit parse correctly', () {
    final unit = RentalUnit.fromJson({
      'id': 'u1',
      'property_id': 'p1',
      'unit_number': 'P.101',
      'area_sqm': 25.0,
      'price': 3500000.0,
      'status': 'available',
      'has_mezzanine': true,
      'has_private_bathroom': true,
    });
    expect(unit.isAvailable, true);
    expect(unit.unitNumber, 'P.101');

    final prop = RentalProperty.fromJson({
      'id': 'p1',
      'host_id': 'h1',
      'name': 'Nhà Trọ Xanh',
      'property_model': 'boarding_house',
      'address': '10 Tạ Quang Bửu',
      'city': 'Hà Nội',
      'units': [unit.toJson()],
    });
    expect(prop.units.length, 1);
    expect(prop.priceUnitLabel, '/tháng');
  });
  testWidgets('Rental details display fee units and only known positive badges', (tester) async {
    final property = Property.fromJson({'id': 'rent', 'listing_type': 'rent', 'price': 3000000, 'rental_type': 'room', 'rental_costs': {'deposit_months': 0, 'service_fee_monthly': 0}, 'rental_rules': {'allow_pets': false, 'has_mezzanine': true}});
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(child: RentalDetails(property: property)))));
    expect(find.text('Có gác lửng'), findsOneWidget);
    expect(find.text('Cho nuôi thú cưng'), findsNothing);
    expect(find.text('Cho nuôi thú cưng: Không'), findsOneWidget);
    expect(find.text('Dịch vụ (đ/tháng): 0'), findsOneWidget);
    expect(find.text('Điện (đ/kWh): Chưa cung cấp'), findsOneWidget);
  });
  group('Data Models & Formatters Test', () {
    test('User model parses correctly', () {
      final json = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'email': 'user@space247.vn',
        'full_name': 'Nguyen Van A',
        'phone': '0901234567',
        'role': 'user',
        'is_active': true,
        'created_at': '2026-09-01T10:00:00Z',
      };

      final user = User.fromJson(json);
      expect(user.id, '123e4567-e89b-12d3-a456-426614174000');
      expect(user.email, 'user@space247.vn');
      expect(user.fullName, 'Nguyen Van A');
      expect(user.isActive, true);
    });

    test('Property and SearchResultItem models parse correctly', () {
      final propertyJson = {
        'id': 'p1-1234',
        'title': 'Căn hộ Masteri Thảo Điền 2PN',
        'description': 'Căn hộ view sông Sài Gòn thoáng mát',
        'property_type': 'apartment',
        'listing_type': 'sale',
        'price': 4500000000,
        'currency': 'VND',
        'area_sqm': 72.5,
        'num_bedrooms': 2,
        'num_bathrooms': 2,
        'address': '159 Xa Lộ Hà Nội',
        'city': 'TP. Hồ Chí Minh',
        'status': 'active',
      };

      final resultJson = {
        'property': propertyJson,
        'similarity_score': 0.885,
        'rrf_score': 0.032,
        'vector_rank': 1,
        'fts_rank': 2,
      };

      final searchItem = SearchResultItem.fromJson(resultJson);
      expect(searchItem.property.title, 'Căn hộ Masteri Thảo Điền 2PN');
      expect(searchItem.property.price, 4500000000.0);
      expect(searchItem.similarityScore, 0.885);
      expect(searchItem.similarityPercentage, 89);
    });

    test('Formatters format currency and areas accurately', () {
      expect(Formatters.formatPrice(4500000000), '4.5 tỷ VND');
      expect(Formatters.formatPrice(15000000), '15 triệu VND');
      expect(Formatters.formatPrice(2500, currency: 'USD'), '2.500 USD');
      expect(Formatters.formatArea(72.5), '72.5 m²');
      expect(Formatters.propertyTypeLabel('apartment'), 'Chung cư');
      expect(Formatters.listingTypeLabel('sale'), 'Mua bán');
    });

    test('ToggleFavoriteResponse model parses correctly', () {
      final json = {
        'property_id': 'p1-1234',
        'is_favorite': true,
        'message': 'Đã lưu bất động sản vào danh sách yêu thích',
      };
      final res = ToggleFavoriteResponse.fromJson(json);
      expect(res.propertyId, 'p1-1234');
      expect(res.isFavorite, true);
      expect(res.message, 'Đã lưu bất động sản vào danh sách yêu thích');
    });
  });

  group('Widget Tests', () {
    testWidgets('PropertyCard renders title, price, and match badge', (tester) async {
      final property = Property(
        id: 'p1',
        title: 'Căn hộ River Gate 2PN',
        description: 'Đầy đủ nội thất cao cấp',
        propertyType: 'apartment',
        listingType: 'rent',
        price: 18000000,
        currency: 'VND',
        areaSqm: 68.0,
        numBedrooms: 2,
        numBathrooms: 2,
        address: '151 Ben Van Don',
        city: 'TP. Hồ Chí Minh',
        status: 'active',
      );

      final searchItem = SearchResultItem(
        property: property,
        similarityScore: 0.92,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            favoriteIdsProvider.overrideWith(FakeFavoriteIdsNotifier.new),
          ],
          child: MaterialApp(
            home: Scaffold(
              body: PropertyCard(item: searchItem),
            ),
          ),
        ),
      );
      await tester.pump();

      expect(find.text('Căn hộ River Gate 2PN'), findsOneWidget);
      expect(find.text('18 triệu VND/tháng'), findsOneWidget);
      expect(find.text('92% match'), findsOneWidget);
      expect(find.text('CHO THUÊ'), findsOneWidget);
    });
  });
}
