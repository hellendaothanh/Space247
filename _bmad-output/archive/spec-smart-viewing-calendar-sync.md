---
title: 'Smart Viewing and Calendar Sync'
type: 'feature'
created: '2026-09-09'
status: 'done'
baseline_commit: '912ad3df93af3f7633680e848212de4f82e0c4fe'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Rental tenants cannot discover trustworthy host availability, reserve a viewing slot safely, or carry a confirmed appointment into their calendar. Hosts lack a weekly availability planner and a focused appointment workflow.

**Approach:** Extend the existing rental-inquiry appointment record with calendar fields, add host availability and exceptions, expose slot booking/confirmation/calendar APIs, and surface the same flow in shared, web, and Flutter clients.

## Boundaries & Constraints

**Always:** Use `rental_inquiries` as the canonical appointment record; preserve legacy inquiry APIs, statuses, UUID conventions, and host authorization. Treat Monday as `0`, use Vietnam local civil dates/times for schedules and calendar event values, and return only slots contained fully in an active schedule, not blocked, and not overlapping a confirmed appointment. Booking and confirmation must be atomic and prevent concurrent double booking. Generate standards-compatible Google Calendar URLs and iCalendar text without Google OAuth. Confirmed events create in-app notifications for tenant and host and persist their calendar metadata. Maintain existing property, deposit, contract, invoice, contact, and search behavior.

**Never:** Create or assume a separate `viewing_appointments` table, alter prior migrations, deploy, run a live migration, fabricate a Google OAuth sync, expose other hosts' schedules/appointments, or make a calendar URL substitute for authorization or a booked slot.

**Approved decisions:** Confirmation always creates in-app notifications, a direct iCalendar download, and a Google Calendar quick-open URL. When SMTP configuration is available, dispatch an `.ics` attachment in the background; otherwise log safely without interrupting the user flow.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Available slots | Active host hours and a valid date | Returns duration-sized, ordered, unreserved slots | Blocked/inactive/no-hours date returns an empty slot list |
| Booking collision | Two tenants request the same slot | Exactly one pending appointment is created | The loser receives conflict; no partial calendar data |
| Confirmation | Host owns a pending appointment | Marks confirmed and returns persisted Google/iCal metadata | Missing/non-owned/non-pending appointment returns 404/403/409 |
| Calendar download | Authorized appointment owner requests ICS | Returns downloadable `text/calendar` content | Non-owner receives 403; unknown id receives 404 |
| Weekly updates | Host sends multiple weekday windows | Replaces that host's weekly configuration and validates non-overlap | Invalid day/time/duration or overlapping windows returns 422 |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0013_e_contract_digital_kyc.py`, `0009_two_sided_rental_system.py` -- migration head and UUID/PostgreSQL conventions; add reversible `0014` only.
- `backend/src/models/rental_property.py`, `backend/src/models/__init__.py` -- `RentalInquiry` is the existing appointment; add its calendar fields plus host schedule/block-date models and exports.
- `backend/src/schemas/rental_management.py` -- preserve `RentalInquiryCreate`/response compatibility while adding schedule, slot, booking, confirmation, and calendar DTOs.
- `backend/src/api/v1/endpoints/rentals.py`, `host.py`, `router.py` -- existing tenant inquiry and host authorization/status paths; add slot, booking, ICS, schedule, and confirmation routes without replacing legacy routes.
- `backend/src/models/alert.py`, `backend/src/services/payment_service.py` -- reuse `UserNotification` and atomic notification patterns; introduce calendar utility and, if approved, mail delivery adapter.
- `frontend/shared/types.ts`, `api-client.ts` -- append schedule/calendar contracts and methods without changing request/auth behavior.
- `frontend/web/src/app/rentals/[id]/page.tsx`, `components/PropertyBookingModal.tsx`, `app/properties/[id]/page.tsx` -- replace rental booking time input with date/slot selection; preserve sale contact actions.
- `frontend/web/src/app/host/dashboard/page.tsx` -- add isolated availability planner and appointment timeline while retaining dashboard billing features.
- `frontend/mobile/lib/screens/property_detail_screen.dart`, `host_management_screen.dart`, `models/rental_property.dart`, `services/host_service.dart`, `providers/app_providers.dart` -- add rental-only booking sheet, calendar launcher, schedule models/calls and host schedule UI; retain phone/email and billing workflows.
- `backend/tests/test_rental_two_sided.py`, `backend/tests/test_alembic_migrations.py`, `docs/database-design.md`, `docs/api-specs.md`, `README.md` -- regression/race tests and public data/API/migration documentation.

## Tasks & Acceptance

**Execution:**
- [ ] Migration, models, and schemas -- add schedule/blocked-date persistence, appointment calendar columns, constraints/indexes, and typed request/response contracts.
- [ ] Calendar and API services -- calculate slots, protect booking/confirmation transactions, generate Google/ICS values, expose all requested tenant/host endpoints, and notify both parties.
- [ ] Shared, web, and mobile clients -- use typed APIs for slot booking, confirmation actions, calendar CTAs, host schedule planning, and visual status timelines.
- [ ] Tests and docs -- cover slot subtraction, blocked dates, invalid schedules, authorization, concurrent bookings, calendar payloads, migration head, and all stated documentation.

**Acceptance Criteria:**
- Given an available rental unit, when a tenant selects a displayed slot, then one appointment is created and competing requests cannot reserve that interval.
- Given a host configures hours and confirms an owned appointment, when either party uses the calendar CTA, then Google and ICS representations match the confirmed time and location.
- Given rental or host users on web and mobile, when they use scheduling features, then non-rental contact, existing inquiry, and host billing workflows continue to work.
- Given the completed change, when backend tests, web typecheck/build, Flutter analysis, and mobile tests run, then they exit successfully.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Use a database transaction with a host/date/time overlap predicate at booking and confirmation boundaries; the UI's disabled slots are advisory only. Preserve `scheduled_time` as a compatibility projection of appointment date/start time.

## Verification

**Commands:**
- `cd backend; uv run pytest` -- expected: all backend tests pass, including slot and concurrency coverage.
- `cd frontend/web; npx tsc --noEmit` -- expected: zero type errors.
- `cd frontend/web; npm run build` -- expected: successful production build.
- `cd frontend/mobile; flutter analyze` -- expected: zero issues.
- `cd frontend/mobile; flutter test` -- expected: calendar booking behavior passes.
