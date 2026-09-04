import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:space247/models/property.dart';

class ComparisonNotifier extends StateNotifier<List<Property>> {
  ComparisonNotifier() : super([]);

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

final comparisonProvider = StateNotifierProvider<ComparisonNotifier, List<Property>>((ref) {
  return ComparisonNotifier();
});
