---
title: 'Unified Interactive Room Selection'
type: 'feature'
created: '2026-09-10'
status: 'done'
route: 'oneshot'
baseline_commit: '6891eb752bd0d28e4ea1b0f3c5c7dc0005c2fc0f'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="The user explicitly requested one-shot direct execution">

## Intent

**Problem:** The rental detail page presents the same rooms twice: the current interactive selector and the legacy list at the page bottom. The interactive panel also separates selection from the selected room's action controls.

**Approach:** Make one master-detail section titled “Bảng Chọn Phòng & Dự Toán Chi Phí”. Selecting any card drives its room gallery, calculator and booking actions in the adjacent detail panel.

## Boundaries & Constraints

**Always:** Preserve current safe cost-calculator requests, detailed room dialog, booking appointment flow and reservation/deposit behavior. Use Vietnamese customer copy, retain room status semantics and disable all conversion actions for occupied rooms.

**Never:** Change APIs, pricing formulas, availability rules, booking mutations or the global building media section. Do not retain any duplicate room-card grid outside the unified section.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Available selection | Tenant selects P.101 | Selected card receives primary ring/background; gallery, quote and both actions show P.101 | Latest estimate wins |
| Reserved or occupied selection | Tenant selects a non-available room | Detail still shows room data; conversion actions are unavailable | Disabled status action |
| Sparse room data | Room has no images or floor plan | Detail provides a useful empty state and remains selectable | No broken image/action |
</frozen-after-approval>

## Code Map

- `frontend/web/src/components/rentals/RentalExperience.tsx` owns the current room card grid, active unit, cost request state and detail modal. Replace the separated card/calculator layout with one section.
- `frontend/web/src/app/rentals/[id]/page.tsx` renders a legacy “Danh sách phòng & căn hộ” grid after `RentalExperience`; remove it while retaining its booking modal and `selectedUnit` state.
- `frontend/shared/api-client.ts` provides `calculateRentalLivingCost`; do not alter its API contract.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/web/src/components/rentals/RentalExperience.tsx` -- build the unified two-column selector/detail section with active card styling, room gallery, 1–2 occupant calculator controls and contextual conversion actions.
- [x] `frontend/web/src/app/rentals/[id]/page.tsx` -- delete the duplicate legacy room list while preserving booking modal integration.
- [x] `frontend/web/README.md` -- document the unified room-selection interaction.

**Acceptance Criteria:**
- Given a rental with three rooms, when the page renders, then room information appears in one selector list only.
- Given a tenant selects an available room, when its card becomes active, then detail media, price, calculator and reserve/view actions use that room.
- Given an occupied room, when selected, then its action control says “Phòng đã có người thuê” and cannot initiate conversion.

## Implementation Notes

User explicitly supplied one-shot authorization. No user-visible intent gaps; “Đặt cọc giữ chỗ” uses the existing booking request path because the page's current appointment modal owns the available public flow and a VietQR transaction is created only after host approval.

The selector is the sole room list. It synchronizes selected card state, single-room gallery, cost calculator and selected booking action. The legacy duplicate grid was removed.

## Spec Change Log

## Review Triage Log

## Verification

- `npx tsc --noEmit` -- expected: no errors.
- `npm run build` -- expected: production build succeeds.
