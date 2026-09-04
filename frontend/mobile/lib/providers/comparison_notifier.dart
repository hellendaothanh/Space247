import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:space247_mobile/models/property.dart';

class ComparisonNotifier extends Notifier<List<Property>> {
  @override
  List<Property> build() {
    return [];
  }

  void toggleProperty(Property property) {
    final isSelected = state.any((p) => p.id == property.id);
    if (isSelected) {
      state = state.where((p) => p.id != property.id).toList();
    } else {
      if (state.length < 3) {
        state = [...state, property];
      } else {
        throw Exception('Chỉ có thể so sánh tối đa 3 bất động sản.');
      }
    }
  }

  void clearComparison() {
    state = [];
  }

  bool isSelected(String id) {
    return state.any((p) => p.id == id);
  }
}

final comparisonProvider = NotifierProvider<ComparisonNotifier, List<Property>>(ComparisonNotifier.new);
