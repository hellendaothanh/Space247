---
title: 'Space247 Multi-Platform Property Detail Page Fixes and Enhancements'
type: 'feature'
created: '2026-09-04'
baseline_commit: '5a63661'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Property Detail page across Web and Mobile lacks dynamic agent contact information, renders hardcoded placeholder images instead of user-uploaded property images, renders raw unformatted markdown text, and contains a non-functional Share button. Additionally, the backend Property model lacks an images column and User lacks an avatar_url column, preventing uploaded photos and agent profile updates from persisting.

**Approach:** Add images (PostgreSQL TEXT[]) to properties and avatar_url to users via an Alembic migration; update backend schemas (PropertyResponse, PropertyDetailResponse, UserUpdate) and endpoints (GET /properties/{id}, POST/PUT /properties, PUT /auth/me) to return full agent data and persist images. Enhance Web with PropertyGallery (carousel/grid with fallback), PropertyShareButton (Web Share API + clipboard toast), react-markdown with remark-gfm, and dynamic Agent Card (tel:, mailto:). Enhance Mobile with share_plus, url_launcher, flutter_markdown, and image carousel slider with cached_network_image.

## Boundaries & Constraints

**Always:**
- Persist images as a real PostgreSQL array of strings and return it as images: string[] in API responses.
- Load the listing owner in GET /properties/{id} via eager loading (selectinload(Property.owner)) and map to agent object { id, full_name, email, phone_number, avatar_url, role }.
- Fall back to standard placeholder images only when property.images is empty.
- Keep all existing pytest suites at 100% PASS and maintain clean production builds (npm run build).

**Never:**
- Do not lose existing property attributes, spatial indexing, or search vector compatibility.
- Do not break backward compatibility for existing properties that have empty image arrays.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Property with multiple images | POST /properties with images: ["url1", "url2"] | Property created, DB stores images, GET /properties/{id} returns both images in order | Validated non-empty URLs |
| Property with no images | POST /properties with images: [] or omitted | Property created with images: [], frontend falls back to category placeholder | Graceful fallback without broken img |
| Fetch Property with owner | GET /properties/{id} | Returns PropertyDetailResponse with agent object populated from owner | If user_id is null, agent is null |
| Update User Profile | PUT /auth/me with { phone_number: "0912345678", avatar_url: "https://..." } | Current user updated in DB and updated UserResponse returned | 401 if unauthenticated |
| Web Share on mobile/desktop | Click Chia sẻ | Uses navigator.share if supported, else copies URL to clipboard and shows toast | Catch cancellation silently |

</frozen-after-approval>

## Code Map

- backend/migrations/versions/0005_add_property_images_and_user_avatar.py -- Alembic migration adding images to properties and avatar_url to users.
- backend/src/models/property.py -- Add images column (Mapped[list[str]]) to Property.
- backend/src/models/user.py -- Add avatar_url column to User.
- backend/src/schemas/user.py -- Add UserUpdate DTO and add avatar_url, phone_number to UserResponse.
- backend/src/schemas/property.py -- Add PropertyAgentResponse, PropertyDetailResponse, update PropertyBase, PropertyCreate, PropertyUpdate, PropertyResponse to support images and agent.
- backend/src/api/v1/endpoints/properties.py -- Eager load owner in get_property, support images in create_property and update_property.
- backend/src/api/v1/endpoints/auth.py -- Add PUT /auth/me to update current users profile (phone, avatar_url, full_name).
- backend/tests/test_alembic_migrations.py -- Update migration head to 0005.
- backend/tests/api/v1/test_properties.py -- Pytest test suite for property detail agent info and images array.
- frontend/shared/types.ts -- Add PropertyAgent interface and images / agent to PropertyResponse / PropertyDetailResponse.
- frontend/web/src/components/PropertyGallery.tsx -- Image gallery with carousel slider, thumbnail selector, and fallback placeholder.
- frontend/web/src/components/PropertyShareButton.tsx -- Share button with Web Share API and clipboard copy toast.
- frontend/web/src/app/properties/[id]/page.tsx -- Integrate gallery, markdown description, dynamic agent card, and share button.
- frontend/web/src/app/properties/create/page.tsx -- Pass uploaded images array in createProperty payload.
- frontend/mobile/lib/models/property.dart -- Add images and PropertyAgent model.
- frontend/mobile/lib/screens/property_detail_screen.dart -- Add native share button, image carousel, markdown body, and dynamic agent contact actions.

## Tasks & Acceptance

**Execution:**
- [ ] backend/migrations/versions/0005_add_property_images_and_user_avatar.py -- Create migration for properties.images and users.avatar_url.
- [ ] backend/src/models/property.py & backend/src/models/user.py -- Update SQLAlchemy models.
- [ ] backend/src/schemas/user.py & backend/src/schemas/property.py -- Update Pydantic schemas.
- [ ] backend/src/api/v1/endpoints/auth.py -- Implement PUT /me.
- [ ] backend/src/api/v1/endpoints/properties.py -- Update get_property, create_property, and update_property to handle images and agent.
- [ ] backend/tests/test_alembic_migrations.py & backend/tests/api/v1/test_properties.py -- Update migration head test and add property detail test.
- [ ] frontend/shared/types.ts -- Update shared TypeScript interfaces.
- [ ] frontend/web/src/components/PropertyGallery.tsx -- Build image gallery carousel component.
- [ ] frontend/web/src/components/PropertyShareButton.tsx -- Build share button with toast.
- [ ] frontend/web/src/app/properties/[id]/page.tsx -- Wire up gallery, markdown, agent card, and share button.
- [ ] frontend/web/src/app/properties/create/page.tsx -- Include uploaded images in create payload.
- [ ] frontend/mobile/lib/models/property.dart & property_detail_screen.dart -- Update Dart model and detail screen.

**Acceptance Criteria:**
- Given a property with uploaded images, when GET /api/v1/properties/{id} is queried, it returns images matching the uploaded URLs and agent with full contact details.
- Given an authenticated user, when PUT /api/v1/auth/me is called with new phone and avatar, the users profile is updated and returned.
- Given the Web Property Detail page, clicking Chia sẻ copies the link to clipboard with toast notification or triggers native share.
- Given the Web Property Detail page, the description renders formatted Markdown (headers, lists, bold) via react-markdown and remark-gfm.
- Given the Web Property Detail page, the Agent Card displays the agents real name, avatar, and active tel: / mailto: links.
- Given the Mobile Property Detail screen, it renders image carousel, markdown description, and active call/email actions.
- 100% pytest pass across all backend suites and clean Next.js production build (npm run build).

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- cd backend && uv run pytest tests/api/v1/test_properties.py tests/test_alembic_migrations.py -- expected: PASS 100%
- cd backend && uv run pytest -- expected: PASS 100%
- cd frontend/web && npx tsc --noEmit -- expected: 0 errors
- cd frontend/web && npm run build -- expected: SUCCESS
