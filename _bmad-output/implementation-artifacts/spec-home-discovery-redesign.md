---
title: 'Modern homepage discovery experience'
type: 'feature'
created: '2026-09-11'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '0e826b197918119f3d6fc946883ad13d575a63bd'
context: []
---

<frozen-after-approval>
## Intent

Redesign the Vietnamese Space247 homepage as one cohesive modern property discovery experience. The user explicitly authorizes one-shot implementation without another approval checkpoint. Deliver a polished glass header, light architectural hero, three-mode floating search, category navigation, distinct project/sale/rental collections and a commercial footer.

## Boundaries & Constraints

Preserve authentication, favorites, comparison, notifications, map view and existing APIs. Use actual listing images with error fallback. Never invent counts, legal certificates, ownership guarantees, direction, developer logos or regulatory certification. Display unavailable metadata honestly or omit it. Existing private KYC workflows are out of scope. No remote operations, deployment, migration or secrets changes. Vietnamese user-facing strings; English source identifiers. Ownership: implementation agent owns homepage discovery components, Navbar, Footer, PropertyCard, closely related SDK/filter adapters and docs; other agents may inspect concurrently, never revert unrelated changes.

## Expected behavior

Sale mode offers house/apartment/land/commercial filters and VND billion price bands; rent mode offers room/studio/whole-house/commercial and monthly million bands; project mode offers appropriate project discovery options without pretending unsupported backend fields exist. Switching modes clears incompatible category/price/advanced values. AI toggle is explicit and genuinely controls semantic versus conventional search; non-AI search must not silently invoke semantic search. Categories apply filters to results below, with accurate counts labeled as loaded counts if not global. Handle loading, partial failures, zero results and missing images. Mobile has no horizontal document overflow; category rail itself scrolls. Drawer/dialog controls are labeled, keyboard accessible, dismissible, and return focus.

</frozen-after-approval>

## Code Map

- `frontend/web/src/app/page.tsx`: currently one property list with semantic search and map view. Preserve URL listing_type/view navigation, add separate collections and category selection.
- `frontend/web/src/components/SearchSection.tsx`: existing FilterState and advanced filter drawer. Replace dark hero with light gradient and decorative architectural graphic, exact H1 "Tìm Không Gian Sống Hoàn Hảo Cho Bạn". Three tabs: Mua Bán Nhà Đất, Thuê Nhà & Phòng Trọ, Dự Án Mới. Unified responsive pill with location/category/price/filter/search and AI switch.
- `frontend/web/src/components/Navbar.tsx`: authentication, notifications, favorites and responsive navigation already exist. Preserve these; hide raw role label, compact avatar/name, keep superadmin link conditional and Host Portal available appropriately.
- `frontend/web/src/components/common/PropertyCard.tsx`: currently ignores property.images in favor of placeholders. Prefer real images, 16:10 inset rounded-xl media, status and animated favorite, prominent monthly/sale price and computed sale price per sqm, factual RentalBadges.
- `frontend/web/src/components/Footer.tsx`: four-column foundation. Add cities Hanoi/HCMC/Da Nang/Can Tho sale/project links, rental destinations Bach Khoa/Tay Ho/District 7, host/contracts/mortgage/map support links to real destinations. Keep hotline 1900 247 247 and copyright 2026; privacy commitment wording without claiming certification. Unconfigured social/legal destinations must not be fake links.
- `frontend/shared/types.ts`, `api-client.ts`: PropertyResponse, ProjectResponse with average_price_per_sqm, RentalProperty and list/search methods. Check supported filters and consume real contracts; no unnecessary backend expansion.
- `frontend/web/src/app/layout.tsx`: global max-width container and shared header/footer; preserve providers.

## Tasks & Acceptance

- [ ] Redesign Navbar, SearchSection and homepage composition with responsive spacing, teal/blue brand accents, category rail and functional three-mode search.
- [ ] Render "Dự Án Đô Thị Nổi Bật", "Bất Động Sản Bán Mới Nhất", "Cho Thuê & Phòng Trọ Tiện Nghi" using real APIs. Large project cards show available progress, developer, price range and average per sqm; rentals use real units/cost/rules metadata.
- [ ] Polish PropertyCard and modernize Footer without fabricating metadata or links.
- [ ] Synchronize root README, frontend/web/README and a focused docs feature guide describing behavior and limits.
- [ ] Run TypeScript and production build, plus meaningful filter tests if logic changes; fix failures.

Acceptance: Given a transaction mode, selecting category and price then searching applies that mode's criteria. Given the AI switch is off, conventional filtering occurs. Given an API failure, other successful collections remain visible with an actionable error. Given mobile viewport, inputs/cards/actions remain usable. Given missing listing metadata, no unsupported badge/count is shown. Given a superadmin, its portal link remains available while raw role text disappears.

## Implementation Notes

User explicitly selected one-shot execution; no additional approval required. Single cohesive discovery redesign, no irreversible changes.

## Verification

- `cd frontend/web && npx tsc --noEmit` succeeds.
- `cd frontend/web && npm run build` succeeds.
- Inspect responsive behavior and search wiring; report any unverified browser checks accurately.
