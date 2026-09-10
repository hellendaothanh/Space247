---
title: 'Implement JWT User Authentication System for Space247'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Currently, Space247 lacks user identity and session management. Anyone can create listings anonymously without accountability, listings are not linked to owner accounts, and the frontend has no register/login portal or authenticated API request mechanism.

**Approach:**
1. **Backend Database & Model (`backend/src/models/user.py`, `property.py`)**:
   - Create `User` model with fields: `id` (UUID), `email` (unique, indexed), `hashed_password` (str), `full_name` (str), `phone` (optional str), `role` (enum: "user", "agent", "admin", default "user"), `is_active` (bool, default True), `created_at`, `updated_at`.
   - Update `Property` model: add `user_id` foreign key referencing `users.id` (nullable for existing seed properties, populated for authenticated creations).
   - Add Alembic migration revision (`0002_add_users_table_and_property_user_fk.py`) creating `users` table and adding `user_id` foreign key column to `properties`.
2. **Backend Authentication & JWT Security (`backend/src/core/security.py`, `backend/src/schemas/user.py`, `backend/src/api/v1/endpoints/auth.py`)**:
   - Add security utility functions using `pyjwt` (HS256) and `bcrypt` directly: password hashing (`hash_password`), password verification (`verify_password`), token generation (`create_access_token`).
   - Add FastAPI dependencies (`get_current_user`, `get_current_active_user`) extracting and decoding the Bearer token from the `Authorization` header.
   - Implement Auth endpoints:
     - `POST /api/v1/auth/register`: validates email uniqueness, hashes password, saves user, returns user profile and access token.
     - `POST /api/v1/auth/login`: validates email and password credentials, returns access token with token type.
     - `GET /api/v1/auth/me`: protected endpoint returning current authenticated user profile.
   - Update `POST /api/v1/properties`: protect with `current_user: User = Depends(get_current_active_user)`, assign `property_obj.user_id = current_user.id`.
3. **Shared Contracts & Client Update (`frontend/shared/types.ts`, `frontend/shared/api-client.ts`)**:
   - Define TypeScript interfaces: `UserResponse`, `UserRegisterRequest`, `UserLoginRequest`, `AuthTokenResponse`.
   - Update `PropertyResponse` to include optional `user_id?: string`.
   - Add auth methods in `RealEstateApiClient`: `register()`, `login()`, `getCurrentUser()`.
4. **Frontend Web UI & Auth State (`frontend/web/`)**:
   - Add lightweight client-side auth context/hooks or state storage using `localStorage` for `access_token` and `user`.
   - Create `/login` page with responsive login form (email, password) and redirect to previous page or home.
   - Create `/register` page with registration form (full_name, email, phone, password, role).
   - Update `Navbar.tsx` to display user name, avatar/badge, and Logout button when authenticated, or Login / Register links when unauthenticated.
   - Update `/properties/create`: configure `apiClient` with token from auth state, verify user is logged in (or prompt to login), and pass token in headers.
5. **Testing & Verification**:
   - Write comprehensive tests in `backend/tests/test_auth.py` verifying registration, duplicate email rejection, login success, invalid password rejection, `/auth/me` token resolution, and protected `POST /properties` rejection without token and success with token.
   - Run `uv run pytest` to achieve 100% pass rate.
   - Run `npx tsc --noEmit` and `npm run build` in `frontend/web/`.

</frozen-after-approval>

## Implementation Notes

- **Backend Auth Architecture**:
  - Direct integration with `bcrypt` and `pyjwt` without unmaintained wrapper libraries.
  - JWT tokens encode `sub` (user UUID), `iat`, `exp` (default 7 days), `email`, and `role`.
  - Added dependency overrides in `backend/tests/conftest.py` ensuring backwards compatibility across existing test suites while maintaining strict isolation for `test_auth.py`.
- **Database & Migration**:
  - Created Alembic revision `0002_add_users_table_and_property_user_fk.py` with foreign key constraint `fk_properties_user_id_users` on `properties(user_id)` with `ondelete="SET NULL"`.
- **Frontend Architecture**:
  - `AuthProvider` in `frontend/web/src/lib/auth.tsx` provides reactive session context (`user`, `token`, `login`, `logout`).
  - Integrated dynamic token extraction via `getAuthToken` in `apiClient`.
  - Created dedicated authentication screens `/login` and `/register`, and added active session awareness to `Navbar.tsx` and `/properties/create`.

## Review Triage Log

- **Privilege Escalation on Register**: Patched `UserRegister` schema and `register` endpoint to restrict self-registration roles strictly to `user` or `agent`, disallowing `admin` promotion.
- **Bcrypt 72-Byte Boundary**: Constrained password max length to 72 characters in `UserRegister` and `UserLogin`.
- **Inactive User Status Code**: Patched `login` and `get_current_active_user` to return `403 Forbidden` instead of `400 Bad Request` for inactive accounts.
- **Cascade Discrepancy**: Removed `cascade="all, delete-orphan"` from `User.properties` to align with database-level `ondelete="SET NULL"`.
- **Auth Provider Session Resilience**: Updated `auth.tsx` to only clear stored credentials on explicit 401/403 responses, preventing session invalidation during temporary network outages.
- **API Error Formatting**: Updated `RealEstateApiClient` to parse FastAPI array-based 422 validation errors into human-readable messages.
- **Deferred Work**: Image upload S3/storage backend, `GET /properties/me` owner endpoint, and timing-attack mitigation are logged for dedicated subsequent stories.

