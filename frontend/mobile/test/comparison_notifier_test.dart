import 'package:flutter_test/flutter_test.dart';
import 'package:space247/models/property.dart';
import 'package:space247/providers/comparison_notifier.dart';

void main() {
  group('ComparisonNotifier Tests', () {
    late ComparisonNotifier notifier;

    final mockProperty1 = Property(
      id: '1',
      title: 'Prop 1',
      description: 'Desc',
      propertyType: 'apartment',
      listingType: 'sale',
      price: 1000,
      currency: 'VND',
      areaSqm: 50,
      address: 'Addr',
      city: 'City',
      status: 'active',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final mockProperty2 = Property(
      id: '2',
      title: 'Prop 2',
      description: 'Desc',
      propertyType: 'apartment',
      listingType: 'sale',
      price: 2000,
      currency: 'VND',
      areaSqm: 50,
      address: 'Addr',
      city: 'City',
      status: 'active',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final mockProperty3 = Property(
      id: '3',
      title: 'Prop 3',
      description: 'Desc',
      propertyType: 'apartment',
      listingType: 'sale',
      price: 3000,
      currency: 'VND',
      areaSqm: 50,
      address: 'Addr',
      city: 'City',
      status: 'active',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final mockProperty4 = Property(
      id: '4',
      title: 'Prop 4',
      description: 'Desc',
      propertyType: 'apartment',
      listingType: 'sale',
      price: 4000,
      currency: 'VND',
      areaSqm: 50,
      address: 'Addr',
      city: 'City',
      status: 'active',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    setUp(() {
      notifier = ComparisonNotifier();
    });

    test('Initial state should be empty', () {
      expect(notifier.state, isEmpty);
    });

    test('toggleProperty adds property when not selected', () {
      notifier.toggleProperty(mockProperty1);
      expect(notifier.state.length, 1);
      expect(notifier.state.first.id, '1');
    });

    test('toggleProperty removes property when already selected', () {
      notifier.toggleProperty(mockProperty1);
      notifier.toggleProperty(mockProperty1);
      expect(notifier.state, isEmpty);
    });

    test('toggleProperty throws exception when trying to add more than 3', () {
      notifier.toggleProperty(mockProperty1);
      notifier.toggleProperty(mockProperty2);
      notifier.toggleProperty(mockProperty3);
      
      expect(notifier.state.length, 3);
      
      expect(() => notifier.toggleProperty(mockProperty4), throwsException);
      expect(notifier.state.length, 3);
    });

    test('clearComparison empties state', () {
      notifier.toggleProperty(mockProperty1);
      notifier.clearComparison();
      expect(notifier.state, isEmpty);
    });

    test('isSelected returns correct boolean', () {
      notifier.toggleProperty(mockProperty1);
      expect(notifier.isSelected('1'), isTrue);
      expect(notifier.isSelected('2'), isFalse);
    });
  });
}
