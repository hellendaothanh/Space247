# SPEC: Space247 Mobile (Flutter) & README Mermaid Fix

## Goal
1. Fix the Mermaid syntax rendering error in README.md at the Redis node by avoiding nested quotes inside shape parentheses (`Redis[(Redis 7 Cache)]`).
2. Scaffold and implement a clean, robust mobile client for Space247 using Flutter (frontend/mobile/), targeting Android & iOS.
3. Align data models and API services with backend schemas (Property, User, SearchResultItem, PropertySearchResponse).
4. Implement State Management using Flutter Riverpod, HTTP networking via dio, and persistent JWT token storage via flutter_secure_storage.
5. Implement key screens:
   - Home Screen: AI semantic & hybrid search bar, quick filters (Listing Type: Buy/Rent, Property Type), responsive property cards displaying image, price, area, bedroom/bathroom stats, address, and AI match similarity percentage badge.
   - Property Detail Screen: Image header, price & area highlights, specs grid, address, description, and contact action.
   - Auth Screen: User Login with form validation, JWT token persistence, and quick session state.
6. Support dynamic backend endpoint switching (Android emulator http://10.0.2.2:8080/api/v1, iOS simulator / local http://localhost:8080/api/v1, or custom --dart-define).
7. Update README.md with mobile run commands and verify all backend pytest tests pass (57/57) and frontend/web builds cleanly.

## Scope
- Modify: README.md
- Create in frontend/mobile/:
  - Flutter scaffolding (Android & iOS platform runners)
  - pubspec.yaml with Riverpod, Dio, Flutter Secure Storage, Intl, Cached Network Image
  - lib/core/ (constants, api_client, theme, utils)
  - lib/models/ (property.dart, user.dart, search_result.dart)
  - lib/services/ (auth_service.dart, property_service.dart)
  - lib/providers/ (auth_provider.dart, property_provider.dart)
  - lib/screens/ (home_screen.dart, property_detail_screen.dart, login_screen.dart)
  - lib/widgets/ (property_card.dart, search_bar_widget.dart, filter_chips.dart)
  - lib/main.dart
  - test/widget_test.dart

## Verification Plan
1. flutter analyze inside frontend/mobile/ passes with 0 errors.
2. flutter test inside frontend/mobile/ passes.
3. uv run pytest in backend passes 57/57 tests.
4. npm run build in frontend/web builds successfully without errors.
5. Mermaid graph in README.md parses and displays cleanly.
<frozen-after-approval>
spec approved for execution
</frozen-after-approval>
