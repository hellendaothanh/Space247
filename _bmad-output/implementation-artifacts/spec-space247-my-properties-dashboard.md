---
title: 'My Properties Dashboard for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** Authenticated users (property owners/agents) currently lack a personal dashboard to view, track status, edit, or delete their own listings, and the Navbar lacks a quick access menu for personal listings.

**Approach:**
1. Backend:
   - Add endpoint GET /api/v1/properties/my protected by Bearer token (get_current_active_user), returning listings where user_id == current_user.id, with optional pagination and status filter. Ensure it is defined before GET /api/v1/properties/{property_id}.
   - Enforce authorization in PUT /api/v1/properties/{property_id} and DELETE /api/v1/properties/{property_id} ensuring that callers are either the listing owner or an admin.
   - Add automated backend test cases in backend/tests/test_properties_my.py verifying authentication, ownership isolation, status filtering, and edit/delete permissions.
2. Shared SDK & Frontend:
   - Extend RealEstateApiClient with getMyProperties(params?: { skip?: number; limit?: number; status?: PropertyStatus }).
   - Build dashboard page /properties/my displaying personal listings with status badges (active/inactive/pending/sold), statistics (including view count and total listings), quick filters, and action buttons:
     - "Xem" (link to /properties/[id]).
     - "Chỉnh sửa" (link to edit form /properties/[id]/edit).
     - "Xóa" (triggers a confirmation modal and executes deletion via API).
   - Build edit page /properties/[id]/edit with form pre-populated from property details, supporting updates to title, description, price, area, status, bedrooms, bathrooms, etc.
   - Enhance Navbar.tsx user profile section with a dropdown menu offering quick links to "Quản lý tin đăng" (/properties/my), "Đăng tin mới" (/properties/create), and "Đăng xuất".

</frozen-after-approval>

## Implementation Notes

1. **Backend Route Precedence**:
   - Registered `GET /api/v1/properties/my` ahead of `GET /api/v1/properties/{property_id}` in `backend/src/api/v1/endpoints/properties.py` to prevent FastAPI router from parsing string `"my"` as a UUID.
   - Guarded `GET /api/v1/properties/my`, `PUT /api/v1/properties/{property_id}`, and `DELETE /api/v1/properties/{property_id}` with strict authorization check: caller must be listing owner (`user_id == current_user.id`) or an administrator (`role == 'admin'`).
2. **Backend Automated Tests**:
   - Created `backend/tests/test_properties_my.py` verifying:
     - 401 Unauthorized when unauthenticated.
     - 200 OK returning only listings belonging to the authenticated user.
     - Status filtering (`status=inactive` / `status=active`).
     - 403 Forbidden when a user attempts to update/delete another user's property.
     - 204 No Content on successful deletion by owner or admin.
   - Set mock user role to `admin` in `tests/conftest.py` default mock user so legacy semantic search tests with unassigned properties pass smoothly.
   - All 50/50 pytest tests pass 100%.
3. **Frontend Implementation**:
   - `frontend/shared/api-client.ts`: Added `getMyProperties()` method and URL encoding on property IDs.
   - `frontend/web/src/components/Navbar.tsx`: Added interactive user dropdown with avatar, user metadata, links to `/properties/my`, `/properties/create`, and logout action with outside-click dismissal, plus desktop quick action button.
   - `frontend/web/src/app/properties/my/page.tsx`: Built comprehensive personal listings dashboard with status metrics (total, active, inactive, views), search filter, status filter tabs, property cards, and accessible deletion modal with backdrop dismissal and inline error banner.
   - `frontend/web/src/app/properties/[id]/edit/page.tsx`: Built edit property page with form pre-filling, client validation, Vietnamese provinces datalist, and redirection upon update.
   - `npm run build` succeeds cleanly with 0 type or webpack errors.

## Review Triage Log

- **Reviewer**: Blind Hunter Reviewer subagent (Floor N = 9, reported 15 findings).
- **Triage Decision**:
  - *Applied*: Backdrop click dismissal and `deleteError` banner added to delete confirmation modal in `/properties/my`.
  - *Applied*: Added `encodeURIComponent(id)` to API client property operations.
  - *Deferred (Non-blocking)*: Pagination controls beyond initial 50 items (adequate for MVP).
  - *Deferred (Design Choice)*: Server-side soft deletion flag vs database cascade delete.
