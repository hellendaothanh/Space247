---
title: 'Create Property Listing Page for Space247 Frontend Web'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Space247 frontend platform currently allows browsing, searching, and viewing property details, but lacks a property creation interface. Landlords, agents, and sellers need a dedicated page to post new real estate listings with validation, details, and automatic AI embedding generation.

**Approach:**
1. Create a dedicated page at `/properties/create` (`frontend/web/src/app/properties/create/page.tsx`) with a clean, responsive listing creation form:
   - Basic Info: Title (min 3 chars), Description (min 10 chars).
   - Listing & Property Category: Purpose (Sale vs. Rent), Property Type (Apartment, House, Villa, Land, Commercial).
   - Financials & Dimensions: Price (VND), Area (m2), Bedrooms (optional), Bathrooms (optional).
   - Location: Street Address, Ward/Commune, District, City/Province (prepopulated suggestions for Hanoi, TP.HCM, Da Nang, etc.), Latitude & Longitude (optional/auto-calculated or manual input).
   - Amenities & Features: Multi-select tags (Hồ bơi, Gym, Chỗ để xe, An ninh 24/7, Sổ hồng riêng, Nội thất cao cấp, Thang máy, Ban công, View hồ/sông, v.v.).
   - Image upload / media attachment preview (supporting local image file selection preview with placeholder URL fallback).
2. Validate form inputs with `zod` client-side schema matching backend constraints (`min_length`, positive price/area, valid ranges).
3. Connect submission to the backend API `POST /api/v1/properties` via `apiClient.createProperty()`, which automatically computes 768-dim embeddings via FastEmbed/E5.
4. Display clear success notification toast/banner, error feedback per field, and redirect the user smoothly to the created property detail page (`/properties/[id]`).
5. Update `Navbar.tsx` "Đăng tin" button to link directly to `/properties/create`.
6. Verify TypeScript correctness (`npx tsc --noEmit`) and Next.js production build (`npm run build`).

</frozen-after-approval>

## Implementation Notes

- Added `zod` dependency to `frontend/web/`.
- Created comprehensive `/properties/create` page with:
  - Six structured form sections: Purpose & Type, Title & Description, Financials & Area, Location & Coordinates, Amenities, and Image Upload.
  - Automatic dynamic formatting helper for Vietnamese Currency (`tỷ`, `triệu`, `đ`).
  - Drag-and-drop file upload with preview cards, deletion action, and client-side MIME/size validation (up to 10MB).
  - Integration with `apiClient.createProperty()` to submit data directly to backend `POST /api/v1/properties`.
  - Double-submit protection disabling action button on submission and redirect.
- Linked Navbar "Đăng tin" button to `/properties/create`.

## Review Triage Log

- **Subagent**: Blind Hunter Reviewer (`f18c2580-2586-4bcc-b2e9-e23db27990b8`).
- **Findings & Verdicts**:
  1. *Drag-and-drop file upload missing handlers*: **patch** (high) - Added `onDragOver`, `onDragLeave`, `onDrop` event handlers and active drag state styling.
  2. *Missing validation error elements for city, district, ward, coordinates*: **patch** (high) - Added error alert text beneath all corresponding input fields.
  3. *Double-submission window during redirect*: **patch** (high) - Added guard `if (isPending || successInfo) return;` preventing repeated submission clicks.
  4. *File input reset value*: **patch** (medium) - Reset `e.target.value = ""` upon change so identical files can be re-selected.
  5. *File size and type validation*: **patch** (medium) - Enforced image MIME check and 10MB file limit with user notification.
  6. *Currency helper shorthand*: **patch** (low) - Added real-time badge calculating VND denomination in billion (`tỷ`) and million (`triệu`).
  7. *Image upload backend persistence*: **defer** (medium) - Current database and schema do not yet have an `images` table/array column; deferred to dedicated media storage story.


