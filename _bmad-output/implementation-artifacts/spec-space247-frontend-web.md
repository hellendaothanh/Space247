---
title: 'Build Space247 Frontend Web Application with Next.js 16 App Router'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247 has a fully functional backend API with pgvector hybrid search and seeded realistic listings, but lacks a web frontend for users to search properties via natural language, filter by real estate criteria, and view detailed listing information.

**Approach:**
1. Initialize and configure the Next.js 16.3.4 project in `frontend/web/` using App Router, TypeScript, Tailwind CSS, and path alias linking to `frontend/shared/` (`@shared/*`).
2. Build the Home Page (`frontend/web/src/app/page.tsx`):
   - Hero section with an interactive Semantic Search Bar connecting to `POST /api/v1/properties/search`.
   - Quick Filters: Purpose (`sale` / `rent`), Price Range, and Property Type (`apartment`, `house`, `villa`, `commercial`).
   - Property Cards grid displaying photo placeholders, title, price, area, bedroom/bathroom stats, location address, and semantic/hybrid similarity badge.
3. Build the Property Detail Page (`frontend/web/src/app/properties/[id]/page.tsx`):
   - Display full property metadata, formatted pricing, coordinates, full description, and quick contact/inquiry actions by fetching `GET /api/v1/properties/{id}`.
4. Configure environment variables in `frontend/web/.env.example` and `frontend/web/.env.local` pointing to backend API (`http://localhost:8080/api/v1`).
5. Ensure successful production build (`npm run build`) and clean type-checking.

</frozen-after-approval>

## Implementation Notes

- Configured `frontend/web/` with Next.js 16.3.4, React 19.2.5, Tailwind CSS v4 (`@tailwindcss/postcss`), and Lucide icons.
- Configured TypeScript path aliases `@/*` to `./src/*` and `@shared/*` to `../shared/*` with twin Turbopack and Webpack resolver configurations in `next.config.ts`.
- Implemented `frontend/web/src/lib/utils.ts` for price formatting (Triệu, Tỷ, VNĐ), property type Vietnamese labels, and high-res Unsplash architectural photo mapping.
- Implemented `frontend/web/src/lib/api.ts` connecting to `http://localhost:8080/api/v1` via `RealEstateApiClient`.
- Built core UI components:
  - `Navbar.tsx`: Sticky responsive header with AI search links and brand identity.
  - `Footer.tsx`: Information footer displaying platform stack specs.
  - `SearchSection.tsx`: AI Semantic Search Bar with sample prompts, Quick Filters (Sale/Rent toggle, Property Type including Land/Đất nền, Cities, Price brackets, and Hybrid Search toggle).
  - `PropertyCard.tsx`: Grid card with listing badges, bedroom/bathroom/area chips, pricing, and semantic match similarity percentage.
- Built App Router pages:
  - `src/app/page.tsx`: Home page with initial property loading, natural language search integration, loading skeletons, and empty state fallbacks.
  - `src/app/properties/[id]/page.tsx`: Full property details page with dynamic metadata, image gallery, specs grid, description, coordinates, agent contact CTAs, and safety advisories.
- Verified TypeScript checks (`npx tsc --noEmit`) and production builds (`npm run build`).
- Verified all 43 backend pytest tests remain 100% passing.

## Review Triage Log

- **Finding 1 (Webpack alias configuration in next.config.ts)**: Configured `webpack(config)` to resolve `@shared` alongside Turbopack alias. Fixed in `next.config.ts`.
- **Finding 2 (Semantic score guard & NaN prevention)**: Clamped percentage and guarded `typeof similarityScore === "number"`. Fixed in `PropertyCard.tsx`.
- **Finding 3 (Missing land option in property filter)**: Added `land` ("Đất nền") to dropdown options. Fixed in `SearchSection.tsx`.
- **Finding 4 (Division by zero guard on area_sqm)**: Guarded `property.area_sqm > 0` and defaulted currency fallback. Fixed in `properties/[id]/page.tsx`.
- **Finding 5 (Accessible label and Tailwind scale utility)**: Added `aria-label` to search input and corrected `active:scale-[0.98]`. Fixed in `SearchSection.tsx`.
- **Finding 6 (URL query sync & pagination)**: Logged as deferred work for frontend search state enhancement.

