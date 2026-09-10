---
title: 'Host Management Portal, VietQR Deposit Gateway and AI Living Cost Calculation'
type: 'feature'
created: '2026-09-07'
status: 'done'
baseline_commit: '54b7c54051ac5468cbd7a58ce5d62f47751426b7'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247's rental subsystem lacks landlord post-leasing management (contracts, meter reading calculations, monthly invoice generation, debt reminders), real-time room reservation deposit checkout (VietQR Napas 247 / MoMo with webhook IPN), and an automated AI all-in-one living cost estimator for prospective tenants.

**Approach:** Implement Alembic migration 0010 introducing `rental_contracts`, `monthly_invoices`, and `deposit_transactions` tables; build Host Dashboard APIs and reservation payment endpoints with VietQR quick link generation and webhook processing; enhance `ChatAssistantService` with `calculate_total_living_cost` tool; update Shared SDK; build Next.js host dashboard (`/host/dashboard`), tenant deposit modal with 15-minute countdown and polling, and chat breakdown widget; build Flutter host tab and VietQR payment screen; and maintain 100% test coverage and documentation.

## Boundaries & Constraints

**Always:**
- Require `HOST`, `AGENT`, `ADMIN`, or `SUPERADMIN` authorization for `/api/v1/host/*` endpoints.
- Calculate electricity, water, and service costs dynamically per contract or property rules, preventing negative usage numbers.
- Auto-expire pending deposit transactions after 15 minutes and generate standard Napas 247 VietQR URLs (`https://img.vietqr.io/image/...`).
- On successful payment webhook, atomically update transaction status to `success`, unit status to `reserved`, inquiry status to `confirmed`, and create `UserNotification` records for both tenant and landlord.
- Maintain backward compatibility across all existing endpoints, PostGIS spatial indexing, and ensure 0 errors on backend pytest, frontend tsc/build, and Flutter analyze.

