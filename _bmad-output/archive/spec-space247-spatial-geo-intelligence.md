---
title: 'Spatial & Geo-Intelligence'
type: 'feature'
created: '2026-09-04'
baseline_commit: 'e98f1866257082a9f84b2de6d8dc7958ef795f9d'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users searching for properties need to find homes based on actual commuting time to their workplace or school (Isochrone) rather than simple circular radius, and need to visualize nearby amenity density (schools, hospitals, transit, supermarkets) as a heatmap.

**Approach:** Build a full-stack Spatial & Geo-Intelligence suite using PostGIS geometry/spatial indexing, Isochrone travel-time polygon generation with landmark geocoding, PostGIS `ST_Within` polygon filtering, amenity heatmap POI service, and interactive map UI on both Web (Leaflet + leaflet.heat) and Mobile (Flutter Map Explorer).

**Decisions:**
- Adopt Option A (Hybrid Engine):
  - Primary internal geocoding database for popular landmarks in Vietnam (Keangnam, Bến Thành, Landmark 81, ĐH Bách Khoa, Hồ Gươm, Lotte Center, Nội Bài, Tân Sơn Nhất, v.v.) with Nominatim OpenStreetMap fallback.
  - High-fidelity algorithmic isochrone travel polygon buffer calibrated for Vietnamese traffic speeds (motorcycle: 25-30 km/h, car: 30-40 km/h, transit: 20 km/h, walking: 4.5 km/h) with realistic road network buffer contours.
  - Optional integration with OpenRouteService (`OPENROUTESERVICE_API_KEY`) and Mapbox (`MAPBOX_ACCESS_TOKEN`) when supplied in environment.
  - Amenity POI database (schools, hospitals, transit, supermarkets) with Overpass API fallback.
  - Redis caching for both Isochrone polygons and Amenity Heatmaps with a 1-hour TTL.

## Boundaries & Constraints

**Always:**
- Enable and use PostGIS extension with SRID 4326 Point geometry column (`geom`) and GiST spatial indexing on `Property`.
- Keep lat/lng synchronized with `geom` on create/update.
- Return valid GeoJSON Feature / Polygon in Isochrone responses and GeoJSON Point collections with intensity weights in Heatmap responses.
- Cache Isochrone polygon & POI queries in Redis with a 1-hour TTL.
- Provide graceful fallbacks for geocoding and isochrones so the system functions reliably even without third-party API keys.

**Never:**
- Do not perform full table scans for spatial queries; always leverage the GiST spatial index.
- Do not crash if a landmark name cannot be resolved; return helpful error detail or nearest candidate.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Isochrone search with valid landmark / coordinates | `POST /api/v1/spatial/isochrone-search` with landmark name (e.g., "Keangnam") or `(lat, lng)`, 15 min, "motorcycle" | GeoJSON Isochrone polygon, travel time estimates, matching properties inside polygon | Return empty list if no properties fall within polygon |
| Unknown landmark | `POST /api/v1/spatial/isochrone-search` with non-existent location | 400 Bad Request with detail "Landmark could not be geocoded" | Clear 400 error response |
| Amenity heatmap query | `GET /api/v1/spatial/amenities/heatmap?category=school&bounds=...` | Weighted POI array for heatmap rendering | Fallback to pre-indexed POIs if external OSM API is unreachable |
| Cache hit | Repeated Isochrone / Heatmap query within 1 hour | Cached response from Redis | N/A |

</frozen-after-approval>

## Code Map

- `docker-compose.yml` -- Document/ensure PostGIS extension capability.
- `backend/pyproject.toml` -- Add `geoalchemy2` and `shapely`.
- `backend/src/models/property.py` -- Add `geom = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))` with auto-sync trigger/hook.
- `backend/src/schemas/spatial.py` -- Pydantic DTOs for `IsochroneSearchRequest`, `IsochroneSearchResponse`, `AmenityHeatmapRequest`, `AmenityHeatmapResponse`.
- `backend/src/services/spatial_service.py` -- Geocoding, Isochrone polygon computation, POI generation, Redis caching.
- `backend/src/api/v1/endpoints/spatial.py` -- Endpoints `POST /isochrone-search` and `GET /amenities/heatmap`.
- `backend/src/api/v1/router.py` -- Mount `/spatial` router.
- `backend/tests/api/v1/test_spatial.py` -- Pytest test suite for spatial endpoints.
- `frontend/shared/types.ts` -- Sync spatial TypeScript interfaces.
- `frontend/shared/api-client.ts` -- Add `isochroneSearch` and `getAmenityHeatmap` methods.
- `frontend/web/package.json` -- Install `leaflet.heat` & `@types/leaflet.heat`.
- `frontend/web/src/components/PropertyMapClient.tsx` -- Add Isochrone polygon overlay (`L.geoJSON`), search controls, and amenity heatmap layer (`L.heatLayer`).
- `frontend/mobile/pubspec.yaml` -- Add `flutter_map` & `latlong2`.
- `frontend/mobile/lib/screens/map_explorer_screen.dart` -- Interactive map with isochrone polygon and amenity markers.
- `frontend/mobile/lib/screens/home_screen.dart` -- Link to Map Explorer.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml` -- Add `geoalchemy2` and `shapely` dependencies.
- [x] `backend/src/models/property.py` -- Add PostGIS `geom` column and GiST index.
- [x] `backend/src/schemas/spatial.py` -- Create Pydantic DTOs for Isochrone & Amenity Heatmap.
- [x] `backend/src/services/spatial_service.py` -- Implement geocoding, isochrone polygon generator, and POI heatmap queries with Redis caching.
- [x] `backend/src/api/v1/endpoints/spatial.py` -- Implement `POST /isochrone-search` and `GET /amenities/heatmap` using PostGIS `ST_Within`.
- [x] `backend/src/api/v1/router.py` -- Register spatial router with prefix `/spatial`.
- [x] `backend/tests/api/v1/test_spatial.py` -- Write automated tests for valid isochrone search, unknown landmark 400, heatmap query, and caching.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Export spatial types and API client methods.
- [x] `frontend/web/src/components/PropertyMapClient.tsx` -- Implement Isochrone controls, polygon layer, and Amenity Heatmap toggle.
- [x] `frontend/mobile/lib/screens/map_explorer_screen.dart` -- Implement Mobile Map Explorer with Isochrone sheet and POI toggle.
- [x] `README.md` -- Update spatial API documentation.

**Acceptance Criteria:**
- Given a landmark name or lat/lng and travel duration, when `POST /api/v1/spatial/isochrone-search` is called, then it returns a valid GeoJSON polygon and properties located strictly within that travel zone.
- Given an unknown landmark text, when isochrone search is called, then it returns HTTP 400 with a descriptive error.
- Given a category and bounds, when `GET /api/v1/spatial/amenities/heatmap` is called, then it returns weighted POIs for heatmap rendering.
- On Web, users can select a landmark, choose 5-30 min, pick travel mode (motorcycle/car/walking), see the polygon rendered on Leaflet, and toggle school/hospital/metro/supermarket heatmaps.
- On Mobile, users can open the Map Explorer screen, adjust the isochrone travel slider, and view POIs.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest tests/api/v1/test_spatial.py` -- expected: PASS 100%
- `cd frontend/web && npx tsc --noEmit` -- expected: 0 errors
- `cd frontend/web && npm run build` -- expected: SUCCESS
