import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../services/auth_service.dart';
import '../services/property_service.dart';
import '../services/host_service.dart';
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

final hostServiceProvider = Provider<HostService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return HostService(apiClient);
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

  void setUser(User? user) {
    state = AsyncValue.data(user);
  }
}

final authStateProvider = NotifierProvider<AuthNotifier, AsyncValue<User?>>(AuthNotifier.new);

// Search and Filter State
class SearchFilterState {
  final String query;
  final String? listingType;
  final String? propertyType;
  final Map<String, dynamic> rentalFilters;

  const SearchFilterState({
    this.query = '',
    this.listingType,
    this.propertyType,
    this.rentalFilters = const {},
  });

  SearchFilterState copyWith({
    String? query,
    String? listingType,
    String? propertyType,
    Map<String, dynamic>? rentalFilters,
    bool clearListingType = false,
    bool clearPropertyType = false,
  }) {
    return SearchFilterState(
      query: query ?? this.query,
      rentalFilters: rentalFilters ?? this.rentalFilters,
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
      state = state.copyWith(clearListingType: true, rentalFilters: {});
    } else {
      state = state.copyWith(listingType: type, rentalFilters: type == "rent" ? state.rentalFilters : {});
    }
  }

  void setPropertyType(String? type) {
    if (state.propertyType == type) {
      state = state.copyWith(clearPropertyType: true);
    } else {
      state = state.copyWith(propertyType: type);
    }
  }

  void setRentalFilter(String key, dynamic value) {
    final next = Map<String, dynamic>.from(state.rentalFilters);
    if (value == null) { next.remove(key); } else { next[key] = value; }
    state = state.copyWith(listingType: "rent", rentalFilters: next);
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
    rentalFilters: filter.rentalFilters,
    limit: 25,
  );
});

// Property Detail Provider by ID
final propertyDetailProvider = FutureProvider.family<Property, String>((ref, id) async {
  final propertyService = ref.watch(propertyServiceProvider);
  return propertyService.getPropertyById(id);
});

// Favorite Properties Provider
final favoritePropertiesProvider = FutureProvider<List<Property>>((ref) async {
  final authState = ref.watch(authStateProvider);
  final user = authState.value;
  if (user == null) {
    return [];
  }
  final propertyService = ref.watch(propertyServiceProvider);
  return propertyService.getFavorites();
});

// Set of favorite property IDs for fast O(1) bookmark lookup
class FavoriteIdsNotifier extends Notifier<Set<String>> {
  @override
  Set<String> build() {
    ref.listen<AsyncValue<List<Property>>>(
      favoritePropertiesProvider,
      (previous, next) {
        next.whenData((list) {
          state = list.map((p) => p.id).toSet();
        });
      },
    );

    final favAsync = ref.watch(favoritePropertiesProvider);
    return favAsync.value?.map((p) => p.id).toSet() ?? <String>{};
  }

  Future<bool> toggleFavorite(String propertyId) async {
    final propertyService = ref.read(propertyServiceProvider);
    final isCurrentlyFav = state.contains(propertyId);

    // Optimistic UI state update
    if (isCurrentlyFav) {
      state = Set.from(state)..remove(propertyId);
    } else {
      state = Set.from(state)..add(propertyId);
    }

    try {
      final res = await propertyService.toggleFavorite(propertyId);
      if (res.isFavorite) {
        state = Set.from(state)..add(propertyId);
      } else {
        state = Set.from(state)..remove(propertyId);
      }
      ref.invalidate(favoritePropertiesProvider);
      return res.isFavorite;
    } catch (e) {
      // Revert on error
      if (isCurrentlyFav) {
        state = Set.from(state)..add(propertyId);
      } else {
        state = Set.from(state)..remove(propertyId);
      }
      rethrow;
    }
  }
}

final favoriteIdsProvider = NotifierProvider<FavoriteIdsNotifier, Set<String>>(FavoriteIdsNotifier.new);
