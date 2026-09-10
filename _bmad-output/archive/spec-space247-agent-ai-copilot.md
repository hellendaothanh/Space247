---
title: 'Agent AI Co-Pilot'
type: 'feature'
created: '2026-09-04'
baseline_commit: '2db3e968de6623a01df495b859c4771da497a448'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Real estate agents spend significant time drafting SEO-friendly listing descriptions, manually extracting specs from rough notes or title deeds (sổ đỏ), and often price properties blindly without statistical neighborhood market comps, leading to overpriced listings that fail to sell or underpriced listings that lose revenue.

**Approach:** Build a comprehensive Agent AI Co-Pilot tool suite for Space247:
1. **AI Listing Generator**: Ingests bullet points / notes and optional title deed / floorplan images, using Gemini Multimodal LLM to generate SEO-optimized titles, rich Vietnamese Markdown descriptions, and auto-extracted technical specifications.
2. **Smart AVM Pricing Advisor (Automated Valuation Model)**: Uses PostGIS spatial queries (`ST_DWithin` / GiST index) to fetch neighborhood comps, applies Weighted K-Nearest Neighbors (distance + area decay), generates price ranges (low, recommended, high), confidence scores, and deviation warnings against user-proposed prices.
3. **Frontend Integration**:
   - Web: AI Listing Generator modal with auto-fill into property create/edit forms, and interactive AVM Pricing Advisor gauge bar with market deviation warnings.
   - Mobile: "AI Hỗ trợ soạn tin" modal/dialog and AVM pricing hint widget under the price input field.

**Decisions:**
- Adopt Option A (Flexible Valuation Radius & Dynamic Confidence Adjustment):
  - Default search radius is 2.5 km.
  - If fewer than 2 comparable properties are found, automatically expand the search radius incrementally up to 6.0 - 8.0 km.
  - Dynamically scale down confidence score (e.g. from 0.85-0.95 down to 0.40-0.65) when expanded, and append clear guidance notes explaining the wider search area.
  - Calculate percentage deviation between proposed price and AVM market estimate, providing 3 tier assessments: "Thấp hơn thị trường" (bargain/liquidity), "Định giá hợp lý" (market fit), "Cao hơn thị trường" (overpriced warning).

## Boundaries & Constraints

**Always:**
- Secure `/api/v1/agent/*` endpoints with Bearer JWT requiring `agent` or `admin` role.
- Provide safe fallback content for AI listing generation if Gemini API key is missing or calls time out.
- Ensure AVM uses spatial PostGIS queries or Haversine fallback with radius expansion if comps are sparse.
- Cache AVM valuation calculations in Redis with a 15-minute TTL.
- Validate that estimated price calculations handle `Decimal` and `float` gracefully without `TypeError`.

**Never:**
- Do not allow unauthenticated or regular users to access agent-only co-pilot endpoints.
- Do not crash if no comps are found in radius; gracefully expand radius and return baseline estimate with lower confidence score.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid listing generation with text notes | `POST /api/v1/agent/listing/generate` with bullets: `["3PN D'Capitale", "view hồ", "nội thất nhập"]` | SEO title, structured Markdown description, extracted specs | If Gemini unavailable, return structured fallback |
| Listing generation with title deed image | Base64 image + notes | Multimodal extraction of specs (area, bedrooms, orientation) + description | Fallback gracefully if image cannot be parsed |
| Unauthorized access | Call from user with role `user` | 403 Forbidden | Clear error detail |
| AVM valuation with nearby comps | `POST /api/v1/agent/valuation/estimate` with `lat=21.0169, lng=105.7839, area=90, proposed=6.5B` | `estimated_price_per_sqm`, `estimated_total_price`, `confidence_score > 0.7`, comps list, deviation warning | Return estimated range |
| AVM valuation with no comps in 2km | Location in isolated/new area | Auto-expand search to 8km, return estimate with `confidence_score <= 0.5` | Graceful baseline without 404/500 |
| Cache hit for AVM | Repeated request with same coords, area, property_type | Response retrieved from Redis | N/A |

</frozen-after-approval>

## Code Map

