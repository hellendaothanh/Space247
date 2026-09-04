import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:space247_mobile/models/property.dart';
import 'package:space247_mobile/providers/comparison_notifier.dart';

void main() {
  group('ComparisonNotifier Tests', () {
    late ProviderContainer container;

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
      createdAt: DateTime.now().toIso8601String(),
      updatedAt: DateTime.now().toIso8601String(),
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
      createdAt: DateTime.now().toIso8601String(),
      updatedAt: DateTime.now().toIso8601String(),
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
      createdAt: DateTime.now().toIso8601String(),
      updatedAt: DateTime.now().toIso8601String(),
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
      createdAt: DateTime.now().toIso8601String(),
      updatedAt: DateTime.now().toIso8601String(),
    );

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('Initial state should be empty', () {
      final state = container.read(comparisonProvider);
      expect(state, isEmpty);
    });

    test('toggleProperty adds property when not selected', () {
      container.read(comparisonProvider.notifier).toggleProperty(mockProperty1);
      final state = container.read(comparisonProvider);
      expect(state.length, 1);
      expect(state.first.id, '1');
    });

    test('toggleProperty removes property when already selected', () {
      final notifier = container.read(comparisonProvider.notifier);
      notifier.toggleProperty(mockProperty1);
      notifier.toggleProperty(mockProperty1);
      final state = container.read(comparisonProvider);
      expect(state, isEmpty);
    });

    test('toggleProperty throws exception when trying to add more than 3', () {
      final notifier = container.read(comparisonProvider.notifier);
      notifier.toggleProperty(mockProperty1);
      notifier.toggleProperty(mockProperty2);
      notifier.toggleProperty(mockProperty3);

      expect(container.read(comparisonProvider).length, 3);
      expect(() => notifier.toggleProperty(mockProperty4), throwsException);
      expect(container.read(comparisonProvider).length, 3);
    });

    test('clearComparison empties state', () {
      final notifier = container.read(comparisonProvider.notifier);
      notifier.toggleProperty(mockProperty1);
      notifier.clearComparison();
      expect(container.read(comparisonProvider), isEmpty);
    });

    test('isSelected returns correct boolean', () {
      final notifier = container.read(comparisonProvider.notifier);
      notifier.toggleProperty(mockProperty1);
      expect(notifier.isSelected('1'), isTrue);
      expect(notifier.isSelected('2'), isFalse);
    });
  });
}

