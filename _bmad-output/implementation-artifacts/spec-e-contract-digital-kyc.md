---
title: 'KYC Document Retrieval'
type: 'feature'
created: '2026-09-08'
status: 'done'
route: 'dispatch'
baseline_commit: '10329ca1acee940bb578c64e922301de536c1682'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users cannot safely retrieve their submitted CCCD images across devices, and KYC media could be exposed if it is stored or served as public static files.

**Approach:** Store KYC documents behind a storage abstraction, authorize a short-lived retrieval endpoint, and add a protected KYC status and document preview to the existing web profile.

## Boundaries & Constraints

**Always:** Accept CCCD documents as authenticated multipart uploads. In local/development, store files outside public static mounts under `backend/storage/kyc/`; in production, use configured S3-compatible/Cloudflare R2 storage. Persist only storage keys and metadata, never raw base64. `GET /api/v1/kyc/my-documents` requires JWT and returns only the caller's documents, except `superadmin` may request a selected user's documents for review. Return a private temporary stream or pre-signed URL with a fixed 15-minute TTL; never disclose a filesystem path, permanent object URL, or full citizen ID in a response. Profile previews must use authorized document retrieval, visually apply a light blur/watermark, and show an unblurred detail only after an explicit click.

**Never:** Mount `storage/kyc` as a static directory, return KYC media from profile/account DTOs, allow `admin` cross-user KYC access, expose document data to unauthenticated requests, or add a browser-held permanent object-storage credential.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Local upload | Authenticated user provides valid front/back images | Files are stored under a user-scoped private key and metadata is upserted | Unsupported/missing media returns 422; partial write cleans up created data |
| Own retrieval | Verified user requests `my-documents` | Response exposes status, masked citizen ID, and two 15-minute authorized retrieval grants | Missing KYC returns 404 |
| Cross-user retrieval | User A requests User B's document/key | No media or metadata is returned | 403 Forbidden |
| Superadmin review | Superadmin supplies `user_id` | The selected user's protected document references are retrievable for review | Unknown target returns 404 |
| Profile preview | Logged-in user opens profile | KYC card displays verification state and blurred/watermarked previews that open intentionally | Retrieval failure displays a non-sensitive error state |

</frozen-after-approval>

## Code Map

- `backend/src/core/config.py` -- environment configuration convention; extend with private local storage, S3/R2 endpoint, bucket, credentials, and temporary URL TTL settings.
- `backend/src/models/rental_property.py` -- current KYC-adjacent rental model module; add a dedicated KYC model without public-media relationships.
- `backend/src/api/deps.py`, `backend/src/models/user.py` -- JWT current-user and `superadmin` authorization rules to reuse.
- `backend/src/api/v1/router.py` -- register the KYC router under `/api/v1/kyc`.
- `frontend/shared/types.ts`, `frontend/shared/api-client.ts` -- authenticated request conventions; KYC DTOs must contain no permanent paths.
- `frontend/web/src/app/profile/page.tsx` -- authenticated profile loading/error patterns for the KYC card and modal preview.
- `backend/tests/test_auth.py`, `backend/tests/test_alembic_migrations.py` -- API auth and persistence-test patterns to extend with KYC isolation coverage.

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/services/storage.py` and `backend/src/core/config.py` -- implemented private local and S3/R2-compatible storage, content validation, safe key generation, and 900-second retrieval grants.
- [x] `backend/migrations/versions/0013_e_contract_digital_kyc.py`, `backend/src/models/kyc.py`, and `backend/src/models/__init__.py` -- added `user_kyc_verifications` with one-to-one user FK, verification state, masked-safe metadata, and private document keys.
- [x] `backend/src/schemas/kyc.py`, `backend/src/api/v1/endpoints/kyc.py`, and `backend/src/api/v1/router.py` -- provided authenticated multipart verification upload and authorized document retrieval, including superadmin-only targeted review.
- [x] `backend/tests/test_kyc_documents.py` and `backend/tests/test_alembic_migrations.py` -- covered local persistence, retrieval TTL, ownership, superadmin review, and the required User A/User B 403 case.
- [x] `frontend/shared/types.ts`, `frontend/shared/api-client.ts`, and `frontend/web/src/app/profile/page.tsx` -- added retrieval DTO/client calls and status, blurred/watermarked thumbnails, intentional full-view modal, and safe errors.
- [x] `docs/database-design.md`, `docs/api-specs.md`, and `README.md` -- documented storage modes, environment variables, endpoint authorization, TTL, and data boundaries.

**Acceptance Criteria:**
- Given local development, when an authenticated user uploads CCCD front/back images, then they are written under private `backend/storage/kyc/` storage and cannot be fetched from a public static URL.
- Given User A and User B have KYC documents, when User A requests User B's document, then the API responds 403 and returns neither media nor document metadata.
- Given a valid user JWT, when the owner retrieves documents from any device, then the API provides an authorized 15-minute retrieval grant and profile displays safe previews that open only on explicit interaction.
- Given a superadmin and selected user ID, when KYC review is requested, then only the selected user's protected documents are available; non-superadmins cannot use that path.

## Implementation Notes

- Local retrieval uses a 900-second signed API stream; S3/R2 retrieval uses provider pre-signed URLs. All persisted KYC document references are private keys and the database retains only the final four CCCD digits.

## Spec Change Log

## Review Triage Log

- patch — `storage.py` buffers uploads before size rejection; enforce bounded reads to prevent a malformed multipart body exhausting worker memory.
- patch — `storage.py` accepts prefix-only image signatures; decode and bound image dimensions before private persistence.
- patch — replacement upload deletion precedes durable persistence; defer old-key deletion and clean new keys after a failed transaction.
- patch — synchronous S3/R2 calls run in async handlers; move remote storage operations off the event loop.
- patch — invalid non-local backend configuration fails late; validate the backend and required S3/R2 settings before use.
- patch — S3/R2 grants omit explicit no-store response controls; set private cache controls for object and pre-signed retrieval responses.
- patch — profile treats a no-KYC 404 as a failure; retain the normal empty state for that response.
- patch — profile grants expire without refresh; obtain fresh grants immediately before full document view.
- patch — profile omits the requested watermark and eagerly fetches raw media; render a watermark-only protected preview and defer raw retrieval until user action.
- patch — upload, stream, S3/R2, and profile behavior lack route/component coverage; add the smallest practical tests for those contracts.

## Design Notes

The client receives separate temporary retrieval grants per document. Local grants are signed single-purpose API URLs that stream the file after validation; S3/R2 grants use provider pre-signed URLs. Both expire after 900 seconds.

## Verification

**Commands:**
- `uv run pytest -q` from `backend` -- expected: all tests pass, including KYC media isolation and expiry behavior.
- `npx tsc --noEmit` and `npm run build` from `frontend/web` -- expected: zero TypeScript and production-build errors.
