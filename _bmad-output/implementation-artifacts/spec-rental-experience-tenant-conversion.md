---
title: 'Rental Experience and Tenant Conversion Suite'
type: 'feature'
created: '2026-09-10'
status: 'done'
route: 'dispatch'
baseline_commit: 'd3d87a1c3f289272d15db90e4b561080a3f4cfbc'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="User authorized one-shot execution and continuation of unfinished changes">

## Intent

**Problem:** Tenants cannot inspect individual rooms or compare a credible monthly living budget on the rental detail page. The previous interrupted session has partially implemented migration, backend schemas, calculator, and seed changes.

**Approach:** Complete one cohesive rental discovery experience across database, API, shared SDK, web media and room details, interactive monthly estimates, and nearby amenities. Preserve existing viewing and booking flows.

## Boundaries & Constraints

**Always:** Continue existing edits without reverting them. Vietnamese customer-facing copy; English code identifiers and technical documentation. Reuse current architecture and media allowlists. Preserve explicit zero and unknown fees. Respect unit capacity and active property visibility. User explicitly authorized technical decisions and one-shot implementation without intermediate approvals. All agents share the repository; do not revert other work. Implementation agent owns suite source, tests, and related documentation; coordinator owns this spec and review.

**Never:** Deploy, run live data mutations, modify credentials, or claim sample stock imagery/video is verified real property evidence. Do not read archived specs. Do not duplicate images/max_occupants columns already in migration 0009. Do not widen this into unrelated host portal redesign.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Known budget | Rent 2200000, electricity 3000/kWh, two occupants, AC and fridge | 180kWh, electricity 540000; add declared water and fixed fees; divide total by two | Valid estimate |
| Zero and unknown | Zero electricity or service fee; missing water rate | Preserve zero, identify unknown amounts separately and mark partial total | No false free fee claim |
| Capacity and lookup | Invalid occupants, missing room, mismatched property, inactive building | Validation or not-found response, no public inactive budget | 422 / 404 |
| UI interaction | Change selected room, occupancy or devices, including rapid changes | Updated latest budget only; loading/error/empty states; room media and capacity visible | Retry after API error |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0015_rental_experience_media_and_costs.py`: unfinished migration; 0009 already defines room images and capacity. Align new nullability/defaults with models.
- `backend/src/models/rental_property.py`, `backend/src/schemas/rental_management.py`: partial new fields; complete typed surroundings and backward-compatible output.
- `backend/src/services/rental.py`: unfinished pure calculator currently loses zero electricity and treats unknown water as zero; add service_fee_monthly and disclose rate/consumption assumptions.
- `backend/src/api/v1/endpoints/rentals.py`: unfinished property/unit calculator route; enforce visibility and capacity.
- `backend/src/api/v1/endpoints/host.py`: explicit property serializer must carry new fields; create paths must persist them.
- `backend/scripts/seed_properties.py`: partial sample media/nearby data for Bach Khoa Da Nang and other rentals; preserve idempotency and honestly identify sample assets.
- `frontend/shared/types.ts`, `frontend/shared/api-client.ts`: existing RentalUnit/RentalProperty and getRentalProperty; extend without breaking callers.
- `frontend/shared/media.ts`, `frontend/web/src/components/common/MediaSuite.tsx`: reuse existing mosaic/lightbox and validated YouTube/Shorts/TikTok embed support.
- `frontend/web/src/app/rentals/[id]/page.tsx`: text-only rooms and existing appointment/booking modal; integrate dedicated suite components.
- `frontend/mobile/lib/models/rental_property.dart`: maintain new metadata serialization compatibility; no separate mobile UI requested.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0015_rental_experience_media_and_costs.py`, models and schemas -- complete additive media, amenities, surroundings and security metadata with aligned defaults.
- [x] `backend/src/services/rental.py`, rental and host endpoints -- implement accurate disclosed monthly estimate and complete read/write serialization. Missing fees stay unknown; state_rate without published per-kWh rate must not masquerade as fixed published tariff. Default 3000 assumption may be disclosed explicitly. Use 120/30/30 kWh and 2m3/person assumption for per_m3 water; show fee basis.
- [x] `backend/scripts/seed_properties.py` -- add distinct room sample media/amenities and surroundings for multiple rentals.
- [x] `frontend/shared/types.ts`, `frontend/shared/api-client.ts` -- export RentalUnitDetail, RoomAmenity, SurroundingPlace, MonthlyCostEstimate and calculateRentalLivingCost(unitId, params), with property_id in params.
- [x] `frontend/web/src/app/rentals/[id]/page.tsx` and rental components -- mosaic/lightbox of building plus rooms, video tab, room thumbnails/badges/capacity, accessible detail dialog with room photos/floor plan, smart calculator with 1-3 occupants capped to room capacity, neighborhood icons/security cards. Preserve inquiry modal behavior.
- [x] `frontend/mobile/lib/models/rental_property.dart` -- carry new fields through parsing/serialization.
- [x] Backend regression tests -- exercise calculation, room/property metadata, migration chain and existing rental lifecycle.
- [x] `README.md`, `backend/README.md`, `frontend/web/README.md` -- synchronize contracts and verification guidance.

**Acceptance Criteria:**
- Given a listed rental, when tenants explore building and room media, then room-specific images, amenities, capacity and available layout are accessible without losing booking actions.
- Given declared charges, when occupants/devices change, then fixed/variable monthly costs and per-person total agree with the backend estimate and all assumptions are visible.
- Given nearby and security metadata, when opening the detail page, then Vietnamese commute and security cards display only supplied facts.
- Given the full change, when backend pytest, web TypeScript/build and mobile analyze run, then all pass; behavioral tests cover the matrix.

## Implementation Notes

User's explicit continuation authorizes the existing dirty worktree. Writing a migration is reversible; live migration/seeding is outside this execution. No unresolved user-visible intent gaps.

Completed directly after the delegated implementation agent exhausted its usage quota. Review found and corrected host create serialization, inactive-detail visibility, zero-fee preservation, service-fee calculation, and migration-head expectations.

## Spec Change Log

## Review Triage Log

## Verification

- Backend: `uv run pytest` -- all pass.
- Web: `npx tsc --noEmit`, `npm run build` -- no errors, plus behavioral tests using available tooling.
- Mobile: `flutter analyze` -- no issues; add focused DTO round-trip test if model changes.
- Inspect migration chain and generated SQL where available; do not claim applied live migration.
