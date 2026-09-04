---
title: 'Space247 User Retention and Financial Tools'
type: 'feature'
created: '2026-09-04'
baseline_commit: '9703c3f'
status: 'completed'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users searching for real estate often browse repeatedly without saving their search criteria or receiving timely notifications when matching homes enter the market. Additionally, homebuyers struggle to estimate bank loan affordability, interest rates, and monthly repayments without financial modeling tools, lowering platform retention and conversion.

**Approach:** Build a comprehensive "User Retention & Financial Tools" suite for Space247:
1. **Saved Search Alerts & Notification Matching Engine**:
   - Store search criteria (price, location, property type, bedrooms, radius, keywords) with instant/daily/weekly frequency.
   - Event-driven matching: when a new property is published, an asynchronous background task scans active alerts, matches criteria, generates in-app notifications (`user_notifications`), and logs email alerts.
2. **Mortgage & Loan Financial Calculator (Public API & Interactive UI)**:
   - Computes loan schedules for both "declining_balance" (dư nợ giảm dần) and "fixed_payment" (niên kim cố định / chia đều).
   - Accounts for preferential interest periods (e.g. 12-24 months) and post-preferential floating rates.
3. **AI Chatbot Assistant Financial Advisor**:
   - Quick CTA action in chat: "🔔 Lưu tìm kiếm & Nhận cảnh báo khi có căn mới" automatically passing extracted criteria to alerts API.
   - Financial Q&A intent detection: auto-simulates mortgage payments when users ask "Nếu vay 70% mua căn hộ này trong 20 năm thì mỗi tháng trả bao nhiêu?".
4. **Frontend Web & Mobile Integrations**:
   - Web: Interactive `MortgageCalculator.tsx` with principal/interest distribution and amortization table on property detail page (`/properties/[id]`); notification bell with unread badge in Navbar; alert management at `/profile/alerts`.
   - Mobile: Mortgage calculator bottom sheet, notifications tab, and "Theo dõi tiêu chí này" button.

**Decisions:**
- Background Alert Matching Strategy: Adopt Option A (FastAPI `BackgroundTasks`). When a new property is published (`POST /api/v1/properties`), an asynchronous background task evaluates active alerts against the property's price, location, property_type, and specs, immediately creating in-app notification records in `user_notifications` with zero extra worker container dependencies.

## Boundaries & Constraints

**Always:**
- Secure `/api/v1/alerts` and `/api/v1/notifications` with Bearer JWT (requires authenticated user).
- Keep `/api/v1/financial/mortgage-calc` public without authentication requirement so unauthenticated visitors can calculate loans.
- Ensure mortgage calculations accurately compute amortization tables with `round(..., 0)` in VND.
- Trigger background alert evaluation asynchronously via FastAPI `BackgroundTasks` to avoid blocking property creation response.
- Support cascade deletion of notifications and alerts when users are deleted.

