import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:space247_mobile/models/user.dart';
import 'package:space247_mobile/models/property.dart';
import 'package:space247_mobile/models/search_result.dart';
import 'package:space247_mobile/widgets/property_card.dart';
import 'package:space247_mobile/core/utils.dart';

void main() {
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
        MaterialApp(
          home: Scaffold(
            body: PropertyCard(item: searchItem),
          ),
        ),
      );

      expect(find.text('Căn hộ River Gate 2PN'), findsOneWidget);
      expect(find.text('18 triệu VND'), findsOneWidget);
      expect(find.text('92% match'), findsOneWidget);
      expect(find.text('CHO THUÊ'), findsOneWidget);
    });
  });
}