- `backend/src/api/deps.py` -- Add `get_current_agent_user` dependency.
- `backend/src/schemas/agent.py` -- Pydantic DTOs for `GenerateListingRequest`, `GenerateListingResponse`, `ValuationRequest`, `ValuationResponse`.
- `backend/src/services/agent_service.py` -- AI Listing Generator (Gemini + fallback) and AVM Valuation Engine (PostGIS + Weighted KNN).
- `backend/src/api/v1/endpoints/agent.py` -- Endpoints `POST /listing/generate` and `POST /valuation/estimate`.
- `backend/src/api/v1/router.py` -- Mount `/agent` router.
- `backend/tests/api/v1/test_agent.py` -- Pytest test suite for Agent Co-Pilot endpoints.
- `frontend/shared/types.ts` -- TypeScript types for Agent Co-Pilot.
- `frontend/shared/api-client.ts` -- Methods `generateAgentListing` and `estimatePropertyValuation`.
- `frontend/web/src/components/AiListingGeneratorModal.tsx` -- Modal for bullet notes/image upload and auto-fill.
- `frontend/web/src/components/AvmPriceAdvisor.tsx` -- Interactive AVM gauge bar and comps reference component.
- `frontend/web/src/app/properties/create/page.tsx` -- Integrate AI Listing Generator & AVM Price Advisor.
- `frontend/web/src/app/properties/[id]/edit/page.tsx` -- Integrate AI Listing Generator & AVM Price Advisor.
- `frontend/mobile/lib/widgets/ai_listing_dialog.dart` -- Mobile dialog for AI listing generation.
- `frontend/mobile/lib/widgets/avm_price_advisor_widget.dart` -- Mobile AVM pricing hint and gauge bar.
- `README.md` -- Update documentation with Agent AI Co-Pilot API docs.

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/api/deps.py` -- Add `get_current_agent_user` dependency.
- [x] `backend/src/schemas/agent.py` -- Create schemas for Listing Generation & AVM Valuation.
- [x] `backend/src/services/agent_service.py` -- Implement AI Listing Generator (with multimodal image OCR/Vision) and PostGIS AVM valuation engine with Redis caching.
- [x] `backend/src/api/v1/endpoints/agent.py` -- Implement `/listing/generate` and `/valuation/estimate`.
- [x] `backend/src/api/v1/router.py` -- Register `/agent` router.
- [x] `backend/tests/api/v1/test_agent.py` -- Write comprehensive pytest suite for permission check, generation, AVM calculation, and caching.
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add Agent Co-Pilot types and SDK methods.
- [x] `frontend/web/src/components/AiListingGeneratorModal.tsx` -- Build Web AI listing generator dialog.
- [x] `frontend/web/src/components/AvmPriceAdvisor.tsx` -- Build Web AVM pricing advisor gauge and comps card.
- [x] `frontend/web/src/app/properties/create/page.tsx` & `[id]/edit/page.tsx` -- Integrate both widgets into property forms.
- [x] `frontend/mobile/` -- Add mobile AI listing dialog and AVM price advisor widget.
- [x] `README.md` -- Document new Co-Pilot endpoints.

**Acceptance Criteria:**
- Given an agent with bullet points, when `/api/v1/agent/listing/generate` is called, it returns a compelling SEO title, markdown description, and structured specs.
- Given property specs and coordinates, when `/api/v1/agent/valuation/estimate` is called, it returns price per sqm, total price range, confidence score, and comparable properties.
- Non-agent/non-admin users receive 403 Forbidden.
- On Web, agent can click "AI Soạn tin" to auto-fill form, and see real-time AVM valuation gauge as price/area/coords are entered.
- 100% pytest pass and Next.js build clean with 0 errors.

## Implementation Notes
- Gemini Multimodal LLM integration uses `gemini-3.5-flash` with structured heuristic Vietnamese fallback for robustness.
- Smart AVM pricing engine implements Option A dynamic radius expansion (2.5km default, incrementally expanding up to 8.0km if comps < 2) with distance and area decay weighting.
- AVM valuation calculations are cached in Redis with a 900-second (15-minute) TTL.

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest tests/api/v1/test_agent.py` -- PASSED (9/9 passed)
- `cd backend && uv run pytest` -- PASSED (90/90 passed)
- `cd frontend/web && npx tsc --noEmit` -- PASSED (0 errors)
- `cd frontend/web && npm run build` -- PASSED (Compiled successfully, all routes generated)
