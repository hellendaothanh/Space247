---
status: complete
baseline_commit: 50f5b295c2a78e9956715258cd50dbccf4c87ee3
context:
  - backend/src/models/user.py
  - backend/src/schemas/user.py
  - backend/src/api/deps.py
  - backend/src/api/v1/router.py
  - backend/scripts/seed_properties.py
  - frontend/shared/types.ts
  - frontend/shared/api-client.ts
  - frontend/web/src/components/Navbar.tsx
---

# Technical Specification: User Management & Superadmin RBAC

<frozen-after-approval>

## 1. Context & Objectives
Space247 requires enterprise-grade identity and access management (IAM) with Role-Based Access Control (RBAC).
Key objectives:
1. Expand the `UserRole` enum to support `superadmin`, `admin`, `agent`, `user`.
2. Introduce account management flags and metadata: `is_active`, `phone_verified`, `last_login_at`.
3. Seed default `superadmin@space247.vn` with full administrative privileges.
4. Provide user self-management APIs:
   - Profile retrieval with aggregate statistics (`GET /api/v1/users/me`)
   - Profile updating (`PUT /api/v1/users/me`)
   - Secure password change (`POST /api/v1/users/me/change-password`)
5. Provide administrative management APIs restricted to `superadmin`:
   - Paginated user list with filtering and search (`GET /api/v1/admin/users`)
   - User creation by admin (`POST /api/v1/admin/users`)
   - User detail inspection (`GET /api/v1/admin/users/{id}`)
   - User editing (role assignment, status toggle, password reset) (`PUT /api/v1/admin/users/{id}`)
   - Soft deletion / deactivation (`DELETE /api/v1/admin/users/{id}`)
6. Update the Shared TypeScript SDK with type definitions and API client methods.
7. Implement Web UI:
   - User profile and password management page (`/profile`)
   - Superadmin management dashboard and DataTable (`/admin/users`)
   - Role-gated navigation in Header/Navbar
8. Implement Mobile UI:
   - User profile screen with update capabilities and Change Password bottom sheet.
9. Maintain enterprise technical documentation and 100% test coverage.

## 2. Tasks & Acceptance

### Task 1: Database & Migration 0007
- [x] Add `phone_verified` and `last_login_at` to `backend/src/models/user.py`, and expand `UserRole` to include `SUPERADMIN = "superadmin"`.
- [x] Create Alembic migration `backend/migrations/versions/0007_user_management_superadmin_rbac.py` and run `alembic upgrade head`.
- [x] Update `backend/scripts/seed_properties.py` to seed `superadmin@space247.vn` (password `Password123@`, role `superadmin`). Run seed script.
*Acceptance:*
- Given the database is upgraded to revision `0007`, when inspecting PostgreSQL schema for table `users`, then columns `phone_verified`, `last_login_at`, and `is_active` are present.
- Given seed script executes, when logging in as `superadmin@space247.vn`, then credentials succeed and user role is `superadmin`.

### Task 2: Backend Schemas & RBAC Dependencies
- [x] Update `backend/src/schemas/user.py` with `UserRole.SUPERADMIN`, `UserCreateByAdminRequest`, `UserUpdateByAdminRequest`, `UserProfileUpdateRequest`, `ChangePasswordRequest`, `UserPaginationResponse`, `UserProfileDetailResponse`.
- [x] Add `require_roles` dependency factory and `get_current_superadmin_user` to `backend/src/api/deps.py`.
- [x] Ensure `get_current_active_user` verifies `is_active is True`.
*Acceptance:*
- Given an active user JWT token, when accessing protected endpoints, then the user is resolved.
- Given an inactive user (`is_active=False`), when attempting authentication, then HTTP 403 is returned.
- Given a user with role `user` or `agent`, when attempting to access a superadmin endpoint, then HTTP 403 is returned.

### Task 3: Backend User Self-Management & Admin Endpoints
- [x] Create `backend/src/api/v1/endpoints/users.py` (`GET /me`, `PUT /me`, `POST /me/change-password`).
- [x] Create `backend/src/api/v1/endpoints/admin_users.py` (`GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`).
- [x] Register routes in `backend/src/api/v1/router.py`.
*Acceptance:*
- Given an authenticated user, when calling `GET /api/v1/users/me`, then user info along with listing/favorite counts is returned.
- Given an authenticated user, when calling `PUT /api/v1/users/me`, then profile info is updated.
- Given an authenticated user, when calling `POST /api/v1/users/me/change-password` with valid old password and new password >= 8 characters, then password hash is updated.
- Given a superadmin user, when calling `GET /api/v1/admin/users`, then filtered paginated user records are returned.
- Given a superadmin user, when calling `DELETE /api/v1/admin/users/{id}`, then target user has `is_active = False` (soft delete).

### Task 4: Shared TypeScript SDK
- [x] Update `frontend/shared/types.ts` with `superadmin` role and admin user DTOs.
- [x] Update `frontend/shared/api-client.ts` with user self-management and admin user management methods.
*Acceptance:*
- Given client code calling `apiClient.getAdminUsers(...)` or `apiClient.updateProfile(...)`, types compile cleanly.

### Task 5: Frontend Web Implementation
- [x] Create `/profile` page with personal info and password change tabs.
- [x] Create `/admin/users` page with user data table, filters, search, edit role modal, toggle active/block modal, add user modal.
- [x] Update `Navbar.tsx` to conditionally render link to `/admin/users` only for `superadmin`.
*Acceptance:*
- Given a superadmin user, when viewing the navbar, then "Quản trị người dùng" / "Quản lý người dùng" link is visible.
- Given a normal user or agent, when navigating to `/admin/users`, then access is restricted/redirected.
- Given a user on `/profile`, when changing password with mismatch or invalid length, client validation indicates error; when submitting valid form, password update succeeds.

### Task 6: Frontend Mobile Integration
- [x] Update `frontend/mobile/lib/models/user.dart` and `frontend/mobile/lib/services/auth_service.dart`.
- [x] Implement `frontend/mobile/lib/screens/profile_screen.dart` with profile update and change password modal.
*Acceptance:*
- Given mobile user, user can view role badge and update profile / trigger change password.

### Task 7: Pytest Coverage & Documentation
- [x] Create `backend/tests/api/v1/test_admin_users.py` and `backend/tests/api/v1/test_user_profile.py`.
- [x] Run test suite with 100% pass rate.
- [x] Update `docs/api-specs.md`, `docs/database-design.md`, and `docs/security-privacy.md`.
*Acceptance:*
- `uv run pytest` passes 100%.
- `npx tsc --noEmit` and `npm run build` succeed in `frontend/web`.

</frozen-after-approval>
