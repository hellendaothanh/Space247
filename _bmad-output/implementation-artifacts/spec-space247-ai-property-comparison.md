---
title: 'AI Property Comparison'
type: 'feature'
created: '2026-09-04'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '7be5a223d08235100b7f1205f95ab5b135fb196e'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users cannot easily compare multiple properties side-by-side or understand the nuanced trade-offs between them based on price, location, and potential.

**Approach:** Implement an "AI Property Comparison" feature across backend, web, and mobile that allows selecting 2-3 properties, calculates key metrics (e.g. price/m²), and uses AI to generate a structured comparison across 4 core criteria (cost, location, investment potential, legal/safety), complete with recommendations.

**Decisions:**
- Use Gemini as the LLM provider via the `google-genai` dependency.
- Use the `gemini-3.5-flash` model (configurable).
- API key provided via `GEMINI_API_KEY` environment variable.
- Provide a safe fallback (structured placeholder text) if the LLM call times out or fails.
- The prompt will be in Vietnamese and strictly follow the 4 core criteria.

## Boundaries & Constraints

**Always:**
- Strict validation: Exactly 2 to 3 properties can be compared at once.
- Cache comparison results in Redis with a 30-minute TTL based on a hash of the property IDs.
- Follow existing UI patterns (Riverpod for Mobile, Next.js for Web).

**Never:**
- Do not block the UI while waiting for the AI response (use proper skeleton/shimmer loading).
- Do not exceed the 3-property limit in the UI selection logic.
- Do not crash the endpoint if the LLM fails; return a fallback response.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid selection (2-3 items) | POST `/compare` with 2 IDs | Returns comparison data, calculated price/m², and AI markdown | N/A |
| Invalid selection (< 2) | POST `/compare` with 1 ID | 400 Bad Request | Return explicit error message |
| Invalid selection (> 3) | POST `/compare` with 4 IDs | 400 Bad Request | Return explicit error message |
| Cache hit | POST `/compare` with same IDs | Returns cached response immediately | N/A |
| LLM Failure/Timeout | POST `/compare` with 2 IDs | Returns comparison data and structured fallback markdown | Graceful fallback |

</frozen-after-approval>

## Code Map

- `backend/pyproject.toml` -- Add `google-genai` dependency.
- `backend/src/schemas/property.py` -- Add `ComparePropertiesRequest` and `ComparePropertiesResponse` DTOs.
- `backend/src/api/v1/endpoints/properties.py` -- Add `POST /api/v1/properties/compare` endpoint logic and Redis caching.
- `backend/src/services/ai_comparison.py` -- New service to call Gemini and handle fallback.
- `backend/tests/api/v1/test_properties.py` -- Add tests for the new endpoint (valid, <2, >3, cache).
- `frontend/shared/types.ts` -- Sync new DTOs.
- `frontend/shared/api-client.ts` -- Add `compareProperties(ids)` method.
- `frontend/web/src/components/PropertyCard.tsx` -- Add comparison checkbox/button.
- `frontend/web/src/components/StickyComparisonBar.tsx` -- New component for selected properties bar.
- `frontend/web/src/components/ComparisonModal.tsx` -- New component for the comparison result UI.
- `frontend/mobile/lib/providers/comparison_notifier.dart` -- New Riverpod state for selected properties.
- `frontend/mobile/lib/widgets/property_card.dart` -- Add comparison checkbox/button.
- `frontend/mobile/lib/screens/comparison_screen.dart` -- New screen for comparison results.
- `frontend/mobile/test/comparison_notifier_test.dart` -- Tests for the Riverpod notifier.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml` -- Add `google-genai` dependency -- Required for Gemini API.
- [x] `backend/src/schemas/property.py` -- Add `ComparePropertiesRequest` and `ComparePropertiesResponse` DTOs -- Define request and response shapes.
- [x] `backend/src/services/ai_comparison.py` -- Create `AIComparisonService` -- Encapsulate Gemini API call with prompt for 4 criteria and fallback logic.
- [x] `backend/src/api/v1/endpoints/properties.py` -- Add `POST /compare` endpoint -- Validate input, fetch properties, call AI service, and implement Redis caching.
- [x] `backend/tests/api/v1/test_properties.py` -- Add tests for comparison endpoint -- Verify 400 errors and successful 200 cache hits.
- [x] `frontend/shared/types.ts` -- Export `ComparePropertiesRequest` and `ComparePropertiesResponse` -- Sync types.
- [x] `frontend/shared/api-client.ts` -- Add `compareProperties` method -- Expose API to frontends.
- [x] `frontend/web/src/components/PropertyCard.tsx` -- Add checkbox for comparison -- Allow users to select properties.
- [x] `frontend/web/src/components/StickyComparisonBar.tsx` -- Create sticky bar -- Show selected count and trigger compare action.
- [x] `frontend/web/src/components/ComparisonModal.tsx` -- Create comparison modal -- Display matrix and AI markdown with skeleton loading.
- [x] `frontend/mobile/lib/providers/comparison_notifier.dart` -- Create Riverpod notifier -- Manage up to 3 selected properties.
- [x] `frontend/mobile/lib/widgets/property_card.dart` -- Update card UI -- Add comparison selection toggle.
- [x] `frontend/mobile/lib/screens/comparison_screen.dart` -- Create comparison screen -- Render property matrix and AI analysis with shimmer.
- [x] `frontend/mobile/test/comparison_notifier_test.dart` -- Add tests for state -- Verify max 3 limit and selection toggle.

**Acceptance Criteria:**
- Given a user on Web/Mobile, when they select 2 or 3 properties and click "Compare", then they see a side-by-side matrix and an AI-generated analysis.
- Given a user trying to select a 4th property, when they click the checkbox, then they receive an error/toast indicating the limit is 3.
- Given a valid comparison request, when the same request is made within 30 minutes, then the backend returns the cached response.
- Given a failure in Gemini API, when the user requests a comparison, then a structured fallback response is returned.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest backend/tests/api/v1/test_properties.py` -- expected: PASS
- `cd frontend/mobile && flutter test test/comparison_notifier_test.dart` -- expected: PASS

**Manual checks (if no CLI):**
- Verify Web UI sticky bar appears when 1+ property is selected.
- Verify Mobile UI floating bar appears and comparison screen renders correctly.
