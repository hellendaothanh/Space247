---
title: 'Two-Sided Host and Tenant Rental Subsystem'
type: 'feature'
created: '2026-09-07'
status: 'done'
baseline_commit: '877bb3145d3cb1d13bfa174cc8126d46dc370472'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The previous rental module treated boarding houses and serviced apartments as flat individual properties, mixing entire complexes with individual rooms, cluttering the discovery interface with 14 raw controls, lacking daily homestay distinction, and having no dedicated landlord management or room viewing appointment workflow.

**Approach:** Restructure the rental subsystem into a two-way Host and Tenant platform with dedicated models: building/property-level (`rental_properties`) holding general location, property model (boarding house, serviced apartment, homestay), shared utilities and rules; room-level (`rental_units`) holding unit number, floor, area, monthly rent/deposit, status (available, occupied, reserved), furnishing, and photos; and inquiry/booking appointments (`rental_inquiries`) connecting tenants and hosts. Redesign the tenant discovery UI with a clean search bar and advanced filter modal, build the landlord dashboard (`/host/rentals`) with room toggle and multi-step creation wizard, implement authenticated host & tenant APIs, and provide full mobile support and test coverage.

## Boundaries & Constraints

**Always:**
- Keep existing `properties` (sale/rent) backward compatible; provide unified/dedicated discovery for rentals under `/rentals` and `/api/v1/rentals`.
- Distinguish monthly rental models (`boarding_house`, `serviced_apartment`) with VND/tháng and daily rental (`homestay`) with VND/đêm.
- Require role `host`, `agent`, `admin`, or `superadmin` for Host management endpoints (`/api/v1/host/*`). Add `HOST = "host"` to `UserRole` enum so property owners can register/act as dedicated hosts.
- Guard against invalid operations: tenants cannot book occupied rooms; hosts can only modify their own properties/units unless admin.
- Maintain PostGIS spatial indexing (`geom`) and 100% test pass on backend, frontend web build, and mobile analyze.

**Never:**
- Break legacy `Property` endpoints or drop existing database columns.
- Display 14 horizontal inline form inputs on web or mobile search screens.
- Allow anonymous users to toggle unit status or view landlord financial statistics.

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0009_two_sided_rental_system.py`: Alembic migration creating `rental_properties`, `rental_units`, and `rental_inquiries` tables, indexes, and foreign keys.
- `backend/src/models/user.py`: Add `HOST = "host"` to `UserRole` enum.
- `backend/src/models/rental_property.py`: SQLAlchemy models `RentalProperty`, `RentalUnit`, `RentalInquiry`.
- `backend/src/models/__init__.py`: Export new rental models so Alembic and queries discover them.
- `backend/src/schemas/rental_management.py`: Pydantic schemas for RentalProperty, RentalUnit, RentalInquiry, filters, creation, and updates.
- `backend/src/api/deps.py`: Add `get_current_host_user` dependency (accepting `host`, `agent`, `admin`, `superadmin`).
- `backend/src/api/v1/endpoints/rentals.py`: Tenant endpoints: search/list, property details, unit inquiry booking, and tenant inquiry history.
- `backend/src/api/v1/endpoints/host.py`: Host endpoints: property CRUD, unit management, unit status toggle, landlord dashboard stats, and inquiry management.
- `backend/src/api/v1/router.py`: Register `/rentals` and `/host` routers.
- `backend/tests/test_rental_two_sided.py`: Pytest suite covering full host creation, unit management, tenant discovery, and inquiry booking flow.
- `frontend/shared/types.ts`: TypeScript interfaces for `RentalProperty`, `RentalUnit`, `RentalInquiry`, filters, and DTOs.
- `frontend/shared/api-client.ts`: Shared API client methods for tenant and host operations.
- `frontend/web/src/app/rentals/page.tsx`: Redesigned tenant discovery page with clean search bar, quick pills, modal/drawer filters, and card grid.
- `frontend/web/src/app/rentals/[id]/page.tsx`: Rental property & units detail page with available units list and "Đặt lịch xem phòng" modal.
- `frontend/web/src/app/host/rentals/page.tsx`: Landlord Dashboard with occupancy stats, unit quick-toggle, recent inquiries list, and properties list.
- `frontend/web/src/app/host/rentals/new/page.tsx`: Multi-step wizard form for registering a new rental property / building and initial units.
- `frontend/web/src/components/Navbar.tsx`: Add link to "Kênh chủ nhà" / "Đăng tin cho thuê" when logged in.
- `frontend/mobile/lib/models/rental_property.dart`: Dart models for `RentalProperty`, `RentalUnit`, `RentalInquiry`.
- `frontend/mobile/lib/services/rental_service.dart`: Mobile service for tenant discovery and inquiries.
- `frontend/mobile/lib/widgets/search_and_filter.dart`: Clean search bar & filter drawer replacing cumbersome 14-input dropdowns.
- `docs/database-design.md`, `docs/api-specs.md`: Update architecture documentation with the new two-sided ERD and API specifications.

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/models/user.py` & `backend/src/models/rental_property.py`: Add `UserRole.HOST`, define `RentalProperty`, `RentalUnit`, `RentalInquiry` with PostGIS geom and foreign keys.
- [x] `backend/migrations/versions/0009_two_sided_rental_system.py`: Migration creating the 3 tables, foreign keys, and indexes. Update migration tests in `backend/tests/test_alembic_migrations.py`.
- [x] `backend/src/schemas/rental_management.py`: Pydantic request/response models.
- [x] `backend/src/api/deps.py`: Add `get_current_host_user` dependency.
- [x] `backend/src/api/v1/endpoints/rentals.py` & `host.py`: Implement tenant and host endpoints, wire into `router.py`.
- [x] `backend/tests/test_rental_two_sided.py`: Pytest suite testing tenant search, inquiry creation, host property/unit creation, status toggle, and permissions.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts`: TypeScript DTOs and API methods.
- [x] `frontend/web/src/app/rentals/page.tsx`: Redesigned clean tenant discovery page with search bar, model pills, and filter modal.
- [x] `frontend/web/src/app/rentals/[id]/page.tsx`: Detailed building and units view with booking CTA modal.
- [x] `frontend/web/src/app/host/rentals/page.tsx` & `frontend/web/src/app/host/rentals/new/page.tsx`: Host dashboard with 1-click unit status toggle, KPI stats, inquiry manager, and multi-step registration wizard.
- [x] `frontend/mobile/lib/models/rental_property.dart` & `frontend/mobile/lib/widgets/search_and_filter.dart`: Mobile models, clean search UI, and test updates in `widget_test.dart`.
- [x] `docs/database-design.md` & `docs/api-specs.md`: Document ERD and REST API endpoints.

**Acceptance Criteria:**
- Given a registered host/agent, when they access `/host/rentals`, they can create a building with multiple units and toggle unit status between available/occupied in 1 click.
- Given a tenant on `/rentals`, they see a clean modern search bar with category pills (Phòng trọ, Căn hộ dịch vụ, Homestay) and advanced filter drawer, without 14 horizontal inline controls.
- Given an available unit, when a tenant submits a viewing appointment, an inquiry is created with status `pending` and appears in the host's inquiry inbox.
- All backend pytest tests pass (100%), web TypeScript and `npm run build` pass with 0 errors, and `flutter analyze` passes with 0 issues.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest` -- expected: All backend tests pass including new rental two-sided tests.
- `npx tsc --noEmit && npm run build` (in frontend/web) -- expected: 0 compilation or type errors.
- `flutter analyze && flutter test` (in frontend/mobile) -- expected: 0 issues, all tests pass.