**Never:**
- Do not block the property creation response while matching alerts.
- Do not crash mortgage calculator if down payment is 0 or 100%.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create Alert from Chat Criteria | `POST /api/v1/alerts` with `title="Chung cư Cầu Giấy 3-5 tỷ"`, `criteria={min_price: 3e9, max_price: 5e9, district: "Cầu Giấy"}` | 201 Created with alert ID and active status | 401 if unauthenticated, 422 if invalid criteria |
| Mortgage Calc Declining Balance | `property_price=5e9, down_payment_percent=30, loan_term_years=20, rate=7.5%, preferential=12mo, post_rate=10.5%` | `monthly_payment_first_month`, `total_interest`, `amortization_schedule` (240 months) | 400 if loan_term_years not in 1-35 |
| Property Published Triggers Matching | `POST /api/v1/properties` with matching criteria for 2 users' alerts | 2 entries created in `user_notifications` | Handled asynchronously in background |
| Notification Bell Count | `GET /api/v1/notifications` | List of notifications with `unread_count` | 401 if unauthenticated |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0004_add_alerts_and_notifications.py` -- Alembic migration for `saved_search_alerts` and `user_notifications` tables.
- `backend/src/models/alert.py` -- SQLAlchemy models `SavedSearchAlert` and `UserNotification`.
- `backend/src/schemas/alert.py` -- Pydantic schemas `CreateAlertRequest`, `AlertResponse`, `NotificationResponse`, `NotificationListResponse`.
- `backend/src/schemas/mortgage.py` -- Pydantic schemas `MortgageCalcRequest`, `MortgageCalcResponse`, `AmortizationScheduleItem`.
- `backend/src/services/mortgage_service.py` -- Financial mortgage calculation engine (declining balance & fixed payment).
- `backend/src/services/alert_service.py` -- Alert matching engine and notification dispatcher.
- `backend/src/services/chat_assistant.py` -- Integrate financial Q&A intent and mortgage calculation.
- `backend/src/api/v1/endpoints/alerts.py` -- CRUD endpoints for saved search alerts.
- `backend/src/api/v1/endpoints/notifications.py` -- Endpoints for listing and marking notifications as read.
- `backend/src/api/v1/endpoints/financial.py` -- Endpoint `POST /financial/mortgage-calc`.
- `backend/src/api/v1/endpoints/properties.py` -- Hook alert matching into `create_property` background tasks.
- `backend/src/api/v1/router.py` -- Mount `/alerts`, `/notifications`, and `/financial` routers.
- `backend/tests/api/v1/test_alerts.py` -- Pytest suite for alerts, notifications, and matching engine.
- `backend/tests/api/v1/test_mortgage.py` -- Pytest suite for mortgage calculator math and edge cases.
- `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add DTO types and SDK client methods.
- `frontend/web/src/components/MortgageCalculator.tsx` -- Interactive loan calculator with sliders and breakdown.
- `frontend/web/src/components/Navbar.tsx` -- Notification bell dropdown with unread badge count.
- `frontend/web/src/components/ChatAssistantWidget.tsx` -- Quick CTA button "🔔 Lưu tìm kiếm & Nhận cảnh báo".
- `frontend/web/src/app/properties/[id]/page.tsx` -- Embed MortgageCalculator in property details.
- `frontend/web/src/app/profile/alerts/page.tsx` -- Alerts management page.
- `frontend/mobile/lib/widgets/mortgage_calculator_sheet.dart` -- Mobile loan calculator bottom sheet.
- `frontend/mobile/lib/screens/notifications_screen.dart` -- Mobile notifications screen.
- `README.md` -- Documentation for new endpoints and features.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0004_add_alerts_and_notifications.py` -- Create Alembic migration for alerts and notifications.
- [x] `backend/src/models/alert.py` -- Define `SavedSearchAlert` and `UserNotification` models.
- [x] `backend/src/schemas/alert.py` & `backend/src/schemas/mortgage.py` -- Create Pydantic DTOs.
- [x] `backend/src/services/mortgage_service.py` -- Implement mortgage loan calculation formulas.
- [x] `backend/src/services/alert_service.py` -- Implement alert matching against new properties.
- [x] `backend/src/services/chat_assistant.py` -- Add mortgage advice intent and alert CTA data.
- [x] `backend/src/api/v1/endpoints/alerts.py`, `notifications.py`, `financial.py` -- Implement endpoints.
- [x] `backend/src/api/v1/endpoints/properties.py` -- Trigger matching engine in `create_property`.
- [x] `backend/src/api/v1/router.py` -- Register new routers.
- [x] `backend/tests/api/v1/test_alerts.py` & `test_mortgage.py` -- Write comprehensive pytest test suites.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add types and SDK methods.
- [x] `frontend/web/src/components/MortgageCalculator.tsx` -- Build Web mortgage calculator component.
- [x] `frontend/web/src/components/Navbar.tsx` -- Add notification bell with unread badge.
- [x] `frontend/web/src/components/ChatAssistantWidget.tsx` -- Add save alert CTA button.
- [x] `frontend/web/src/app/properties/[id]/page.tsx` -- Integrate MortgageCalculator into detail page.
- [x] `frontend/web/src/app/profile/alerts/page.tsx` -- Create alerts management dashboard.
- [x] `frontend/mobile/` -- Add mobile mortgage sheet and notifications screen.
- [x] `README.md` -- Update documentation with new features and endpoints.

**Acceptance Criteria:**
- Given an authenticated user, when `POST /api/v1/alerts` is called with search criteria, an active alert is saved.
- Given active alerts, when a matching property is created via `POST /api/v1/properties`, notification records are generated in `user_notifications`.
- Given property price and loan terms, when `POST /api/v1/financial/mortgage-calc` is called, it returns precise amortization schedule and monthly payment amounts.
- Given Web property detail page, user can adjust loan percentage/term and view visual breakdown of principal vs interest.
- 100% pytest pass across all backend tests and clean Next.js build.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest tests/api/v1/test_alerts.py tests/api/v1/test_mortgage.py` -- expected: PASS 100%
- `cd backend && uv run pytest` -- expected: PASS 100%
- `cd frontend/web && npx tsc --noEmit` -- expected: 0 errors
- `cd frontend/web && npm run build` -- expected: SUCCESS