**Never:**
- Allow hosts to view or modify contracts, invoices, or units belonging to other hosts.
- Permit booking or depositing on rooms that are already occupied or reserved.
- Drop or mutate existing database columns or break existing migration chains.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Generate Monthly Invoices | List of unit meter readings with previous & current index | Creates `monthly_invoices` records with room fee + electricity total + water total + service total; returns invoices list | 400 Bad Request if current reading < previous reading or contract inactive |
| Approve & Deposit Inquiry | Host calls approve endpoint for pending inquiry | Creates `deposit_transactions` record, generates VietQR URL, returns transaction reference | 404 if inquiry not found, 400 if room occupied, 403 if not unit host |
| Payment Webhook IPN | Webhook POST with matching reference code & amount | Marks deposit as success, locks room as reserved, creates in-app notifications | 404 if reference code unknown; idempotent 200 if already processed |
| AI Living Cost Query | "Căn này 2 người ở thì mỗi tháng hết bao nhiêu tiền?" | Extracts occupants=2, applies property utility rates, returns structured table + friendly explanation | Fallbacks to standard city rates if property rates unspecified |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0010_host_contracts_invoices_deposits.py`: Alembic migration creating `rental_contracts`, `monthly_invoices`, and `deposit_transactions` tables and indexes.
- `backend/src/models/rental_property.py`: SQLAlchemy models `RentalContract`, `MonthlyInvoice`, and `DepositTransaction` with relationships.
- `backend/src/models/__init__.py`: Export new models for discovery.
- `backend/src/schemas/rental_management.py`: Pydantic schemas for contracts, monthly invoice generation, debt reminders, deposit transactions, and payment webhooks.
- `backend/src/schemas/chat.py`: Add `LivingCostBreakdown` schema to `ChatAssistantResponse`.
- `backend/src/services/chat_assistant.py`: Implement `calculate_total_living_cost` tool and pattern matching in `ChatAssistantService`.
- `backend/src/services/payment_service.py`: Service for VietQR quick link generation, reference code minting, and webhook IPN processing.
- `backend/src/api/v1/endpoints/host.py`: Add `/dashboard/stats`, `/contracts`, `/invoices/generate-monthly`, `/invoices/{id}/remind`.
- `backend/src/api/v1/endpoints/rentals.py`: Add `/inquiries/{id}/approve-and-deposit`.
- `backend/src/api/v1/endpoints/payments.py`: Add webhook `/webhook/{provider}` and status query `/deposit-transactions/{reference_code}`.
- `backend/src/api/v1/router.py`: Register payments router.
- `backend/tests/test_host_billing_payments.py`: Pytest suite covering host dashboard, invoice calculations, debt reminders, payment webhook, and AI cost tool.
- `backend/tests/test_alembic_migrations.py`: Update migration chain assertions for revision 0010.
- `frontend/shared/types.ts`: TypeScript interfaces `RentalContract`, `MonthlyInvoice`, `DepositTransaction`, `HostDashboardStats`, `LivingCostBreakdown`.
- `frontend/shared/api-client.ts`: Client methods for host dashboard, invoice creation, reminders, deposit initiation, and webhook polling.
- `frontend/web/src/app/host/dashboard/page.tsx`: Host Management Dashboard with KPI summary cards, unit meter reading quick-form, invoice generator, and tenant list.
- `frontend/web/src/components/DepositPaymentModal.tsx`: Tenant deposit payment modal with VietQR image, countdown timer (15 min), and real-time polling.
- `frontend/web/src/components/ChatAssistantWidget.tsx`: Render interactive breakdown card for living cost estimates.
- `frontend/mobile/lib/screens/host_management_screen.dart`: Host rental unit and tenant management screen.
- `frontend/mobile/lib/screens/vietqr_payment_screen.dart`: VietQR payment screen with QR display, save image, and bank app launcher.
- `docs/database-design.md`, `docs/api-specs.md`, `README.md`: System documentation updates.

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/models/rental_property.py` & `backend/src/models/__init__.py` -- Define `RentalContract`, `MonthlyInvoice`, `DepositTransaction` models and export them.
- [x] `backend/migrations/versions/0010_host_contracts_invoices_deposits.py` & `backend/tests/test_alembic_migrations.py` -- Migration creating the 3 new tables with FKs and indexes, updating alembic tests.
- [x] `backend/src/schemas/rental_management.py` & `backend/src/schemas/chat.py` -- Add request/response schemas for contracts, invoices, deposits, webhooks, and living cost breakdowns.
- [x] `backend/src/services/payment_service.py` & `backend/src/api/v1/endpoints/payments.py` -- Implement VietQR generation, transaction tracking, and webhook IPN handler.
- [x] `backend/src/api/v1/endpoints/host.py` & `backend/src/api/v1/endpoints/rentals.py` -- Add host dashboard stats, contracts list, invoice generation, debt reminders, and inquiry deposit approval.
- [x] `backend/src/services/chat_assistant.py` -- Implement `calculate_total_living_cost` tool in ChatAssistantService with regex detection and breakdown math.
- [x] `backend/tests/test_host_billing_payments.py` -- Comprehensive pytest suite covering all host operations, payment workflows, and AI tool.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add TypeScript DTOs and API methods for host portal and payments.
- [x] `frontend/web/src/app/host/dashboard/page.tsx` & `frontend/web/src/components/DepositPaymentModal.tsx` -- Host dashboard with KPI cards, meter reader, reminder trigger, and tenant payment modal.
- [x] `frontend/web/src/components/ChatAssistantWidget.tsx` -- Living cost breakdown card renderer in chat bubbles.
- [x] `frontend/mobile/lib/screens/host_management_screen.dart` & `frontend/mobile/lib/screens/vietqr_payment_screen.dart` -- Mobile landlord management screen and VietQR payment viewer.
- [x] `docs/database-design.md`, `docs/api-specs.md`, `README.md` -- Update architectural diagrams, ERD, and API endpoint documentation.

