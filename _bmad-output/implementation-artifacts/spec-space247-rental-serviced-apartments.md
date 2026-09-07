---
title: 'Rental and Serviced Apartments'
type: 'feature'
created: '2026-09-07'
status: 'done'
baseline_commit: '8c9152b6437a9baf813c58e1853197412665cd40'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Generic rent listings exist but lack structured room categories, transparent expenses, rules, and matching rental discovery across web, mobile, and AI.

**Approach:** Extend the existing property contract with rental metadata, exact filters, rental-aware embeddings/chat, a web rental catalog, posting controls, and mobile rental discovery/details.

## Boundaries & Constraints

**Always:** Preserve existing listings, authorization, caching, pagination, and 768-dimensional vectors. Use sale/rent and room/serviced_apartment/house_share/entire_house. Store requested costs and rules in nullable JSONB. Missing values mean unknown; zero and false remain meaningful. Prices are monthly VND for rentals. Interpret max_deposit in months. Deposit amount equals monthly rent times deposit_months; variable electricity/water expenses cannot be totaled without consumption/person counts. Keep rental metadata optional for legacy listings. Reuse existing sale/rent types.

**Never:** Recreate the existing listing_type column, invent amenities, equate unknown charges with free service, deploy, or migrate a live database during implementation.

**Approved decisions:** Add optional electricity_billing (state_rate | fixed) to rental_costs for exact state-tariff filtering. Geocode landmarks, resolving Bách Khoa to Hanoi University of Science and Technology, and filter with PostGIS within a default 3.0 km radius; fall back to semantic location search when coordinates cannot be resolved. Add optional has_washing_machine, live_with_owner, has_elevator, fingerprint_lock booleans to rental_rules. Migration 0008 alters the existing listing_type default without duplicating the column. The user approved this complete cross-layer scope on 2026-09-07.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Rental record | Valid subtype, costs, rules | Create/read/update round-trip metadata | Invalid enums, negative costs/deposits, invalid time or occupancy return 422 |
| Exact filters | Rent, subtype, pets, mezzanine, deposit ceiling | Only matching active rentals; predicates apply before ranking/limit | Preserve false/zero; missing JSON keys do not satisfy explicit predicates |
| Legacy record | No rental metadata | Listing remains readable; unknown charges labeled unavailable | No fabricated badges |
| Update | Rental expenses/rules change | Embedding refresh and cache invalidation | Preserve omitted fields; explicit null clears optional metadata |
| Sale transition | Rental changed to sale | Clear rental-only metadata; hide rental UI | Do not mutate unrelated fields |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0001_initial_pgvector_properties.py`: listing_type already exists; 0007 is current head.
- `backend/src/models/property.py`, `backend/src/schemas/property.py`: persistence and inherited create/response/detail DTOs; update and search schemas separate.
- `backend/src/api/v1/endpoints/properties.py`, `search.py`: list, CRUD, hybrid and vector filters; keep existing auth/cache behavior.
- `backend/src/services/embedding.py`, `chat_assistant.py`, `backend/src/schemas/chat.py`: text composer, regex intent parser, separate hybrid filter closure.
- `frontend/shared/types.ts`, `api-client.ts`: inherited property DTOs; list and search filter serialization.
- `frontend/web/src/components/Navbar.tsx`, `SearchSection.tsx`, `PropertyCard.tsx`: current sale/rent links, filters, cards. Price utility already supports /tháng.
- `frontend/web/src/app/properties/[id]/page.tsx`: details already hide mortgage calculator for rent. Create/edit property pages contain sale/rent tabs; create also hydrates cloned listings.
- `frontend/mobile/lib/models/property.dart`, `providers/app_providers.dart`, `services/property_service.dart`: serialization, filter state, POST hybrid search.
- `frontend/mobile/lib/widgets/search_and_filter.dart`, `property_card.dart`, `screens/property_detail_screen.dart`: existing rental chip, cards, details; no mobile posting form exists.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0008_rental_serviced_apartments.py`, model: alter listing_type default to sale, add rental_type VARCHAR(50), costs/rules JSONB, composite B-tree (listing_type,rental_type,price); reversible downgrade.
- [x] Property/chat schemas and `backend/src/services/rental.py`: typed validation, shared exact predicates and deposit calculations; follow resolved questions.
- [x] Property/search endpoints: persist fields, GET price/rental filters, apply consistent predicates to vector/FTS/fallback, update embeddings and invalidate caches.
- [x] Embedding/chat services: rental cost/rule text, Vietnamese room/loft/pet/budget intent and resolved electricity/location semantics.
- [x] Shared types/client: RentalCosts, RentalRules, RentalType; preserve ListingType; extend CRUD and list/search parameters.
- [x] `frontend/web/src/app/rentals/page.tsx` and listed web components: sale/rent navigation, monthly price/type/amenity filters, rental badges and transparent expense/rule cards.
- [x] Web property create/edit pages: conditional rental inputs, validation, clone hydration and payload handling.
- [x] Listed mobile files: rental discovery tab/filters, metadata serialization, /tháng prices, loft/pet badges and expense details.
- [x] `backend/tests/test_rentals.py`, migration/search/chat tests: matrix, arithmetic, SQL filters, intent, embedding refresh and regression coverage. Extend `frontend/mobile/test/widget_test.dart` for rental model/UI behavior.
- [x] `docs/database-design.md`, `docs/api-specs.md`, `README.md`: schema, units, filters, examples, migration instructions and rental capabilities.

**Acceptance Criteria:**
- Given migration head 0007, when 0008 upgrades, then existing sale/rent values survive and the requested fields/default/index exist; downgrade retains listing_type.
- Given mixed listings, when rental criteria are used through web/mobile/chat, then sale listings and nonmatching rentals are excluded.
- Given a rental, when viewing, creating, editing or cloning on web, then costs/rules persist and display with correct units; mobile discovery/details reflect the same data.
- Given the completed change, when backend tests, TypeScript and production build execute, then every test passes and both web commands exit without errors.

## Implementation Notes

- Implemented all layers; parent audit corrected original requested field names and integer costs, added curfew/private_bathroom, around-landmark parsing, and separate icon-based fee/rule cards. No live migration applied.
- Verification: 146 backend tests passed, followed by all 18 rental tests including the added exact-contract/original-query regression; TypeScript and production build passed; 13 Flutter tests passed. Matrix rows covered by rental validation, predicate, legacy, CRUD/update/sale-transition tests and mobile unknown-fee/badge checks.

## Spec Change Log

## Review Triage Log

## Verification

- Backend: `uv run pytest` (all pass); `uv run alembic upgrade head --sql` and migration downgrade SQL tests.
- Web: `npx tsc --noEmit` and `npm run build` (zero errors).
- Mobile: `flutter analyze` and `flutter test`; inspect rental filters, badges and fee units.
- Report environmental blockers explicitly; mocked SQL tests do not establish live PostgreSQL execution.
