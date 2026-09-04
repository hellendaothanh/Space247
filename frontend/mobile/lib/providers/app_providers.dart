import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../services/auth_service.dart';
import '../services/property_service.dart';
import '../models/user.dart';
import '../models/property.dart';
import '../models/search_result.dart';

// Core Api Client Provider
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

// Services
final authServiceProvider = Provider<AuthService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthService(apiClient);
});

final propertyServiceProvider = Provider<PropertyService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PropertyService(apiClient);
});

// Auth State Provider using Notifier
class AuthNotifier extends Notifier<AsyncValue<User?>> {
  @override
  AsyncValue<User?> build() {
    _initUser();
    return const AsyncValue.loading();
  }

  Future<void> _initUser() async {
    try {
      final user = await ref.read(authServiceProvider).getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final res = await ref.read(authServiceProvider).login(email, password);
      state = AsyncValue.data(res.user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  Future<void> logout() async {
    await ref.read(authServiceProvider).logout();
    state = const AsyncValue.data(null);
  }
}

final authStateProvider = NotifierProvider<AuthNotifier, AsyncValue<User?>>(AuthNotifier.new);

// Search and Filter State
class SearchFilterState {
  final String query;
  final String? listingType;
  final String? propertyType;

  const SearchFilterState({
    this.query = '',
    this.listingType,
    this.propertyType,
  });

  SearchFilterState copyWith({
    String? query,
    String? listingType,
    String? propertyType,
    bool clearListingType = false,
    bool clearPropertyType = false,
  }) {
    return SearchFilterState(
      query: query ?? this.query,
      listingType: clearListingType ? null : (listingType ?? this.listingType),
      propertyType: clearPropertyType ? null : (propertyType ?? this.propertyType),
    );
  }
}

class SearchFilterNotifier extends Notifier<SearchFilterState> {
  @override
  SearchFilterState build() {
    return const SearchFilterState();
  }

  void setQuery(String q) {
    state = state.copyWith(query: q);
  }

  void setListingType(String? type) {
    if (state.listingType == type) {
      state = state.copyWith(clearListingType: true);
    } else {
      state = state.copyWith(listingType: type);
    }
  }

  void setPropertyType(String? type) {
    if (state.propertyType == type) {
      state = state.copyWith(clearPropertyType: true);
    } else {
      state = state.copyWith(propertyType: type);
    }
  }

  void resetFilters() {
    state = const SearchFilterState();
  }
}

final searchFilterProvider = NotifierProvider<SearchFilterNotifier, SearchFilterState>(SearchFilterNotifier.new);

// Property Search Results Provider
final searchResultsProvider = FutureProvider<PropertySearchResponse>((ref) async {
  final filter = ref.watch(searchFilterProvider);
  final propertyService = ref.watch(propertyServiceProvider);

  return propertyService.searchProperties(
    query: filter.query.trim().isEmpty ? 'bất động sản' : filter.query.trim(),
    listingType: filter.listingType,
    propertyType: filter.propertyType,
    limit: 25,
  );
});

// Property Detail Provider by ID
final propertyDetailProvider = FutureProvider.family<Property, String>((ref, id) async {
  final propertyService = ref.watch(propertyServiceProvider);
  return propertyService.getPropertyById(id);
});
