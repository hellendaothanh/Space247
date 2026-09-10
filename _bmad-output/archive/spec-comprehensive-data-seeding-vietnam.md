---
title: 'Comprehensive Data Seeding for Space247 across Vietnam'
type: 'feature'
created: '2026-09-07'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247 needs a rich, realistic, and balanced seed dataset spanning nationwide Vietnam (North to South: Hanoi, Quang Ninh, Hai Phong, Da Nang, Nha Trang, HCMC, Binh Duong, Can Tho, Phu Quoc) covering major real estate projects, sale listings, long-term rentals, boarding houses/serviced apartments with units, homestays, and sample contracts/invoices with 768-dimensional embeddings and PostGIS geometries, operating idempotently.

**Approach:**
1. Overhaul and expand `backend/scripts/seed_properties.py` to seed:
   - >=6 prominent Projects across North, Central, and South Vietnam with master plans, amenities, price ranges, and coordinates.
   - >=12 Sale listings (apartments in projects, street-front townhouses, villas, suburban land).
   - >=8 Rent listings (apartments, commercial shophouses, serviced offices).
   - >=10 Boarding houses & serviced apartments with unit lists (`rental_units`) and granular utility cost rules (`rental_costs`, `rental_rules`).
   - >=5 Homestay & vacation listings with daily pricing and check-in rules.
   - 2 sample rental contracts (`rental_contracts`) linked to `agent@space247.vn` and `user@space247.vn`.
   - 2 sample monthly invoices (`monthly_invoices` - 1 unpaid for reminder test, 1 paid).
   - 1 pending rental inquiry (`rental_inquiries`) for VietQR reservation deposit testing.
2. Ensure strict idempotency across all entities using slug/title/name/reference matching.
3. Automatically generate 768-dim embeddings via `EmbeddingService` and PostGIS SRID 4326 geometries.
4. Support `--reindex-vectors` CLI flag and verify 100% test pass in `backend/tests/test_seed_properties.py`.

</frozen-after-approval>

## Implementation Notes

- **Overhauled `backend/scripts/seed_properties.py`**:
  - Expanded `SAMPLE_PROJECTS` to 10 tier-1 projects covering North, Central, and South (Vinhomes Ocean Park, Starlake, Vinhomes Smart City, Sun Cosmo Residence, Vinhomes Central Park, The Metropole, Vinhomes Grand Park, Masteri Centre Point, Phu My Hung Midtown, Sun Grand City Hillside).
  - Expanded `SAMPLE_PROPERTIES` to 41 nationwide properties across 9 provinces/cities (Hanoi, Quang Ninh, Hai Phong, Da Nang, Nha Trang, HCMC, Binh Duong, Can Tho, Phu Quoc) covering sale apartments, street-front townhouses, sea/garden villas, residential land, long-term rentals, and homestay vacation apartments.
  - Implemented `SAMPLE_RENTALS` with 11 complexes and 31 granular rental units with detailed `shared_costs` and `shared_rules`.
  - Added dedicated `host@space247.vn` user to `DEFAULT_SEED_USERS`.
  - Seeded 2 active `RentalContract` records, 2 `MonthlyInvoice` records (1 pending, 1 paid), 1 pending `RentalInquiry`, and 1 pending `DepositTransaction` with VietQR Napas 247 payment URL.
  - Generates PostGIS `WKTElement` SRID 4326 geometry points and computes 768-dimensional dense vector embeddings with FastEmbed `paraphrase-multilingual-mpnet-base-v2`.
  - Added `--reindex-vectors` CLI flag for re-indexing properties and projects.
- **Verification**:
  - Updated `backend/tests/test_seed_properties.py` to 11 comprehensive tests including direct Pydantic schema validation (`PropertyBase`, `ProjectBase`, `RentalPropertyBase`, `RentalUnitBase`), contracts/invoices idempotency, and vector re-indexing.
  - Ran full backend pytest suite: 165 tests passed with 100% success rate.

## Review Triage Log

- `Invalid property_type = 'townhouse'`: verdict `high`, evidence: Pydantic `PropertyType` only permits `apartment`, `house`, `villa`, `land`, `commercial`. Patched by changing `townhouse` items to `house`.
- `Invalid rental_type = 'homestay' and extra fields in rental_rules`: verdict `high`, evidence: `RentalType` and `RentalRuleSchema(extra='forbid')` reject extra fields. Patched to `serviced_apartment`/`entire_house` and compliant schema fields.
- `Rental metadata omitted when building embeddings`: verdict `medium`, evidence: `build_property_text` was called without rental arguments. Patched by passing `rental_type`, `rental_costs`, and `rental_rules`.
- `Inconsistent status='confirmed' for sample inquiry`: verdict `medium`, evidence: spec required 1 pending inquiry for deposit flow testing. Patched to `status='pending'`.
- `Unused import and missing seed data for DepositTransaction`: verdict `medium`, evidence: `DepositTransaction` was imported but unused. Patched by seeding a sample pending VietQR deposit transaction `DEP-SAMPLE-P202`.
- `Flawed vacuous mock test in test_seed_contracts_invoices_and_inquiries_logic`: verdict `medium`, evidence: mock returned None for unit queries. Patched with realistic mock units and idempotency assertions.
- `Missing test coverage for vector reindexing`: verdict `low`, evidence: `--reindex-vectors` was uncovered. Patched by adding `test_reindex_all_vectors_logic`.
- `Unit photos discarded during rental unit seeding`: verdict `medium`, evidence: `RentalUnit` instantiation omitted `images`. Patched by passing `images=u.get('images') or ...`.
- `Orphan project vinhomes-grand-park`: verdict `medium`, evidence: no property pointed to `vinhomes-grand-park`. Patched by adding `The Origami Vinhomes Grand Park` 2PN apartment.
- `Misplaced DDL execution in seed_projects`: verdict `medium`, evidence: raw ALTER TABLE and premature commit in transaction. Patched by removing redundant DDL already handled by migration 0006.
- `Superficial tests miss schema validation for seed datasets`: verdict `medium`, evidence: dictionary-only tests allowed invalid enum values. Patched by validating against Pydantic schemas in tests.
- `Vacation listing test assertion logic`: verdict `low`, evidence: keyword search needed to cover descriptions. Patched in test.
- `Missing host user role in DEFAULT_SEED_USERS`: verdict `medium`, evidence: `UserRole.HOST` exists but was omitted. Patched by adding `host@space247.vn`.
- `Standard rent listings lack rental filters metadata`: verdict `medium`, evidence: rent listings had None for rental filters. Patched by populating `rental_type`, `rental_costs`, and `rental_rules`.
- `Silent failures when entities cannot be resolved`: verdict `low`, evidence: existing code logged debug warnings. Verified and improved with clear error messaging.
- `Dynamic month string in invoices`: verdict `false`, evidence: invoices are keyed by `(contract_id, billing_month)` preventing duplication within billing cycle.
- `Duplicate inline text construction for project embeddings`: verdict `low`, cosmetic; verified working properly in both seed and reindex functions.

