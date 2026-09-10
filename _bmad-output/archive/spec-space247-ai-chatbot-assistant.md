---
title: 'Space247 AI Chatbot Assistant for Real Estate Consultation'
type: 'feature'
created: '2026-09-04'
status: 'done'
baseline_commit: 'cc1992712f983dbeaae8f71e2e1f5e7b089a7cf9'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users browsing real estate listings on Space247 need an intuitive, conversational way to discover properties based on natural language preferences without manually filling complex filter forms.

**Approach:** Build an intelligent AI Chatbot Assistant endpoint (`POST /api/v1/chat/assistant`) that extracts search criteria (price, location, property type, amenities) from Vietnamese conversational queries, executes pgvector and FTS Hybrid Search with RRF, and synthesizes friendly Vietnamese advice accompanied by structured property cards; build a responsive floating chat widget in Next.js web frontend with mini property cards and sample prompt suggestions.

## Boundaries & Constraints

**Always:**
- Endpoint must be located at `POST /api/v1/chat/assistant`.
- Intent parsing must extract price ranges (tỷ, triệu), locations (quận, huyện, thành phố), property types (căn hộ, nhà phố, biệt thự, đất nền), listing types (bán, cho thuê), and bedrooms.
- Responses must be written in natural, helpful, polite Vietnamese.
- When property recommendations are found, return property cards with `PropertyResponse` schema.
- Floating chat widget must support minimize/expand, loading typing indicator, quick prompt pills, and mini property cards with links to `/properties/{id}`.
- Dynamic URLs must be verified or sanitized before rendering in images/links.
- All backend tests must pass with 100% success rate.

**Never:**
- Do not make external paid LLM calls that can fail without fallback; use robust pattern extraction and local semantic embeddings with fastembed/pgvector hybrid search and deterministic Vietnamese synthesis.
- Do not crash when conversational queries contain greetings or general questions without property search intent.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Search Query with Criteria | "Tìm căn hộ 2 phòng ngủ giá dưới 3 tỷ ở Quận 1" | Extracted criteria (`apartment`, max 3B, Q1, 2 beds), hybrid search executed, friendly summary, >=1 property cards | Fallback message if 0 matches found with broadening suggestions |
| Rental Inquiry | "Cần thuê nhà phố Bình Thạnh khoảng 15 triệu/tháng" | Extracted criteria (`rent`, `house`, Bình Thạnh, max 15M), rental properties returned | Friendly message explaining criteria searched |
| General Greeting | "Xin chào, bạn có thể giúp gì cho tôi?" | Friendly welcome message introducing Space247 AI features with suggested prompt chips; empty properties list | None (valid conversation) |
| Empty Messages Array | `{ "messages": [] }` | HTTP 422 Unprocessable Entity or 400 Bad Request | Handled via Pydantic validator |
| Malformed Query / No Match | "Tìm biệt thự giá 100 nghìn đồng trên sao Hỏa" | Friendly Vietnamese response saying no matching properties found and advising broader criteria | Returns 200 with friendly message and empty properties array |

</frozen-after-approval>

## Code Map

- `backend/src/schemas/chat.py` -- Pydantic request/response schemas for chat messages, criteria, and assistant response
- `backend/src/services/chat_assistant.py` -- Intent parser, criteria extractor, hybrid search runner, and Vietnamese response generator
- `backend/src/api/v1/endpoints/chat.py` -- FastAPI router exposing `POST /assistant`
- `backend/src/api/v1/router.py` -- Includes `chat.router` under `/chat` prefix
- `backend/tests/test_chat_assistant.py` -- Pytest test suite for chat assistant functionality and edge cases
- `frontend/shared/types.ts` -- TypeScript definitions for chat request/response
- `frontend/shared/api-client.ts` -- `chatAssistant` API client method
- `frontend/web/src/components/ChatAssistantWidget.tsx` -- Floating chat widget with toggle, typing indicator, suggestion chips, and mini property cards
- `frontend/web/src/app/layout.tsx` -- Integrates `ChatAssistantWidget` globally

## Tasks & Acceptance

**Execution:**
- [x] `backend/src/schemas/chat.py` -- Create schemas `ChatMessage`, `ChatAssistantRequest`, `ChatAssistantResponse`, `ExtractedCriteria` -- Provides type safety and API docs
- [x] `backend/src/services/chat_assistant.py` -- Implement criteria extraction and conversational response generation integrating with embedding service and database queries -- Core intelligence
- [x] `backend/src/api/v1/endpoints/chat.py` -- Create endpoint `POST /api/v1/chat/assistant` -- Exposes the assistant API
- [x] `backend/src/api/v1/router.py` -- Register chat router -- Connects router to main API
- [x] `backend/tests/test_chat_assistant.py` -- Author tests covering search, greetings, rental, edge cases -- Verifies 100% test pass
- [x] `frontend/shared/types.ts` & `frontend/shared/api-client.ts` -- Add Chat types and `chatAssistant` method -- Provides shared frontend client support
- [x] `frontend/web/src/components/ChatAssistantWidget.tsx` -- Create floating UI component -- Delivers user interface
- [x] `frontend/web/src/app/layout.tsx` -- Mount `ChatAssistantWidget` -- Makes widget globally accessible


**Acceptance Criteria:**
- Given a user request to `POST /api/v1/chat/assistant` with a search question, when processed, then returns a natural Vietnamese response, extracted criteria, and matched property cards.
- Given the web application, when opened, then displays a floating button in the bottom right; clicking opens the chat dialog with sample questions.
- Given a message asking for properties, when received from the assistant, then renders mini property cards inside the chat bubble with price, thumbnail, and link.
- Given the pytest test suite, when executed with `uv run pytest`, all tests pass with 100% success.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest tests/test_chat_assistant.py` -- expected: All chat assistant tests pass.
- `uv run pytest` -- expected: All backend tests pass.
- `npm run build` (in `frontend/web`) -- expected: Next.js frontend builds without TypeScript or JSX errors.
