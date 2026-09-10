# SPEC: Space247 Property Bookmarks / Favorites

## Goal
Implement a complete end-to-end Property Favorites/Bookmarks feature for Space247 across Backend, Frontend Web, and Mobile Flutter:
1. Backend:
   - Database model & table `favorite_properties` (many-to-many junction table between `user_id` and `property_id` with unique constraint and timestamps).
   - Alembic migration `0003_add_favorite_properties.py` supporting both offline and idempotent online modes.
   - Endpoints:
     - `POST /api/v1/properties/{property_id}/favorite` (Toggle favorite: returns `{ "property_id": str, "is_favorite": bool, "message": str }`).
     - `GET /api/v1/properties/favorites` (List bookmarked properties for the authenticated user, ordered by favorited_at desc).
   - Cache invalidation: keep consistent and fast.
2. Frontend Web:
   - Heart icon button on every `PropertyCard` allowing quick toggle.
   - New dedicated page `/favorites` displaying user saved listings, empty state, and direct navigation.
   - Navigation links to `/favorites` in Navbar and User Profile dropdown.
   - Shared client & types in `frontend/shared/` updated (`ToggleFavoriteResponse`, `getFavoriteProperties`, `toggleFavoriteProperty`).
3. Mobile Flutter:
   - Add Favorite models, service methods (`toggleFavorite`, `getFavorites`), and Riverpod state notifier (`favoritePropertiesProvider`).
   - Heart bookmark button on `PropertyCard` in Mobile.
   - Dedicated Favorites Screen (`favorites_screen.dart`) accessible from bottom navigation or AppBar.
4. Verification:
   - Backend automated tests (`tests/test_favorites.py`) covering toggle (add/remove), unauthorized protection, listing favorites, and idempotent migration tests.
   - Verify `uv run pytest` passes 100%.
   - Verify `npm run build` in `frontend/web` passes 100%.
   - Verify `flutter analyze` and `flutter test` in `frontend/mobile` pass 100%.
<frozen-after-approval>
spec approved for execution
</frozen-after-approval>