**Acceptance Criteria:**
- Given an active host, when accessing `/api/v1/host/dashboard/stats`, they receive occupancy rate, estimated revenue, unpaid invoices count, and pending inquiry count.
- Given active rental contracts, when the host submits meter readings to `/api/v1/host/invoices/generate-monthly`, invoices are calculated and persisted with correct room, electricity, and water totals.
- Given an approved inquiry, calling `/api/v1/rentals/inquiries/{id}/approve-and-deposit` returns a 15-minute expiring Napas 247 VietQR payment link.
- Given a valid payment webhook callback, the transaction is marked success and the room is immediately transitioned to `reserved`.
- Given a user asking the AI assistant about monthly living expenses (e.g. 2 occupants, 150 kWh electricity), the chatbot returns a structured breakdown table in Vietnamese.
- All backend tests pass (100%), frontend TypeScript passes (`npx tsc --noEmit`), web build succeeds, and `flutter analyze` reports 0 issues.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| Layer | Finding / Location | Verdict | Evidence & Rationale | Route |
|---|---|---|---|---|
| Verification Gap | `backend/src/api/v1/endpoints/host.py` (`GET /invoices`) | medium | Missing explicit endpoint integration test for invoice listing and filter. | patch |
| Verification Gap | `backend/src/api/v1/endpoints/chat.py` (`living_cost`) | medium | Missing endpoint integration test asserting on structured `living_cost` in assistant response. | patch |
| Verification Gap | `backend/src/services/payment_service.py` (`auto-expiration`) | medium | Missing test verifying expired status mutation on stale deposit queries. | patch |
| Verification Gap | `backend/src/api/v1/endpoints/host.py` (`per_person water`) | medium | Missing test asserting per-person flat water rate calculation. | patch |
| Edge Case / Blind | `backend/src/services/payment_service.py` (`process_payment_webhook`) | high | Webhook did not verify `tx.status == "expired"` or `expires_at` or `unit.status == "occupied"`. | patch |
| Edge Case / Blind | `backend/src/api/v1/endpoints/host.py` (`generate_monthly_invoices`) | medium | Missing duplicate invoice prevention for same `contract_id` and `billing_month`. | patch |
| Edge Case / Blind | `backend/src/api/v1/endpoints/host.py` (`create_rental_contract`) | medium | Contract creation did not guard against unit already occupied, and assigned `host_id = current_host.id` instead of property host when called by admin. | patch |
| Edge Case / Blind | `backend/src/api/v1/endpoints/host.py` (`remind_invoice_debt`) | low | Debt reminder should guard against sending for cancelled or paid invoices. | patch |
| Blind Hunter | `backend/src/api/v1/endpoints/host.py` (`list_host_invoices`) | low | Query parameter `status_filter` did not support alias `status` sent by mobile service. | patch |
| Blind Hunter | `backend/src/api/v1/endpoints/rentals.py` (`approve_inquiry_and_deposit`) | low | Endpoint should accept optional request body with custom `deposit_amount` as sent by mobile client. | patch |
| Blind Hunter | `frontend/web/src/app/host/dashboard/page.tsx` (`waterCost calculation`) | medium | Web preview checked `fixed_per_person` instead of `per_person` and didn't multiply by occupants. | patch |
| Blind Hunter | `frontend/web/src/components/ChatAssistantWidget.tsx` (`summary display`) | low | Avoid unparsed raw markdown table snippet in message bubble since itemized cards already show breakdown. | patch |
| Blind Hunter | `frontend/web/src/components/DepositPaymentModal.tsx` (`orphaned UI`) | medium | Integrate `DepositPaymentModal` into `rentals/my-inquiries` and `host/dashboard` so tenants and hosts can view and open it. | patch |
| Blind Hunter | `frontend/mobile/lib/screens/host_management_screen.dart` (`water meter input`) | low | Add client-side validation `waterCurr >= waterPrev`. | patch |

## Verification

**Commands:**
- `uv run pytest` -- expected: 100% pass across all test suites including new host billing and payments tests.
- `npx tsc --noEmit` -- expected: 0 type errors in frontend web.
- `npm run build` (in frontend/web) -- expected: successful Next.js production build.
- `flutter analyze` (in frontend/mobile) -- expected: 0 issues found.
