---
title: 'Redesign Premium Home Search and Property Detail'
type: 'feature'
created: '2026-09-08'
baseline_commit: '1476d75ccfa9b5a9b1be6e7dacbb4e98abff72c1'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Space247's home filters are fragmented and its property detail page does not provide the polished visual hierarchy, booking focus, or rental-fee clarity expected from a premium real-estate product.

**Approach:** Replace the home controls with one responsive segmented floating search bar and rebuild the property detail experience around a mosaic gallery, a content-first two-column layout, structured rental cards, a Leaflet amenity map, and a sticky contact-and-booking sidebar.

## Boundaries & Constraints

**Always:** Preserve current natural-language search and supported structured criteria; map bedroom and area selections to the existing search contract, and fold direction and amenity choices into the natural-language query. Keep existing image fallbacks, Markdown rendering, Leaflet map/POI behavior, favorites, sharing, mortgage calculator, and agent contact data. Make every new control keyboard-accessible and mobile-first.

**Never:** Do not add a backend search schema, booking persistence endpoint, or property orientation field. The booking modal may collect a preferred time and direct the visitor to the supplied agent phone/email, but must not post to the rental-unit inquiry endpoint.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Sale or rental search | User selects a tab, type, price, or advanced search value then submits | The existing search request receives sale/rent-sensitive prices, supported bedroom/area fields, and AI search remains enabled | Omit empty criteria |
| Unsupported advanced metadata | User selects direction or amenity | Values enrich the natural-language query without unsupported API fields | Selection remains visible in the drawer |
| Sparse rental data | Cost or rule value is absent, zero, or false | The card is hidden or softly de-emphasized; no false free-price or unavailable value is shown | Preserve valid zero/false semantics where explicitly meaningful |
| Few gallery images | Property has fewer than five images | Mosaic repeats available images or uses placeholders; mobile shows a single primary image | No broken image or empty grid |
| Booking intent | User opens booking modal | Modal shows selected property, time preference, and usable agent contact actions | No unsupported booking submission |

</frozen-after-approval>

## Code Map

- `frontend/web/src/components/SearchSection.tsx` -- Home hero, current filter state, AI search handoff, sale/rental price mapping, and quick tags.
- `frontend/web/src/app/page.tsx` -- Converts `FilterState` into the shared search request; must forward supported advanced criteria.
- `frontend/shared/types.ts` -- Existing `PropertySearchQuery` supports `min_bedrooms`, `min_area_sqm`, and `max_area_sqm`, but not direction or generic amenities.
- `frontend/web/src/app/properties/[id]/page.tsx` -- Server-rendered property detail composition, Markdown, map, calculator, and agent sidebar.
- `frontend/web/src/components/PropertyGallery.tsx` -- Client image interaction and fallback ownership; replace carousel presentation with responsive mosaic/full-gallery behavior.
- `frontend/web/src/components/RentalDetails.tsx` -- Rental costs and rules; convert text lists to icon cards and suppress unknown values.
- `frontend/web/src/components/PropertyDetailMap.tsx` / `PropertyDetailMapClient.tsx` -- Dynamic Leaflet map and existing school, hospital, and supermarket POI filters.
- `frontend/web/src/components/PropertyShareButton.tsx` -- Existing native-share/clipboard behavior to retain in the sidebar.
- `frontend/web/src/components/PropertyBookingModal.tsx` -- New client-only contact-oriented scheduling modal; no booking API exists for general properties.

## Tasks & Acceptance

**Execution:**
- [x] `SearchSection.tsx` and `page.tsx` -- Implement responsive sale/rental tabs, segmented keyword/type/price controls, advanced filter drawer, quick tags, and CTA search request mapping.
- [x] `PropertyGallery.tsx` -- Implement desktop 60/40 five-image mosaic, a full-gallery trigger, fallback imagery, and a compact mobile gallery.
- [x] `RentalDetails.tsx` -- Render costs and rules as icon cards that omit unknown amounts and unavailable amenities.
- [x] `PropertyBookingModal.tsx` -- Add a client booking-intent modal with preference fields and safe agent contact actions.
- [x] `properties/[id]/page.tsx` -- Compose premium title/specification content, map section, Markdown typography, and a `lg:sticky` 65/35 action sidebar while retaining existing utilities.

**Acceptance Criteria:**
- Given any viewport, when the home search is displayed, then the controls remain operable as a single segmented bar on desktop and a stacked or scrollable touch-friendly layout on smaller screens.
- Given a selected sale or rental tab, when the visitor picks a price range and submits, then the correct sale or monthly-rent bounds are used.
- Given a property with images, when the detail page is viewed on desktop, then one dominant image and four supporting images form a rounded mosaic with a full-gallery action.
- Given incomplete rental data, when pricing and rules are displayed, then unavailable values are not rendered as `0` or `Chưa cung cấp`.
- Given a desktop detail page, when the visitor scrolls, then the action sidebar remains sticky without overlapping page content; on mobile it follows the content normally.
- Given the revised web application, when TypeScript and production build commands run, then both complete with no errors.

## Implementation Notes

- Added client-side advanced filtering that maps supported criteria directly and adds direction/amenity choices to the natural-language query.
- Kept general-property booking contact-only because the API exposes booking persistence only for rental units.
- Verified TypeScript and the optimized Next.js production build.

## Spec Change Log

## Review Triage Log

## Design Notes

The persistent desktop hierarchy is gallery first, then a two-column content/action composition. Mobile collapses the visual density before interaction: gallery, property essentials, actions, content, then supporting tools.

## Verification

**Commands:**
- `cd frontend/web && npx tsc --noEmit` -- expected: 0 errors
- `cd frontend/web && npm run build` -- expected: successful optimized production build
