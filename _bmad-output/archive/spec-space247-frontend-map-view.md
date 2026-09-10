---
title: 'Integrate Interactive Map View for Space247 Frontend Web'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'oneshot'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Space247 homepage currently only displays search and listing results in a traditional Grid view. Users cannot visually explore property locations on an interactive geographical map, compare proximity to transport hubs/districts, or inspect quick listing summaries by clicking markers.

**Approach:**
1. Install `leaflet` and `@types/leaflet` in `frontend/web/`.
2. Create an interactive, client-side Map component (`frontend/web/src/components/PropertyMap.tsx` / `PropertyMapClient.tsx`) utilizing Leaflet with OpenStreetMap tiles:
   - Dynamic marker generation based on `latitude` and `longitude` coordinates of property results.
   - Interactive popups displaying thumbnail image, formatted price, area, bedroom stats, and direct link to `/properties/[id]`.
   - Auto-fit map bounds to encompass all visible markers across Hanoi and Ho Chi Minh City, with sensible zoom fallbacks.
3. Update `frontend/web/src/app/page.tsx` with a Grid vs. Map view toggle control in the results header bar.
4. Support split-view or full-width map view on desktop and mobile, dynamically responding to search query and filter updates.
5. Verify TypeScript validation (`npx tsc --noEmit`) and successful production build (`npm run build`).

</frozen-after-approval>

## Implementation Notes

- Added `leaflet` and `@types/leaflet` dependencies to `frontend/web/`.
- Imported Leaflet CSS in `frontend/web/src/app/globals.css`.
- Built `PropertyMap.tsx` with Next.js dynamic client loading (`ssr: false`) and fallback loading skeleton.
- Built `PropertyMapClient.tsx` featuring:
  - Custom HTML price-pill markers color-coded by listing type (Sale vs. Rent).
  - OpenStreetMap tiles with attribution.
  - Interactive popups with XSS escaping (`escapeHtml`), thumbnail preview, price tag, similarity score badge, and quick details.
  - SPA navigation integration using Next.js `useRouter().push()`.
  - Robust bounds fitting with coordinate validation.
- Updated `frontend/web/src/app/page.tsx` to include Grid and Map switcher buttons with active counts.

## Review Triage Log

- **Subagent**: Blind Hunter Reviewer (`fdfa0bf8-aee1-4728-a1fc-d23b5a7348e8`).
- **Issues addressed**:
  1. *Unstable effect dependency resetting pan/zoom*: Fixed by keeping `onSelectProperty` in `useRef` and decoupling marker recreation from selection state.
  2. *Popup click routing*: Added event delegation on popup button with `data-property-id` executing Next.js client-side router.
  3. *Zero coordinate validation*: Excluded `(0, 0)` or invalid coordinates outside `[-90, 90]` / `[-180, 180]`.
  4. *Tile sizing glitch*: Added `map.invalidateSize()` after DOM mount.
  5. *XSS hardening*: Added HTML entity escaping for title and address strings rendered into Leaflet popup innerHTML.


