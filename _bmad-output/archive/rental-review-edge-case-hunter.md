Read the following instruction file completely and follow it as your review instructions:
# Edge Case Hunter Review

**Goal:** You are a pure path tracer. Never comment on whether code is good or bad; only list missing handling.
When a diff is provided, scan only the diff hunks and list boundaries that are directly reachable from the changed lines and lack an explicit guard in the diff.
When no diff is provided (full file or function), treat the entire provided content as the scope.
Ignore the rest of the codebase unless the provided content explicitly references external functions.
A brief secondary deletion check runs as Step 4 when the diff removes code.
A claims check runs as Step 5.

**Inputs:**
- **content** — Content to review, or a path to read it from: diff, full file, or function
- **also_consider** (optional) — Areas to keep in mind during review alongside normal edge-case analysis
- **claims_file** — Path to the spec this change was built from. Do NOT read it before Step 5: the path tracing in Steps 2–3 must finish before the claims are seen.

**MANDATORY: Execute steps in the Execution section IN EXACT ORDER. DO NOT skip steps or change the sequence. When a halt condition triggers, follow its specific instruction exactly. Each action within a step is a REQUIRED action to complete that step.**

**Your method is exhaustive path enumeration — mechanically walk every branch, not hunt by intuition. Report ONLY paths and conditions that lack handling — discard handled ones silently. Do NOT editorialize or add filler. Do not assign severity labels, rankings, or priority levels.**


## EXECUTION

### Step 1: Receive Content

- Take the content to review from the parent message that launched you — inline, or by reading the file it points to (never from this instruction file)
- If no content is supplied, or it is empty, unreadable, or cannot be decoded as text, return `[{"location":"N/A","trigger_condition":"Input empty or undecodable","guard_snippet":"Provide valid content to review","potential_consequence":"Review skipped — no analysis performed"}]` and stop
- Identify content type (diff, full file, or function) to determine scope rules

### Step 2: Exhaustive Path Analysis

**Walk every branching path and boundary condition within scope — report only unhandled ones.**

- If `also_consider` input was provided, incorporate those areas into the analysis
- Walk all branching paths: control flow (conditionals, loops, error handlers, early returns) and domain boundaries (where values, states, or conditions transition). Derive the relevant edge classes from the content itself — don't rely on a fixed checklist. Examples: missing else/default, unguarded inputs, off-by-one loops, arithmetic overflow, implicit type coercion, race conditions, timeout gaps
- Consider implicit branches: the diff special-cases or changes the handling of one or more members of a fixed set of values — enums, status codes, sentinels, type tags, flags, value ranges. The rest of the set is implicit branches (e.g. the diff changes the `RED` and `YELLOW` cases of a `RED`/`YELLOW`/`GREEN` enum; `GREEN` is the implicit branch)
- Consider handle lifetime: when the changed code re-checks, re-fetches, or re-validates something it already held — a handle, index, id, pointer — the re-check exists because an intervening call can invalidate it. Identify that call, what it does to the thing held, and what the changed code silently skips when the re-check fails
- For each call site the diff adds or changes — in test files as well as production code — read the callee's declaration and check the call against it: argument count, order, types, and defaults. Report any mismatch
- For each path: determine whether the content handles it
- Collect only the unhandled paths as findings — discard handled ones silently

### Step 3: Validate Completeness

- Revisit every edge class from Step 2 — e.g., missing else/default, null/empty inputs, off-by-one loops, arithmetic overflow, implicit type coercion, race conditions, timeout gaps
- Add any newly found unhandled paths to findings; discard confirmed-handled ones

### Step 4: Deletion Check

If the diff removed or replaced meaningful code (ignore pure renames and whitespace): load `references/deletion-check.md` and follow it.

### Step 5: Claims Check

Load `references/claims-check.md` and follow it.

### Step 6: Present Findings

Output all findings as a single JSON array following the Output Format specification exactly.


## OUTPUT FORMAT

Return ONLY a valid JSON array of objects. Each edge-case finding contains exactly these four fields:

```json
[{
  "location": "file:start-end (or file:line when single line, or file:hunk when exact line unavailable)",
  "trigger_condition": "one-line description (max 15 words)",
  "guard_snippet": "minimal code sketch that closes the gap (single-line escaped string, no raw newlines or unescaped quotes)",
  "potential_consequence": "what could actually go wrong (max 15 words)"
}]
```

No extra text, no explanations, no markdown wrapping. An empty array `[]` is valid when nothing is found. Deletion findings from Step 4 and claim findings from Step 5, if any, go in the same array with the extra fields defined in `references/deletion-check.md` and `references/claims-check.md`.


## HALT CONDITIONS

- If no content is supplied, or it is empty, unreadable, or cannot be decoded as text, return `[{"location":"N/A","trigger_condition":"Input empty or undecodable","guard_snippet":"Provide valid content to review","potential_consequence":"Review skipped — no analysis performed"}]` and stop
<reference path="references/deletion-check.md">
# Deletion Check

Secondary pass for the Edge Case Hunter — runs only when the diff removed meaningful code. Subordinate to the edge-case pass; findings are usually few or none.

For each chunk of removed or replaced code (ignore pure renames and whitespace), ask: did it carry behavior or a contract that the change neither re-established nor intentionally retired? Add a finding for any resulting regression, orphaned reference, or newly-dead code. Skip anything already covered by your edge-case findings.

Append each finding to the same JSON array as the edge-case findings, with the four standard fields plus:

- `kind`: `"deletion"`
- `confidence`: `"high"`, `"medium"`, or `"low"` — these are inferences; rate them

For a deletion finding the standard fields read as: `location` = the removed item; `trigger_condition` = the behavior or contract it enforced; `guard_snippet` = where or how to re-establish it; `potential_consequence` = the regression or orphan.

Add nothing if nothing qualifies.
</reference>
<reference path="references/claims-check.md">
# Claims Check

Final pass for the Edge Case Hunter. Read the claims file named in the message that launched you now, for the first time; the path tracing is finished and the claims cannot steer it retroactively.

It is the spec the change was built from. Read only its `## Intent` and `## Tasks & Acceptance` sections — the claims live there; ignore the rest of the file. The spec is the change's own account of itself: testimony, not evidence — a claim repeated in a code comment is still the same claim, not confirmation. Extract each checkable claim — what the change does, what it preserves, ordering, arithmetic, and parity with existing code ("exactly as X does") — then try to falsify each one against the code you have already traced. Where your trace is not enough to decide, read the code that decides it: the compared-to function, the actual callee, the state the claim assumes.

Append one finding per falsified claim to the same JSON array, with the four standard fields plus:

- `kind`: `"claim"`
- `confidence`: `"high"`, `"medium"`, or `"low"`

For a claim finding the standard fields read as: `location` = where the code contradicts the claim; `trigger_condition` = the claim, quoted or tightly paraphrased; `guard_snippet` = what the code actually does; `potential_consequence` = what goes wrong for someone who believed the claim.

Verified claims produce nothing. Add nothing if nothing is falsified.
</reference>

## CONTENT SOURCE

"Review content:" in the message that launched you gives the content itself or a path to read it from. Read the file when it is a path; either way that is the content under review, and this instruction file never is.

claims_file (leave unread until your instructions call for it):
---
title: 'Rental and Serviced Apartments'
type: 'feature'
created: '2026-09-07'
status: 'in-review'
baseline_commit: '8c9152b6437a9baf813c58e1853197412665cd40'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Generic rent listings exist but lack structured room categories, transparent expenses, rules, and matching rental discovery across web, mobile, and AI.

**Approach:** Extend the existing property contract with rental metadata, exact filters, rental-aware embeddings/chat, a web rental catalog, posting controls, and mobile rental discovery/details.

## Boundaries & Constraints

**Always:** Preserve existing listings, authorization, caching, pagination, and 768-dimensional vectors. Use sale/rent and room/serviced_apartment/house_share/entire_house. Store requested costs and rules in nullable JSONB. Missing values mean unknown; zero and false remain meaningful. Prices are monthly VND for rentals. Interpret max_deposit in months. Deposit amount equals monthly rent times deposit_months; variable electricity/water expenses cannot be totaled without consumption/person counts. Keep rental metadata optional for legacy listings. Reuse existing sale/rent types.

**Never:** Recreate the existing listing_type column, invent amenities, equate unknown charges with free service, deploy, or migrate a live database during implementation.

**Approved decisions:** Add optional electricity_billing (state_rate | fixed) to rental_costs for exact state-tariff filtering. Geocode landmarks, resolving Bách Khoa to Hanoi University of Science and Technology, and filter with PostGIS within a default 3.0 km radius; fall back to semantic location search when coordinates cannot be resolved. Add optional has_washing_machine, live_with_owner, has_elevator, fingerprint_lock booleans to rental_rules. Migration 0008 alters the existing listing_type default without duplicating the column. The user approved this complete cross-layer scope on 2026-09-07.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Rental record | Valid subtype, costs, rules | Create/read/update round-trip metadata | Invalid enums, negative costs/deposits, invalid time or occupancy return 422 |
| Exact filters | Rent, subtype, pets, mezzanine, deposit ceiling | Only matching active rentals; predicates apply before ranking/limit | Preserve false/zero; missing JSON keys do not satisfy explicit predicates |
| Legacy record | No rental metadata | Listing remains readable; unknown charges labeled unavailable | No fabricated badges |
| Update | Rental expenses/rules change | Embedding refresh and cache invalidation | Preserve omitted fields; explicit null clears optional metadata |
| Sale transition | Rental changed to sale | Clear rental-only metadata; hide rental UI | Do not mutate unrelated fields |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0001_initial_pgvector_properties.py`: listing_type already exists; 0007 is current head.
- `backend/src/models/property.py`, `backend/src/schemas/property.py`: persistence and inherited create/response/detail DTOs; update and search schemas separate.
- `backend/src/api/v1/endpoints/properties.py`, `search.py`: list, CRUD, hybrid and vector filters; keep existing auth/cache behavior.
- `backend/src/services/embedding.py`, `chat_assistant.py`, `backend/src/schemas/chat.py`: text composer, regex intent parser, separate hybrid filter closure.
- `frontend/shared/types.ts`, `api-client.ts`: inherited property DTOs; list and search filter serialization.
- `frontend/web/src/components/Navbar.tsx`, `SearchSection.tsx`, `PropertyCard.tsx`: current sale/rent links, filters, cards. Price utility already supports /tháng.
- `frontend/web/src/app/properties/[id]/page.tsx`: details already hide mortgage calculator for rent. Create/edit property pages contain sale/rent tabs; create also hydrates cloned listings.
- `frontend/mobile/lib/models/property.dart`, `providers/app_providers.dart`, `services/property_service.dart`: serialization, filter state, POST hybrid search.
- `frontend/mobile/lib/widgets/search_and_filter.dart`, `property_card.dart`, `screens/property_detail_screen.dart`: existing rental chip, cards, details; no mobile posting form exists.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0008_rental_serviced_apartments.py`, model: alter listing_type default to sale, add rental_type VARCHAR(50), costs/rules JSONB, composite B-tree (listing_type,rental_type,price); reversible downgrade.
- [x] Property/chat schemas and `backend/src/services/rental.py`: typed validation, shared exact predicates and deposit calculations; follow resolved questions.
- [x] Property/search endpoints: persist fields, GET price/rental filters, apply consistent predicates to vector/FTS/fallback, update embeddings and invalidate caches.
- [x] Embedding/chat services: rental cost/rule text, Vietnamese room/loft/pet/budget intent and resolved electricity/location semantics.
- [x] Shared types/client: RentalCosts, RentalRules, RentalType; preserve ListingType; extend CRUD and list/search parameters.
- [x] `frontend/web/src/app/rentals/page.tsx` and listed web components: sale/rent navigation, monthly price/type/amenity filters, rental badges and transparent expense/rule cards.
- [x] Web property create/edit pages: conditional rental inputs, validation, clone hydration and payload handling.
- [x] Listed mobile files: rental discovery tab/filters, metadata serialization, /tháng prices, loft/pet badges and expense details.
- [x] `backend/tests/test_rentals.py`, migration/search/chat tests: matrix, arithmetic, SQL filters, intent, embedding refresh and regression coverage. Extend `frontend/mobile/test/widget_test.dart` for rental model/UI behavior.
- [x] `docs/database-design.md`, `docs/api-specs.md`, `README.md`: schema, units, filters, examples, migration instructions and rental capabilities.

**Acceptance Criteria:**
- Given migration head 0007, when 0008 upgrades, then existing sale/rent values survive and the requested fields/default/index exist; downgrade retains listing_type.
- Given mixed listings, when rental criteria are used through web/mobile/chat, then sale listings and nonmatching rentals are excluded.
- Given a rental, when viewing, creating, editing or cloning on web, then costs/rules persist and display with correct units; mobile discovery/details reflect the same data.
- Given the completed change, when backend tests, TypeScript and production build execute, then every test passes and both web commands exit without errors.

## Implementation Notes

- Implemented all layers; parent audit corrected original requested field names and integer costs, added curfew/private_bathroom, around-landmark parsing, and separate icon-based fee/rule cards. No live migration applied.
- Verification: 146 backend tests passed, followed by all 18 rental tests including the added exact-contract/original-query regression; TypeScript and production build passed; 13 Flutter tests passed. Matrix rows covered by rental validation, predicate, legacy, CRUD/update/sale-transition tests and mobile unknown-fee/badge checks.

## Spec Change Log

## Review Triage Log

## Verification

- Backend: `uv run pytest` (all pass); `uv run alembic upgrade head --sql` and migration downgrade SQL tests.
- Web: `npx tsc --noEmit` and `npm run build` (zero errors).
- Mobile: `flutter analyze` and `flutter test`; inspect rental filters, badges and fee units.
- Report environmental blockers explicitly; mocked SQL tests do not establish live PostgreSQL execution.

Review content: the unified diff below. It is the content under review.
diff --git a/README.md b/README.md
index dbe7b9f..d46a90a 100644
--- a/README.md
+++ b/README.md
@@ -319,3 +319,19 @@ Space247/
 ## 9. Giấy Phép (License)
 
 Dự án Space247 được phát triển dưới bản quyền nội bộ phục vụ hệ thống công nghệ bất động sản Space247 Platform.
+
+
+### Rental discovery
+
+The web `/rentals` catalog supports rooms, serviced apartments, house shares and
+entire houses, monthly VND budgets, exact amenity/rule filters, deposit ceilings in
+months, and landmark searches (default 3 km; Bách Khoa resolves to HUST in Hanoi).
+Web create/edit/clone forms and mobile rental discovery/details preserve optional
+expenses and rules, including known zero charges and false values. Unknown
+charges are labeled unavailable; electricity/water totals require actual usage.
+Chat understands Vietnamese room, loft, pet, budget and state electricity tariff
+criteria. Switching a listing to sale clears its rental-only metadata.
+
+See [API contract](docs/api-specs.md#rental-and-serviced-apartment-metadata) and
+[database design](docs/database-design.md#rental-and-serviced-apartment-metadata)
+for field units, request examples, and migration 0008 review instructions.
diff --git a/_bmad-output/implementation-artifacts/spec-space247-rental-serviced-apartments.md b/_bmad-output/implementation-artifacts/spec-space247-rental-serviced-apartments.md
new file mode 100644
index 0000000..d3dc05a
--- /dev/null
+++ b/_bmad-output/implementation-artifacts/spec-space247-rental-serviced-apartments.md
@@ -0,0 +1,86 @@
+---
+title: 'Rental and Serviced Apartments'
+type: 'feature'
+created: '2026-09-07'
+status: 'in-review'
+baseline_commit: '8c9152b6437a9baf813c58e1853197412665cd40'
+route: 'dispatch'
+review_loop_iteration: 0
+context: []
+---
+
+<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">
+
+## Intent
+
+**Problem:** Generic rent listings exist but lack structured room categories, transparent expenses, rules, and matching rental discovery across web, mobile, and AI.
+
+**Approach:** Extend the existing property contract with rental metadata, exact filters, rental-aware embeddings/chat, a web rental catalog, posting controls, and mobile rental discovery/details.
+
+## Boundaries & Constraints
+
+**Always:** Preserve existing listings, authorization, caching, pagination, and 768-dimensional vectors. Use sale/rent and room/serviced_apartment/house_share/entire_house. Store requested costs and rules in nullable JSONB. Missing values mean unknown; zero and false remain meaningful. Prices are monthly VND for rentals. Interpret max_deposit in months. Deposit amount equals monthly rent times deposit_months; variable electricity/water expenses cannot be totaled without consumption/person counts. Keep rental metadata optional for legacy listings. Reuse existing sale/rent types.
+
+**Never:** Recreate the existing listing_type column, invent amenities, equate unknown charges with free service, deploy, or migrate a live database during implementation.
+
+**Approved decisions:** Add optional electricity_billing (state_rate | fixed) to rental_costs for exact state-tariff filtering. Geocode landmarks, resolving Bách Khoa to Hanoi University of Science and Technology, and filter with PostGIS within a default 3.0 km radius; fall back to semantic location search when coordinates cannot be resolved. Add optional has_washing_machine, live_with_owner, has_elevator, fingerprint_lock booleans to rental_rules. Migration 0008 alters the existing listing_type default without duplicating the column. The user approved this complete cross-layer scope on 2026-09-07.
+
+## I/O & Edge-Case Matrix
+
+| Scenario | Input / State | Expected Output / Behavior | Error Handling |
+|---|---|---|---|
+| Rental record | Valid subtype, costs, rules | Create/read/update round-trip metadata | Invalid enums, negative costs/deposits, invalid time or occupancy return 422 |
+| Exact filters | Rent, subtype, pets, mezzanine, deposit ceiling | Only matching active rentals; predicates apply before ranking/limit | Preserve false/zero; missing JSON keys do not satisfy explicit predicates |
+| Legacy record | No rental metadata | Listing remains readable; unknown charges labeled unavailable | No fabricated badges |
+| Update | Rental expenses/rules change | Embedding refresh and cache invalidation | Preserve omitted fields; explicit null clears optional metadata |
+| Sale transition | Rental changed to sale | Clear rental-only metadata; hide rental UI | Do not mutate unrelated fields |
+
+</frozen-after-approval>
+
+## Code Map
+
+- `backend/migrations/versions/0001_initial_pgvector_properties.py`: listing_type already exists; 0007 is current head.
+- `backend/src/models/property.py`, `backend/src/schemas/property.py`: persistence and inherited create/response/detail DTOs; update and search schemas separate.
+- `backend/src/api/v1/endpoints/properties.py`, `search.py`: list, CRUD, hybrid and vector filters; keep existing auth/cache behavior.
+- `backend/src/services/embedding.py`, `chat_assistant.py`, `backend/src/schemas/chat.py`: text composer, regex intent parser, separate hybrid filter closure.
+- `frontend/shared/types.ts`, `api-client.ts`: inherited property DTOs; list and search filter serialization.
+- `frontend/web/src/components/Navbar.tsx`, `SearchSection.tsx`, `PropertyCard.tsx`: current sale/rent links, filters, cards. Price utility already supports /tháng.
+- `frontend/web/src/app/properties/[id]/page.tsx`: details already hide mortgage calculator for rent. Create/edit property pages contain sale/rent tabs; create also hydrates cloned listings.
+- `frontend/mobile/lib/models/property.dart`, `providers/app_providers.dart`, `services/property_service.dart`: serialization, filter state, POST hybrid search.
+- `frontend/mobile/lib/widgets/search_and_filter.dart`, `property_card.dart`, `screens/property_detail_screen.dart`: existing rental chip, cards, details; no mobile posting form exists.
+
+## Tasks & Acceptance
+
+**Execution:**
+- [x] `backend/migrations/versions/0008_rental_serviced_apartments.py`, model: alter listing_type default to sale, add rental_type VARCHAR(50), costs/rules JSONB, composite B-tree (listing_type,rental_type,price); reversible downgrade.
+- [x] Property/chat schemas and `backend/src/services/rental.py`: typed validation, shared exact predicates and deposit calculations; follow resolved questions.
+- [x] Property/search endpoints: persist fields, GET price/rental filters, apply consistent predicates to vector/FTS/fallback, update embeddings and invalidate caches.
+- [x] Embedding/chat services: rental cost/rule text, Vietnamese room/loft/pet/budget intent and resolved electricity/location semantics.
+- [x] Shared types/client: RentalCosts, RentalRules, RentalType; preserve ListingType; extend CRUD and list/search parameters.
+- [x] `frontend/web/src/app/rentals/page.tsx` and listed web components: sale/rent navigation, monthly price/type/amenity filters, rental badges and transparent expense/rule cards.
+- [x] Web property create/edit pages: conditional rental inputs, validation, clone hydration and payload handling.
+- [x] Listed mobile files: rental discovery tab/filters, metadata serialization, /tháng prices, loft/pet badges and expense details.
+- [x] `backend/tests/test_rentals.py`, migration/search/chat tests: matrix, arithmetic, SQL filters, intent, embedding refresh and regression coverage. Extend `frontend/mobile/test/widget_test.dart` for rental model/UI behavior.
+- [x] `docs/database-design.md`, `docs/api-specs.md`, `README.md`: schema, units, filters, examples, migration instructions and rental capabilities.
+
+**Acceptance Criteria:**
+- Given migration head 0007, when 0008 upgrades, then existing sale/rent values survive and the requested fields/default/index exist; downgrade retains listing_type.
+- Given mixed listings, when rental criteria are used through web/mobile/chat, then sale listings and nonmatching rentals are excluded.
+- Given a rental, when viewing, creating, editing or cloning on web, then costs/rules persist and display with correct units; mobile discovery/details reflect the same data.
+- Given the completed change, when backend tests, TypeScript and production build execute, then every test passes and both web commands exit without errors.
+
+## Implementation Notes
+
+- Implemented all layers; parent audit corrected original requested field names and integer costs, added curfew/private_bathroom, around-landmark parsing, and separate icon-based fee/rule cards. No live migration applied.
+- Verification: 146 backend tests passed, followed by all 18 rental tests including the added exact-contract/original-query regression; TypeScript and production build passed; 13 Flutter tests passed. Matrix rows covered by rental validation, predicate, legacy, CRUD/update/sale-transition tests and mobile unknown-fee/badge checks.
+
+## Spec Change Log
+
+## Review Triage Log
+
+## Verification
+
+- Backend: `uv run pytest` (all pass); `uv run alembic upgrade head --sql` and migration downgrade SQL tests.
+- Web: `npx tsc --noEmit` and `npm run build` (zero errors).
+- Mobile: `flutter analyze` and `flutter test`; inspect rental filters, badges and fee units.
+- Report environmental blockers explicitly; mocked SQL tests do not establish live PostgreSQL execution.
diff --git a/backend/migrations/versions/0008_rental_serviced_apartments.py b/backend/migrations/versions/0008_rental_serviced_apartments.py
new file mode 100644
index 0000000..3dfc478
--- /dev/null
+++ b/backend/migrations/versions/0008_rental_serviced_apartments.py
@@ -0,0 +1,23 @@
+"""Optional rental metadata, preserving existing sale/rent listings."""
+from alembic import op
+import sqlalchemy as sa
+from sqlalchemy.dialects import postgresql
+revision = "0008"
+down_revision = "0007"
+branch_labels = None
+depends_on = None
+
+
+def upgrade():
+    op.alter_column("properties", "listing_type", server_default="sale")
+    op.add_column("properties", sa.Column("rental_type", sa.String(50), nullable=True))
+    op.add_column("properties", sa.Column("rental_costs", postgresql.JSONB(), nullable=True))
+    op.add_column("properties", sa.Column("rental_rules", postgresql.JSONB(), nullable=True))
+    op.create_index("ix_properties_rental_price", "properties", ["listing_type", "rental_type", "price"])
+
+
+def downgrade():
+    op.drop_index("ix_properties_rental_price", table_name="properties")
+    for name in ("rental_rules", "rental_costs", "rental_type"):
+        op.drop_column("properties", name)
+    op.alter_column("properties", "listing_type", server_default=None)
diff --git a/backend/src/api/v1/endpoints/properties.py b/backend/src/api/v1/endpoints/properties.py
index 35c7ce0..cfa4a74 100644
--- a/backend/src/api/v1/endpoints/properties.py
+++ b/backend/src/api/v1/endpoints/properties.py
@@ -24,6 +24,7 @@ from src.models.property import Property
 from src.models.user import User
 from src.schemas.property import (
     ListingType,
+    RentalFilters,
     PropertyAgentResponse,
     PropertyCreate,
     PropertyDetailResponse,
@@ -40,6 +41,7 @@ from src.schemas.property import (
     ComparisonData,
 )
 from src.services.embedding import EmbeddingService, get_embedding_service
+from src.services.rental import apply_rental_filters, resolve_landmark, rental_text
 from src.services.ai_comparison import AIComparisonService
 
 logger = logging.getLogger("space247_backend.properties")
@@ -78,6 +80,8 @@ async def create_property(
     Triggers asynchronous background task to match against saved search alerts.
     """
     prop_data = property_in.model_dump()
+    if property_in.listing_type == ListingType.SALE:
+        prop_data.update(rental_type=None, rental_costs=None, rental_rules=None)
 
     if property_in.embedding is not None:
         if len(property_in.embedding) != settings.VECTOR_DIM:
@@ -101,6 +105,8 @@ async def create_property(
             listing_type=property_in.listing_type.value if hasattr(property_in.listing_type, "value") else str(property_in.listing_type),
             num_bedrooms=property_in.num_bedrooms,
         )
+        if property_in.listing_type == ListingType.RENT:
+            text_content += ". " + rental_text(prop_data["rental_type"], prop_data["rental_costs"], prop_data["rental_rules"])
         try:
             prop_data["embedding"] = embedding_service.generate_embedding(text_content, is_query=False)
         except TypeError:
@@ -150,6 +156,16 @@ async def search_properties(
     When enable_hybrid=True, executes both vector search and Full-Text Search (FTS), fusing
     rankings using Reciprocal Rank Fusion (RRF) with smoothing constant k (default 60).
     """
+    # Apply rental intent consistently to web/mobile natural-language discovery.
+    from src.services.chat_assistant import ChatAssistantService
+    from src.schemas.chat import ChatMessage
+    _, inferred = ChatAssistantService(embedding_service).parse_intent_and_criteria([ChatMessage(role="user", content=search_in.query[:4000])])
+    if inferred.listing_type == ListingType.RENT:
+        fields = (*RentalFilters.model_fields, "listing_type", "min_price", "max_price")
+        changes = {key: getattr(inferred, key) for key in fields if key not in search_in.model_fields_set and getattr(inferred, key, None) is not None}
+        search_in = PropertySearchQuery.model_validate({**search_in.model_dump(), **changes})
+    if search_in.near_landmark and search_in.near_landmark not in search_in.query:
+        search_in = search_in.model_copy(update={"query": search_in.query + " " + search_in.near_landmark})
     # Check Redis cache for identical search parameters
     cache_key = generate_search_cache_key(search_in.model_dump())
     cached_data = await get_cached_json(cache_key)
@@ -174,6 +190,8 @@ async def search_properties(
             ),
         )
 
+    coordinates = await resolve_landmark(search_in)
+
     # Common filter builder for structured metadata
     def apply_filters(base_stmt):
         stmt = base_stmt
@@ -199,7 +217,7 @@ async def search_properties(
             stmt = stmt.where(Property.area_sqm >= search_in.min_area_sqm)
         if search_in.max_area_sqm is not None:
             stmt = stmt.where(Property.area_sqm <= search_in.max_area_sqm)
-        return stmt
+        return apply_rental_filters(stmt, search_in, coordinates)
 
     # 1. Vector Search Query
     cosine_dist = Property.embedding.cosine_distance(query_vector)
@@ -352,6 +370,9 @@ async def list_properties(
     listing_type: ListingType | None = Query(None, description="Filter by listing type"),
     property_type: PropertyType | None = Query(None, description="Filter by property type"),
     city: str | None = Query(None, description="Filter by city"),
+    min_price: float | None = Query(None, ge=0),
+    max_price: float | None = Query(None, ge=0),
+    rental: RentalFilters = Depends(),
     status: PropertyStatus | None = Query(None, description="Filter by listing status"),
     db: AsyncSession = Depends(get_db_session),
 ) -> list[Property]:
@@ -370,6 +391,11 @@ async def list_properties(
     else:
         stmt = stmt.where(Property.status == PropertyStatus.ACTIVE.value)
 
+    if min_price is not None:
+        stmt = stmt.where(Property.price >= min_price)
+    if max_price is not None:
+        stmt = stmt.where(Property.price <= max_price)
+    stmt = apply_rental_filters(stmt, rental, await resolve_landmark(rental))
     stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
     result = await db.execute(stmt)
     return list(result.scalars().all())
@@ -575,6 +601,9 @@ async def update_property(
             )
 
     update_data = property_update.model_dump(exclude_unset=True)
+    for key in ("rental_costs", "rental_rules"):
+        if isinstance(update_data.get(key), dict):
+            update_data[key] = {**(getattr(property_obj, key, None) or {}), **update_data[key]}
     if "listing_type" in update_data and isinstance(update_data["listing_type"], ListingType):
         update_data["listing_type"] = update_data["listing_type"].value
     if "property_type" in update_data and isinstance(update_data["property_type"], PropertyType):
@@ -582,7 +611,11 @@ async def update_property(
     if "status" in update_data and isinstance(update_data["status"], PropertyStatus):
         update_data["status"] = update_data["status"].value
 
+    if update_data.get("listing_type", property_obj.listing_type) == "sale" and ("listing_type" in update_data or any(k in update_data for k in ("rental_type", "rental_costs", "rental_rules"))):
+        update_data.update(rental_type=None, rental_costs=None, rental_rules=None)
+
     text_fields = {
+        "rental_type", "rental_costs", "rental_rules",
         "title",
         "description",
         "address",
@@ -619,6 +652,8 @@ async def update_property(
                 listing_type=new_listing_type,
                 num_bedrooms=new_num_bedrooms,
             )
+            if new_listing_type == "rent":
+                combined_text += ". " + rental_text(*(update_data.get(key, getattr(property_obj, key, None)) for key in ("rental_type", "rental_costs", "rental_rules")))
             try:
                 update_data["embedding"] = embedding_service.generate_embedding(combined_text, is_query=False)
             except TypeError:
diff --git a/backend/src/api/v1/endpoints/search.py b/backend/src/api/v1/endpoints/search.py
index 62c2e5c..4fae58a 100644
--- a/backend/src/api/v1/endpoints/search.py
+++ b/backend/src/api/v1/endpoints/search.py
@@ -18,6 +18,8 @@ from src.schemas.property import (
     SemanticSearchResponse,
 )
 
+from src.services.rental import apply_rental_filters, resolve_landmark
+
 router = APIRouter()
 
 
@@ -89,6 +91,8 @@ async def semantic_search(
     if query.max_area_sqm is not None:
         stmt = stmt.where(Property.area_sqm <= query.max_area_sqm)
 
+    stmt = apply_rental_filters(stmt, query, await resolve_landmark(query))
+
     # Order by cosine distance ascending (closest match first)
     stmt = stmt.order_by(cosine_dist.asc()).limit(query.limit)
 
diff --git a/backend/src/models/property.py b/backend/src/models/property.py
index 5e1ec2c..6998146 100644
--- a/backend/src/models/property.py
+++ b/backend/src/models/property.py
@@ -16,7 +16,7 @@ from sqlalchemy import (
     inspect,
     text,
 )
-from sqlalchemy.dialects.postgresql import ARRAY, UUID
+from sqlalchemy.dialects.postgresql import ARRAY, UUID, JSONB
 from sqlalchemy.orm import Mapped, mapped_column, relationship
 
 from src.core.config import settings
@@ -26,6 +26,7 @@ from src.core.database import Base
 class Property(Base):
     __tablename__ = "properties"
     __table_args__ = (
+        Index("ix_properties_rental_price", "listing_type", "rental_type", "price"),
         Index(
             "ix_properties_embedding_hnsw",
             "embedding",
@@ -51,7 +52,10 @@ class Property(Base):
     title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
     description: Mapped[str] = mapped_column(Text, nullable=False)
     property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
-    listing_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # sale / rent
+    listing_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="sale", server_default="sale")  # sale / rent
+    rental_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
+    rental_costs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
+    rental_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
     price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, index=True)
     currency: Mapped[str] = mapped_column(String(10), nullable=False, default="VND")
     area_sqm: Mapped[float] = mapped_column(Float, nullable=False, index=True)
diff --git a/backend/src/schemas/chat.py b/backend/src/schemas/chat.py
index 9a9f657..ead6876 100644
--- a/backend/src/schemas/chat.py
+++ b/backend/src/schemas/chat.py
@@ -24,7 +24,10 @@ class ChatMessage(BaseModel):
         return v_lower
 
 
-class ExtractedCriteria(BaseModel):
+from src.schemas.rental import RentalFilters
+
+
+class ExtractedCriteria(RentalFilters):
     listing_type: ListingType | None = Field(default=None, description="Sale or rent")
     property_type: PropertyType | None = Field(default=None, description="Apartment, house, villa, etc.")
     city: str | None = Field(default=None, description="Extracted city")
diff --git a/backend/src/schemas/property.py b/backend/src/schemas/property.py
index 6b5e353..774f8f5 100644
--- a/backend/src/schemas/property.py
+++ b/backend/src/schemas/property.py
@@ -3,6 +3,7 @@ from enum import Enum
 import uuid
 from pydantic import BaseModel, ConfigDict, Field, model_validator
 from src.schemas.project import ProjectSummary
+from src.schemas.rental import RentalCosts, RentalRules, RentalType, RentalFilters
 
 
 class ListingType(str, Enum):
@@ -27,6 +28,10 @@ class PropertyStatus(str, Enum):
 
 
 class PropertyBase(BaseModel):
+    rental_type: RentalType | None = None
+    rental_costs: RentalCosts | None = None
+    rental_rules: RentalRules | None = None
+
     title: str = Field(..., min_length=3, max_length=255, description="Listing title")
     description: str = Field(..., min_length=10, description="Detailed property description")
     property_type: PropertyType = Field(..., description="Type of property")
@@ -54,6 +59,10 @@ class PropertyCreate(PropertyBase):
 
 
 class PropertyUpdate(BaseModel):
+    rental_type: RentalType | None = None
+    rental_costs: RentalCosts | None = None
+    rental_rules: RentalRules | None = None
+
     title: str | None = Field(default=None, min_length=3, max_length=255)
     description: str | None = Field(default=None, min_length=10)
     property_type: PropertyType | None = None
@@ -105,7 +114,7 @@ class PropertyDetailResponse(PropertyResponse):
     model_config = ConfigDict(from_attributes=True)
 
 
-class SemanticSearchQuery(BaseModel):
+class SemanticSearchQuery(RentalFilters):
     query_vector: list[float] = Field(..., description="768-dimensional embedding vector")
     listing_type: ListingType | None = Field(default=None, description="Filter by listing type (sale/rent)")
     property_type: PropertyType | None = Field(default=None, description="Filter by property type")
@@ -150,7 +159,7 @@ class SemanticSearchResponse(BaseModel):
     results: list[SearchResultItem]
 
 
-class PropertySearchQuery(BaseModel):
+class PropertySearchQuery(RentalFilters):
     query: str = Field(
         ...,
         min_length=1,
diff --git a/backend/src/schemas/rental.py b/backend/src/schemas/rental.py
new file mode 100644
index 0000000..3d9bf35
--- /dev/null
+++ b/backend/src/schemas/rental.py
@@ -0,0 +1,55 @@
+from enum import Enum
+from typing import Literal
+from pydantic import BaseModel, ConfigDict, Field
+
+
+class RentalType(str, Enum):
+    ROOM = "room"
+    SERVICED_APARTMENT = "serviced_apartment"
+    HOUSE_SHARE = "house_share"
+    ENTIRE_HOUSE = "entire_house"
+
+
+class RentalCostSchema(BaseModel):
+    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
+    electricity_per_kwh: int | None = Field(None, ge=0, strict=True)
+    electricity_billing: Literal["state_rate", "fixed"] | None = None
+    water_cost: int | None = Field(None, ge=0, strict=True)
+    water_unit: Literal["per_m3", "per_person"] | None = None
+    parking_fee_monthly: int | None = Field(None, ge=0, strict=True)
+    service_fee_monthly: int | None = Field(None, ge=0, strict=True)
+    deposit_months: int | None = Field(None, ge=0, strict=True)
+
+
+class RentalRuleSchema(BaseModel):
+    model_config = ConfigDict(extra="forbid")
+    allow_pets: bool | None = None
+    curfew: bool | None = None
+    private_bathroom: bool | None = None
+    has_mezzanine: bool | None = None
+    has_washing_machine: bool | None = None
+    live_with_owner: bool | None = None
+    has_elevator: bool | None = None
+    fingerprint_lock: bool | None = None
+    curfew_time: str | None = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
+    max_occupants: int | None = Field(None, ge=1, strict=True)
+
+
+class RentalFilters(BaseModel):
+    rental_type: RentalType | None = None
+    allow_pets: bool | None = None
+    curfew: bool | None = None
+    private_bathroom: bool | None = None
+    has_mezzanine: bool | None = None
+    has_washing_machine: bool | None = None
+    live_with_owner: bool | None = None
+    has_elevator: bool | None = None
+    fingerprint_lock: bool | None = None
+    electricity_billing: Literal["state_rate", "fixed"] | None = None
+    max_deposit: float | None = Field(None, ge=0, allow_inf_nan=False)
+    near_landmark: str | None = None
+    radius_km: float = Field(3.0, gt=0, le=100)
+
+
+RentalCosts = RentalCostSchema
+RentalRules = RentalRuleSchema
diff --git a/backend/src/services/chat_assistant.py b/backend/src/services/chat_assistant.py
index 0c3c355..a7972d8 100644
--- a/backend/src/services/chat_assistant.py
+++ b/backend/src/services/chat_assistant.py
@@ -18,6 +18,8 @@ from src.schemas.property import (
 )
 from src.services.embedding import EmbeddingService, get_embedding_service
 
+from src.services.rental import apply_rental_filters, resolve_landmark
+
 logger = logging.getLogger(__name__)
 
 
@@ -59,7 +61,7 @@ class ChatAssistantService:
 
         # Common real estate intent keywords
         re_keywords = [
-            "tìm", "mua", "bán", "thuê", "căn hộ", "chung cư", "nhà", "biệt thự",
+            "phòng trọ", "ở ghép", "gác", "loft", "pet", "tìm", "mua", "bán", "thuê", "căn hộ", "chung cư", "nhà", "biệt thự",
             "villa", "đất", "mặt bằng", "quận", "huyện", "phòng ngủ", "tỷ", "tỉ",
             "triệu", "triệu/tháng", "tr/tháng", "diện tích", "hồ bơi", "ban công",
             "nội thất", "hà nội", "hồ chí minh", "đà nẵng", "quận 1", "bình thạnh",
@@ -282,6 +284,32 @@ class ChatAssistantService:
             raw_query=raw_query,
         )
 
+        rental_types = {"phòng trọ": "room", "căn hộ dịch vụ": "serviced_apartment", "ở ghép": "house_share", "nguyên căn": "entire_house"}
+        for phrase, subtype in rental_types.items():
+            if phrase in lower_text:
+                criteria.rental_type = subtype
+                criteria.listing_type = ListingType.RENT
+        if "gác" in lower_text or "mezzanine" in lower_text or "loft" in lower_text:
+            criteria.has_mezzanine = not bool(re.search(r"không (?:có |cần )?gác", lower_text))
+            criteria.listing_type = ListingType.RENT
+        if any(x in lower_text for x in ("thú cưng", "nuôi mèo", "nuôi chó", "pet")):
+            criteria.allow_pets = not bool(re.search(r"(?:không|cấm) (?:nuôi )?(?:thú cưng|chó|mèo|pet)", lower_text))
+            criteria.listing_type = ListingType.RENT
+        if "điện" in lower_text and any(x in lower_text for x in ("nhà nước", "giá dân", "bậc thang")):
+            criteria.electricity_billing = "state_rate"
+            criteria.listing_type = ListingType.RENT
+        deposit = re.search(r"cọc\s*(?:tối đa|không quá|dưới)?\s*(\d+(?:[.,]\d+)?)\s*tháng", lower_text)
+        if deposit:
+            criteria.max_deposit = float(deposit.group(1).replace(",", "."))
+        if any(phrase in lower_text for phrase in ("giờ tự do", "giờ giấc tự do", "không giới nghiêm")):
+            criteria.curfew = False
+        if "máy giặt" in lower_text:
+            criteria.has_washing_machine = True
+        if "không chung chủ" in lower_text:
+            criteria.live_with_owner = False
+        landmark = re.search(r"(?:gần|quanh|xung quanh)\s+(.+?)(?=\s+(?:giá|dưới|có|không|cho|tầm|khoảng)|[,.;]|$)", text, re.I)
+        if landmark:
+            criteria.near_landmark = landmark.group(1).strip()
         return True, criteria
 
     async def execute_hybrid_search(
@@ -306,6 +334,8 @@ class ChatAssistantService:
             query_parts.extend(criteria.amenities)
         if criteria.raw_query:
             query_parts.append(criteria.raw_query)
+        if criteria.near_landmark:
+            query_parts.append(criteria.near_landmark)
 
         search_query_text = " ".join(query_parts).strip() or "bất động sản"
 
@@ -315,6 +345,8 @@ class ChatAssistantService:
         except TypeError:
             query_vector = self.embedding_service.generate_embedding(search_query_text)
 
+        coordinates = await resolve_landmark(criteria)
+
         # Build filter statement
         def apply_filters(stmt):
             if criteria.listing_type:
@@ -331,7 +363,7 @@ class ChatAssistantService:
                 stmt = stmt.where(Property.price >= criteria.min_price)
             if criteria.max_price is not None:
                 stmt = stmt.where(Property.price <= criteria.max_price)
-            return stmt
+            return apply_rental_filters(stmt, criteria, coordinates)
 
         # 1. Vector Search
         vector_map: dict[uuid.UUID, tuple[Property, float, int]] = {}
diff --git a/backend/src/services/embedding.py b/backend/src/services/embedding.py
index 9f75752..ee9a6db 100644
--- a/backend/src/services/embedding.py
+++ b/backend/src/services/embedding.py
@@ -96,6 +96,9 @@ class EmbeddingService:
         area_sqm: float | None = None,
         price: float | None = None,
         currency: str = "VND",
+        rental_type: str | None = None,
+        rental_costs: dict | None = None,
+        rental_rules: dict | None = None,
     ) -> str:
         """
         Construct a consolidated semantic text string from property title, description,
@@ -131,6 +134,9 @@ class EmbeddingService:
         if location_components:
             parts.append(f"Địa chỉ: {', '.join(location_components)}")
 
+        if listing_type == "rent":
+            from src.services.rental import rental_text
+            parts.append(rental_text(rental_type, rental_costs, rental_rules))
         return ". ".join(parts)
 
     def _prepare_text(self, text: str, is_query: bool = False) -> str:
diff --git a/backend/src/services/rental.py b/backend/src/services/rental.py
new file mode 100644
index 0000000..e50b497
--- /dev/null
+++ b/backend/src/services/rental.py
@@ -0,0 +1,67 @@
+"""Shared exact rental predicates and explicit cost units."""
+from decimal import Decimal
+from sqlalchemy import func, cast
+from geoalchemy2 import Geography
+from src.models.property import Property
+
+RULE_KEYS = ("allow_pets", "curfew", "private_bathroom", "has_mezzanine", "has_washing_machine", "live_with_owner", "has_elevator", "fingerprint_lock")
+
+
+def deposit_amount(monthly_rent, deposit_months):
+    if deposit_months is None:
+        return None
+    return Decimal(str(monthly_rent)) * Decimal(str(deposit_months))
+
+
+def apply_rental_filters(stmt, criteria, coordinates=None):
+    values = criteria.model_dump() if hasattr(criteria, "model_dump") else criteria
+    keys = (*RULE_KEYS, "rental_type", "electricity_billing", "max_deposit")
+    if any(values.get(key) is not None for key in keys):
+        stmt = stmt.where(Property.listing_type == "rent", Property.status == "active")
+    if values.get("rental_type") is not None:
+        stmt = stmt.where(Property.rental_type == values["rental_type"])
+    for key in RULE_KEYS:
+        if values.get(key) is not None:
+            stmt = stmt.where(Property.rental_rules[key].as_boolean() == values[key])
+    if values.get("electricity_billing") is not None:
+        stmt = stmt.where(Property.rental_costs["electricity_billing"].as_string() == values["electricity_billing"])
+    if values.get("max_deposit") is not None:
+        stmt = stmt.where(Property.rental_costs["deposit_months"].as_integer() <= values["max_deposit"])
+    if coordinates:
+        lat, lng = coordinates
+        point = cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)
+        stmt = stmt.where(func.ST_DWithin(cast(Property.geom, Geography), point, values.get("radius_km", 3.0) * 1000))
+    return stmt
+
+
+async def resolve_landmark(criteria):
+    landmark = getattr(criteria, "near_landmark", None)
+    if not landmark:
+        return None
+    from src.services.spatial_service import SpatialService
+    if "bách khoa" in landmark.lower() or "bach khoa" in landmark.lower():
+        landmark = "Đại học Bách Khoa Hà Nội"
+    try:
+        location = await SpatialService().geocode_landmark(landmark)
+        return (location.latitude, location.longitude) if location else None
+    except Exception:
+        return None
+
+
+def rental_text(rental_type=None, rental_costs=None, rental_rules=None):
+    labels = {"room": "Phòng trọ", "serviced_apartment": "Căn hộ dịch vụ", "house_share": "Ở ghép", "entire_house": "Nguyên căn"}
+    parts = [labels.get(rental_type, rental_type)] if rental_type else []
+    costs = rental_costs or {}
+    water_unit = "VND/người/tháng" if costs.get("water_unit") == "per_person" else "VND/m³" if costs.get("water_unit") == "per_m3" else "VND (chưa rõ đơn vị)"
+    units = {"electricity_per_kwh": "VND/kWh", "water_cost": water_unit, "deposit_months": "tháng", "parking_fee_monthly": "VND/tháng", "service_fee_monthly": "VND/tháng"}
+    names = {"electricity_per_kwh": "Giá điện", "water_cost": "Giá nước", "deposit_months": "Đặt cọc", "parking_fee_monthly": "Phí gửi xe", "service_fee_monthly": "Phí dịch vụ", "allow_pets": "Cho nuôi thú cưng", "curfew": "Có giờ đóng cửa", "private_bathroom": "Phòng tắm riêng", "has_mezzanine": "Có gác lửng", "has_washing_machine": "Máy giặt", "live_with_owner": "Chung chủ", "has_elevator": "Thang máy", "fingerprint_lock": "Khóa vân tay", "max_occupants": "Số người tối đa", "curfew_time": "Giờ đóng cửa"}
+    for key, value in (rental_costs or {}).items():
+        if value is not None:
+            label = names.get(key, key)
+            display = "điện giá dân, giá nhà nước" if value == "state_rate" else "đơn giá cố định" if value == "fixed" else value
+            parts.append(f"{label} ({key}): {display} {units.get(key, '')}")
+    for key, value in (rental_rules or {}).items():
+        if value is not None:
+            display = "Có" if value is True else "Không" if value is False else value
+            parts.append(f"{names.get(key, key)} ({key}): {display}")
+    return ". ".join(parts)
diff --git a/backend/tests/test_alembic_migrations.py b/backend/tests/test_alembic_migrations.py
index ab27bd0..d12a19e 100644
--- a/backend/tests/test_alembic_migrations.py
+++ b/backend/tests/test_alembic_migrations.py
@@ -37,7 +37,7 @@ def test_alembic_script_directory_and_head_revision():
 
     heads = script.get_heads()
     assert len(heads) == 1, f"Expected exactly 1 head revision, got {heads}"
-    assert heads[0] == "0007", f"Expected head revision to be '0007', got {heads[0]}"
+    assert heads[0] == "0008", f"Expected head revision to be '0008', got {heads[0]}"
 
     rev1 = script.get_revision("0001")
     assert rev1 is not None
diff --git a/backend/tests/test_rentals.py b/backend/tests/test_rentals.py
new file mode 100644
index 0000000..6fb1593
--- /dev/null
+++ b/backend/tests/test_rentals.py
@@ -0,0 +1,174 @@
+from decimal import Decimal
+from unittest.mock import AsyncMock, MagicMock, patch
+import uuid
+import pytest
+from fastapi import BackgroundTasks
+from pydantic import ValidationError
+from sqlalchemy import select
+from sqlalchemy.exc import CompileError
+from sqlalchemy.dialects import postgresql
+from alembic import command
+from tests.test_alembic_migrations import get_alembic_config
+from src.models.property import Property
+from src.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertySearchQuery, SemanticSearchQuery
+from src.schemas.rental import RentalCosts, RentalRules, RentalFilters
+from src.schemas.chat import ChatMessage, ExtractedCriteria
+from src.services.embedding import EmbeddingService
+from src.services.chat_assistant import ChatAssistantService
+from src.services.rental import apply_rental_filters, deposit_amount, rental_text, resolve_landmark
+from src.api.v1.endpoints.properties import create_property, update_property, search_properties, list_properties
+from src.api.v1.endpoints.search import semantic_search
+
+
+def listing(**changes):
+    return dict(title="Phòng trọ sáng", description="Phòng rộng có cửa sổ", property_type="apartment", listing_type="rent", price=3000000, area_sqm=25, address="Đại Cồ Việt", city="Hà Nội", **changes)
+
+
+def sql(stmt):
+    try:
+        return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
+    except CompileError:
+        compiled = stmt.compile(dialect=postgresql.dialect())
+        rendered = str(compiled)
+        for key, value in compiled.params.items():
+            rendered = rendered.replace("%(" + key + ")s", repr(value.value if hasattr(value, "value") else value))
+        return rendered
+
+
+@pytest.mark.parametrize("model,data", [(RentalCosts, {"deposit_months": -1}), (RentalCosts, {"electricity_per_kwh": -1}), (RentalCosts, {"electricity_billing": "free"}), (RentalCosts, {"water_unit": "free"}), (RentalCosts, {"service_fee_monthly": float("inf")}), (RentalRules, {"curfew_time": "24:00"}), (RentalRules, {"max_occupants": 0}), (RentalRules, {"max_occupants": 1.2})])
+def test_invalid_metadata(model, data):
+    with pytest.raises(ValidationError): model.model_validate(data)
+
+
+def test_enums_zero_false_unknown_and_deposit():
+    with pytest.raises(ValidationError): PropertyCreate(**listing(rental_type="hotel"))
+    value = PropertyCreate(**listing(rental_type="room", rental_costs={"deposit_months": 0, "service_fee_monthly": 0}, rental_rules={"allow_pets": False}))
+    assert value.rental_costs.service_fee_monthly == 0
+    assert value.rental_costs.water_cost is None
+    assert value.rental_rules.allow_pets is False
+    assert deposit_amount(3000000, 2) == Decimal("6000000")
+    assert deposit_amount(3000000, 0) == 0
+    assert deposit_amount(3000000, None) is None
+    legacy = PropertyResponse.model_validate(Property(**listing()))
+    assert legacy.rental_costs is None and legacy.rental_rules is None
+
+
+def test_exact_sql_predicates_and_geography():
+    stmt = apply_rental_filters(select(Property), RentalFilters(rental_type="room", allow_pets=False, has_mezzanine=True, max_deposit=0, electricity_billing="state_rate"), (21.0056, 105.8433)).limit(10)
+    query = sql(stmt)
+    for fragment in ["listing_type = 'rent'", "status = 'active'", "rental_type = 'room'", "allow_pets", "= false", "has_mezzanine", "deposit_months", "<= 0", "state_rate", "ST_DWithin", "3000"]:
+        assert fragment in query
+    assert "coalesce" not in query.lower()  # Missing keys remain unknown.
+    assert query.index("deposit_months") < query.index("LIMIT")
+
+
+def test_rental_embedding_text():
+    text = EmbeddingService().build_property_text("Phòng", "Cho thuê", "Hà Nội", listing_type="rent", rental_type="room", rental_costs={"service_fee_monthly": 0, "water_cost": None}, rental_rules={"allow_pets": False})
+    assert "Phòng trọ" in text and "service_fee_monthly): 0" in text and "allow_pets): Không" in text
+    assert "water_cost" not in text
+
+
+def test_chat_rental_intent():
+    _, criteria = ChatAssistantService(MagicMock()).parse_intent_and_criteria([ChatMessage(role="user", content="Tìm phòng trọ có gác cho nuôi thú cưng dưới 5 triệu gần Bách Khoa, điện giá nhà nước cọc tối đa 1 tháng")])
+    assert criteria.listing_type == "rent" and criteria.rental_type == "room"
+    assert criteria.has_mezzanine is True and criteria.allow_pets is True
+    assert criteria.max_price == 5000000 and criteria.max_deposit == 1
+    assert criteria.electricity_billing == "state_rate" and criteria.near_landmark == "Bách Khoa"
+
+
+def test_requested_contract_and_original_chat_example():
+    from src.schemas.rental import RentalCostSchema, RentalRuleSchema
+    costs = dict(deposit_months=1, electricity_per_kwh=3500, water_cost=100000,
+                 water_unit="per_person", service_fee_monthly=0, parking_fee_monthly=50000,
+                 electricity_billing="state_rate")
+    rules = dict(curfew=False, curfew_time=None, allow_pets=True, max_occupants=2,
+                 has_mezzanine=True, private_bathroom=True, has_washing_machine=True,
+                 live_with_owner=False, has_elevator=True, fingerprint_lock=True)
+    assert RentalCostSchema(**costs).model_dump() == costs
+    assert RentalRuleSchema(**rules).model_dump() == rules
+    with pytest.raises(ValidationError):
+        RentalCostSchema(deposit_months=1.5)
+    _, criteria = ChatAssistantService(MagicMock()).parse_intent_and_criteria([
+        ChatMessage(role="user", content="tìm phòng trọ quanh Bách Khoa có gác lửng dưới 3 triệu điện giá dân")])
+    assert criteria.near_landmark == "Bách Khoa"
+    assert criteria.rental_type == "room" and criteria.has_mezzanine is True
+    assert criteria.max_price == 3000000 and criteria.electricity_billing == "state_rate"
+    query = sql(apply_rental_filters(select(Property), RentalFilters(curfew=False, private_bathroom=True)))
+    assert "curfew" in query and "private_bathroom" in query and "= false" in query
+
+
+@pytest.mark.asyncio
+async def test_landmark_resolution_and_unavailable_fallback():
+    point = await resolve_landmark(RentalFilters(near_landmark="Bách Khoa"))
+    assert point == (21.0056, 105.8433)
+    with patch("src.services.spatial_service.SpatialService.geocode_landmark", AsyncMock(return_value=None)):
+        assert await resolve_landmark(RentalFilters(near_landmark="unknown")) is None
+
+
+@pytest.mark.asyncio
+async def test_create_update_round_trip_clear_and_refresh():
+    db = AsyncMock(); db.add = MagicMock()
+    user = MagicMock(id=uuid.uuid4(), role="user")
+    embedding = EmbeddingService()
+    embedding.generate_embedding = MagicMock(return_value=[0.1] * 768)
+    with patch("src.api.v1.endpoints.properties.invalidate_property_caches", AsyncMock()) as invalidate:
+        prop = await create_property(PropertyCreate(**listing(rental_type="room", rental_costs={"service_fee_monthly": 0, "deposit_months": 1}, rental_rules={"allow_pets": False})), BackgroundTasks(), user, db, embedding)
+        assert prop.rental_rules["allow_pets"] is False
+        assert PropertyResponse.model_validate(prop).rental_costs.service_fee_monthly == 0
+        result = MagicMock(); result.scalar_one_or_none.return_value = prop; db.execute.return_value = result
+        embedding.generate_embedding.reset_mock()
+        await update_property(prop.id, PropertyUpdate(rental_costs={"deposit_months": 2}), user, db, embedding)
+        assert prop.rental_costs["service_fee_monthly"] == 0 and prop.rental_costs["deposit_months"] == 2
+        embedding.generate_embedding.assert_called_once()
+        assert "deposit_months): 2" in embedding.generate_embedding.call_args.args[0]
+        await update_property(prop.id, PropertyUpdate(rental_rules=None), user, db, embedding)
+        assert prop.rental_rules is None
+        original_title = prop.title
+        await update_property(prop.id, PropertyUpdate(listing_type="sale"), user, db, embedding)
+        assert prop.rental_type is None and prop.rental_costs is None and prop.rental_rules is None
+        assert prop.title == original_title
+        assert invalidate.await_count == 4
+
+
+@pytest.mark.asyncio
+async def test_all_search_branches_filter_before_limit():
+    db = AsyncMock(); result = MagicMock(); result.all.return_value = []; result.scalars.return_value.all.return_value = []; db.execute.return_value = result
+    embedding = MagicMock(); embedding.generate_embedding.return_value = [0.0] * 768
+    with patch("src.api.v1.endpoints.properties.get_cached_json", AsyncMock(return_value=None)), patch("src.api.v1.endpoints.properties.set_cached_json", AsyncMock()):
+        await search_properties(PropertySearchQuery(query="phòng trọ có gác", allow_pets=False, max_deposit=0), db, embedding)
+    assert db.execute.await_count == 2
+    for call in db.execute.await_args_list:
+        query = sql(call.args[0])
+        assert "allow_pets" in query and "deposit_months" in query and "rental_type = 'room'" in query
+        assert query.index("allow_pets") < query.index("LIMIT")
+    db.execute.reset_mock()
+    with patch("src.api.v1.endpoints.search.get_cached_json", AsyncMock(return_value=None)), patch("src.api.v1.endpoints.search.set_cached_json", AsyncMock()):
+        await semantic_search(SemanticSearchQuery(query_vector=[0.0] * 768, has_mezzanine=False), db)
+    assert "has_mezzanine" in sql(db.execute.call_args.args[0])
+    db.execute.reset_mock()
+    await list_properties(skip=0, limit=20, listing_type=None, property_type=None, city=None, min_price=0, max_price=5000000, rental=RentalFilters(max_deposit=0), status=None, db=db)
+    assert "deposit_months" in sql(db.execute.call_args.args[0])
+
+
+@pytest.mark.asyncio
+async def test_chat_fallback_keeps_exact_filters():
+    db = AsyncMock(); result = MagicMock(); result.scalars.return_value.all.return_value = []; result.all.return_value = []
+    db.execute.side_effect = [RuntimeError("vector unavailable"), result, result]
+    embedding = MagicMock(); embedding.generate_embedding.return_value = [0.0] * 768
+    await ChatAssistantService(embedding).execute_hybrid_search(db, ExtractedCriteria(raw_query="phòng", allow_pets=False, max_deposit=0))
+    assert len(db.execute.await_args_list) >= 2
+    for call in db.execute.await_args_list:
+        query = sql(call.args[0]); assert "allow_pets" in query and "deposit_months" in query
+
+
+def test_migration_upgrade_downgrade_preserves_listing_type(capsys):
+    command.upgrade(get_alembic_config(), "0007:0008", sql=True)
+    upgrade = capsys.readouterr().out
+    assert "ALTER COLUMN listing_type SET DEFAULT 'sale'" in upgrade
+    assert "ADD COLUMN listing_type" not in upgrade
+    assert "rental_costs JSONB" in upgrade and "rental_rules JSONB" in upgrade
+    assert "(listing_type, rental_type, price)" in upgrade
+    command.downgrade(get_alembic_config(), "0008:0007", sql=True)
+    downgrade = capsys.readouterr().out
+    assert "DROP COLUMN rental_costs" in downgrade
+    assert "DROP COLUMN listing_type" not in downgrade
diff --git a/docs/api-specs.md b/docs/api-specs.md
index edfdf5b..71ad1a6 100644
--- a/docs/api-specs.md
+++ b/docs/api-specs.md
@@ -754,3 +754,69 @@ Toàn bộ các endpoint trong module này yêu cầu quyền **`superadmin`** (
     }
   }
   ```
+
+
+## Rental and serviced apartment metadata
+
+Migration `0008` adds nullable `properties.rental_type VARCHAR(50)`, `rental_costs JSONB`,
+and `rental_rules JSONB`, plus the B-tree index `(listing_type, rental_type, price)`.
+It alters the existing `listing_type` default to `sale`; existing `sale`/`rent` rows
+are preserved. Downgrading 0008 removes only its metadata/index and restores the
+previous absent default; it retains `listing_type`. Vectors remain 768-dimensional.
+
+Rental subtypes: `room`, `serviced_apartment`, `house_share`, `entire_house`.
+Rental price is monthly VND. All metadata is optional, including for legacy rows.
+Missing/null values mean unknown; `0` is a known zero charge and `false` is a known
+negative rule. No unknown charge is treated as free and no unknown amenity is shown
+as a positive badge.
+
+`rental_costs`: `electricity_per_kwh` (VND/kWh), `electricity_billing` (`state_rate` or
+`fixed`), `water_cost`, `water_unit` (`per_m3`: VND/m³, `per_person`: VND/person/month),
+`parking_fee_monthly`, `service_fee_monthly` (VND/month), and `deposit_months` (months).
+All numeric costs must be finite and nonnegative. Deposit amount = monthly rent ×
+deposit months. Electricity and water cannot be added to a monthly total without
+usage/person counts; if water billing is absent, its unit remains unknown.
+
+`rental_rules`: nullable booleans `curfew`, `private_bathroom`, `allow_pets`, `has_mezzanine`,
+`has_washing_machine`, `live_with_owner`, `has_elevator`, `fingerprint_lock`;
+`curfew_time` uses 24-hour HH:MM; `max_occupants` is a positive integer.
+
+Create/update requests and property responses carry these objects. Omitted update
+fields (including nested cost/rule keys) are preserved; explicit null clears a
+field or entire object. Changing to sale clears all rental metadata. Changes to
+rental metadata refresh embeddings and invalidate property/search caches.
+
+GET `/api/v1/properties`, POST `/api/v1/properties/search`, POST
+`/api/v1/search/semantic`, and chat share exact rental predicates:
+`rental_type`, all eight boolean rule keys, `electricity_billing`, and `max_deposit`
+(in **months**, not VND). Explicit predicates exclude unknown keys and require
+active rental listings before ranking/limits. GET also supports `min_price` and
+`max_price`. Boolean false and deposit ceiling zero are transmitted unchanged.
+
+`near_landmark` is geocoded and filtered through PostGIS `ST_DWithin` with
+`radius_km` defaulting to 3.0. Bách Khoa resolves to Hanoi University of Science and
+Technology. If geocoding fails, natural-language search retains the landmark in
+its semantic query. Web/mobile rental discovery and chat share structured filters.
+
+Example rental metadata:
+```json
+{
+  "listing_type": "rent",
+  "rental_type": "room",
+  "price": 3000000,
+  "rental_costs": {"electricity_billing": "state_rate", "service_fee_monthly": 0, "deposit_months": 2},
+  "rental_rules": {"has_mezzanine": true, "allow_pets": false, "curfew_time": "23:00", "max_occupants": 2}
+}
+```
+
+Example discovery request:
+```json
+{"query":"phòng trọ gần Bách Khoa", "listing_type":"rent", "has_mezzanine":true, "allow_pets":false, "max_price":5000000, "max_deposit":2, "electricity_billing":"state_rate", "near_landmark":"Bách Khoa", "radius_km":3}
+```
+
+Review migration SQL locally with `cd backend` then
+`uv run alembic upgrade head --sql` and
+`uv run alembic downgrade 0008:0007 --sql`. Apply `uv run alembic upgrade head`
+only to an explicitly selected development database after review. Implementation
+verification does not migrate any live database; offline SQL tests do not prove
+execution on PostgreSQL/PostGIS.
diff --git a/docs/database-design.md b/docs/database-design.md
index cb5b76d..5567a07 100644
--- a/docs/database-design.md
+++ b/docs/database-design.md
@@ -296,3 +296,69 @@ Toàn bộ các bước tiến hóa cơ sở dữ liệu được phiên bản h
    - Bổ sung các cột trạng thái định danh: `phone_verified` (Boolean) và `last_login_at` (TIMESTAMPTZ).
    - Thiết lập chỉ mục B-Tree `ix_users_role` trên bảng `users` tối ưu lọc theo nhóm quyền quản trị.
 
+
+
+## Rental and serviced apartment metadata
+
+Migration `0008` adds nullable `properties.rental_type VARCHAR(50)`, `rental_costs JSONB`,
+and `rental_rules JSONB`, plus the B-tree index `(listing_type, rental_type, price)`.
+It alters the existing `listing_type` default to `sale`; existing `sale`/`rent` rows
+are preserved. Downgrading 0008 removes only its metadata/index and restores the
+previous absent default; it retains `listing_type`. Vectors remain 768-dimensional.
+
+Rental subtypes: `room`, `serviced_apartment`, `house_share`, `entire_house`.
+Rental price is monthly VND. All metadata is optional, including for legacy rows.
+Missing/null values mean unknown; `0` is a known zero charge and `false` is a known
+negative rule. No unknown charge is treated as free and no unknown amenity is shown
+as a positive badge.
+
+`rental_costs`: `electricity_per_kwh` (VND/kWh), `electricity_billing` (`state_rate` or
+`fixed`), `water_cost`, `water_unit` (`per_m3`: VND/m³, `per_person`: VND/person/month),
+`parking_fee_monthly`, `service_fee_monthly` (VND/month), and `deposit_months` (months).
+All numeric costs must be finite and nonnegative. Deposit amount = monthly rent ×
+deposit months. Electricity and water cannot be added to a monthly total without
+usage/person counts; if water billing is absent, its unit remains unknown.
+
+`rental_rules`: nullable booleans `curfew`, `private_bathroom`, `allow_pets`, `has_mezzanine`,
+`has_washing_machine`, `live_with_owner`, `has_elevator`, `fingerprint_lock`;
+`curfew_time` uses 24-hour HH:MM; `max_occupants` is a positive integer.
+
+Create/update requests and property responses carry these objects. Omitted update
+fields (including nested cost/rule keys) are preserved; explicit null clears a
+field or entire object. Changing to sale clears all rental metadata. Changes to
+rental metadata refresh embeddings and invalidate property/search caches.
+
+GET `/api/v1/properties`, POST `/api/v1/properties/search`, POST
+`/api/v1/search/semantic`, and chat share exact rental predicates:
+`rental_type`, all eight boolean rule keys, `electricity_billing`, and `max_deposit`
+(in **months**, not VND). Explicit predicates exclude unknown keys and require
+active rental listings before ranking/limits. GET also supports `min_price` and
+`max_price`. Boolean false and deposit ceiling zero are transmitted unchanged.
+
+`near_landmark` is geocoded and filtered through PostGIS `ST_DWithin` with
+`radius_km` defaulting to 3.0. Bách Khoa resolves to Hanoi University of Science and
+Technology. If geocoding fails, natural-language search retains the landmark in
+its semantic query. Web/mobile rental discovery and chat share structured filters.
+
+Example rental metadata:
+```json
+{
+  "listing_type": "rent",
+  "rental_type": "room",
+  "price": 3000000,
+  "rental_costs": {"electricity_billing": "state_rate", "service_fee_monthly": 0, "deposit_months": 2},
+  "rental_rules": {"has_mezzanine": true, "allow_pets": false, "curfew_time": "23:00", "max_occupants": 2}
+}
+```
+
+Example discovery request:
+```json
+{"query":"phòng trọ gần Bách Khoa", "listing_type":"rent", "has_mezzanine":true, "allow_pets":false, "max_price":5000000, "max_deposit":2, "electricity_billing":"state_rate", "near_landmark":"Bách Khoa", "radius_km":3}
+```
+
+Review migration SQL locally with `cd backend` then
+`uv run alembic upgrade head --sql` and
+`uv run alembic downgrade 0008:0007 --sql`. Apply `uv run alembic upgrade head`
+only to an explicitly selected development database after review. Implementation
+verification does not migrate any live database; offline SQL tests do not prove
+execution on PostgreSQL/PostGIS.
diff --git a/frontend/mobile/lib/models/property.dart b/frontend/mobile/lib/models/property.dart
index 8c6c8c4..e3151fa 100644
--- a/frontend/mobile/lib/models/property.dart
+++ b/frontend/mobile/lib/models/property.dart
@@ -47,6 +47,14 @@ class Property {
   final String description;
   final String propertyType;
   final String listingType;
+  final String? rentalType;
+  final Map<String, dynamic>? rentalCosts;
+  final Map<String, dynamic>? rentalRules;
+
+  double? get depositAmount {
+    final months = rentalCosts?["deposit_months"] as num?;
+    return months == null ? null : price * months.toDouble();
+  }
   final double price;
   final String currency;
   final double areaSqm;
@@ -73,6 +81,9 @@ class Property {
     required this.description,
     required this.propertyType,
     required this.listingType,
+    this.rentalType,
+    this.rentalCosts,
+    this.rentalRules,
     required this.price,
     this.currency = 'VND',
     required this.areaSqm,
@@ -101,6 +112,9 @@ class Property {
       description: (json['description'] as String?) ?? '',
       propertyType: (json['property_type'] as String?) ?? 'apartment',
       listingType: (json['listing_type'] as String?) ?? 'sale',
+      rentalType: json['rental_type'] as String?,
+      rentalCosts: (json['rental_costs'] as Map<String, dynamic>?),
+      rentalRules: (json['rental_rules'] as Map<String, dynamic>?),
       price: ((json['price'] as num?) ?? 0).toDouble(),
       currency: (json['currency'] as String?) ?? 'VND',
       areaSqm: ((json['area_sqm'] as num?) ?? 0).toDouble(),
@@ -137,6 +151,9 @@ class Property {
       'description': description,
       'property_type': propertyType,
       'listing_type': listingType,
+      'rental_type': rentalType,
+      'rental_costs': rentalCosts,
+      'rental_rules': rentalRules,
       'price': price,
       'currency': currency,
       'area_sqm': areaSqm,
diff --git a/frontend/mobile/lib/providers/app_providers.dart b/frontend/mobile/lib/providers/app_providers.dart
index 4ff46dc..4eea747 100644
--- a/frontend/mobile/lib/providers/app_providers.dart
+++ b/frontend/mobile/lib/providers/app_providers.dart
@@ -67,22 +67,26 @@ class SearchFilterState {
   final String query;
   final String? listingType;
   final String? propertyType;
+  final Map<String, dynamic> rentalFilters;
 
   const SearchFilterState({
     this.query = '',
     this.listingType,
     this.propertyType,
+    this.rentalFilters = const {},
   });
 
   SearchFilterState copyWith({
     String? query,
     String? listingType,
     String? propertyType,
+    Map<String, dynamic>? rentalFilters,
     bool clearListingType = false,
     bool clearPropertyType = false,
   }) {
     return SearchFilterState(
       query: query ?? this.query,
+      rentalFilters: rentalFilters ?? this.rentalFilters,
       listingType: clearListingType ? null : (listingType ?? this.listingType),
       propertyType: clearPropertyType ? null : (propertyType ?? this.propertyType),
     );
@@ -101,9 +105,9 @@ class SearchFilterNotifier extends Notifier<SearchFilterState> {
 
   void setListingType(String? type) {
     if (state.listingType == type) {
-      state = state.copyWith(clearListingType: true);
+      state = state.copyWith(clearListingType: true, rentalFilters: {});
     } else {
-      state = state.copyWith(listingType: type);
+      state = state.copyWith(listingType: type, rentalFilters: type == "rent" ? state.rentalFilters : {});
     }
   }
 
@@ -115,6 +119,12 @@ class SearchFilterNotifier extends Notifier<SearchFilterState> {
     }
   }
 
+  void setRentalFilter(String key, dynamic value) {
+    final next = Map<String, dynamic>.from(state.rentalFilters);
+    if (value == null) { next.remove(key); } else { next[key] = value; }
+    state = state.copyWith(listingType: "rent", rentalFilters: next);
+  }
+
   void resetFilters() {
     state = const SearchFilterState();
   }
@@ -131,6 +141,7 @@ final searchResultsProvider = FutureProvider<PropertySearchResponse>((ref) async
     query: filter.query.trim().isEmpty ? 'bất động sản' : filter.query.trim(),
     listingType: filter.listingType,
     propertyType: filter.propertyType,
+    rentalFilters: filter.rentalFilters,
     limit: 25,
   );
 });
diff --git a/frontend/mobile/lib/screens/property_detail_screen.dart b/frontend/mobile/lib/screens/property_detail_screen.dart
index 649a6a0..ac5b177 100644
--- a/frontend/mobile/lib/screens/property_detail_screen.dart
+++ b/frontend/mobile/lib/screens/property_detail_screen.dart
@@ -1,3 +1,4 @@
+import '../widgets/rental_details.dart';
 import 'package:flutter/material.dart';
 import 'package:flutter_riverpod/flutter_riverpod.dart';
 import 'package:cached_network_image/cached_network_image.dart';
@@ -235,7 +236,7 @@ class _PropertyDetailScreenState extends ConsumerState<PropertyDetailScreen> {
                                 const Text('Mức giá', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                                 const SizedBox(height: 4),
                                 Text(
-                                  Formatters.formatPrice(property.price, currency: property.currency),
+                                  '${Formatters.formatPrice(property.price, currency: property.currency)}${property.listingType == 'rent' ? '/tháng' : ''}',
                                   style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.primaryColor),
                                 ),
                               ],
@@ -276,6 +277,7 @@ class _PropertyDetailScreenState extends ConsumerState<PropertyDetailScreen> {
                       // Description with Markdown
                       const Text('Mô tả bất động sản', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                       const SizedBox(height: 8),
+                      RentalDetails(property: property),
                       MarkdownBody(
                         data: property.description,
                         styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
@@ -382,7 +384,7 @@ class _PropertyDetailScreenState extends ConsumerState<PropertyDetailScreen> {
                           ),
                           const SizedBox(height: 2),
                           Text(
-                            Formatters.formatPrice(property.price, currency: property.currency),
+                            '${Formatters.formatPrice(property.price, currency: property.currency)}${property.listingType == 'rent' ? '/tháng' : ''}',
                             maxLines: 1,
                             overflow: TextOverflow.ellipsis,
                             style: const TextStyle(
diff --git a/frontend/mobile/lib/services/property_service.dart b/frontend/mobile/lib/services/property_service.dart
index 1d19e97..2a68d64 100644
--- a/frontend/mobile/lib/services/property_service.dart
+++ b/frontend/mobile/lib/services/property_service.dart
@@ -13,6 +13,7 @@ class PropertyService {
     required String query,
     String? listingType,
     String? propertyType,
+    Map<String, dynamic> rentalFilters = const {},
     double? minPrice,
     double? maxPrice,
     int limit = 20,
@@ -22,6 +23,7 @@ class PropertyService {
         'query': query,
         'limit': limit,
         'enable_hybrid': true,
+        ...rentalFilters,
       };
 
       if (listingType != null && listingType.isNotEmpty) {
diff --git a/frontend/mobile/lib/widgets/property_card.dart b/frontend/mobile/lib/widgets/property_card.dart
index 1132391..07ab0eb 100644
--- a/frontend/mobile/lib/widgets/property_card.dart
+++ b/frontend/mobile/lib/widgets/property_card.dart
@@ -1,3 +1,4 @@
+import '../widgets/rental_details.dart';
 import 'package:flutter/material.dart';
 import 'package:flutter_riverpod/flutter_riverpod.dart';
 import 'package:cached_network_image/cached_network_image.dart';
@@ -168,6 +169,7 @@ class PropertyCard extends ConsumerWidget {
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.start,
                     children: [
+                      RentalBadges(property: property),
                       Text(
                         property.title,
                         maxLines: 2,
@@ -183,7 +185,7 @@ class PropertyCard extends ConsumerWidget {
                         mainAxisAlignment: MainAxisAlignment.spaceBetween,
                         children: [
                           Text(
-                            Formatters.formatPrice(property.price, currency: property.currency),
+                            '${Formatters.formatPrice(property.price, currency: property.currency)}${property.listingType == 'rent' ? '/tháng' : ''}',
                             style: const TextStyle(
                               fontSize: 18,
                               fontWeight: FontWeight.w800,
diff --git a/frontend/mobile/lib/widgets/rental_details.dart b/frontend/mobile/lib/widgets/rental_details.dart
new file mode 100644
index 0000000..2c8a747
--- /dev/null
+++ b/frontend/mobile/lib/widgets/rental_details.dart
@@ -0,0 +1,40 @@
+import 'package:flutter/material.dart';
+import '../models/property.dart';
+const rentalTypeLabels = { 'room': 'Phòng trọ', 'serviced_apartment': 'Căn hộ dịch vụ', 'house_share': 'Ở ghép', 'entire_house': 'Nhà nguyên căn' };
+const rentalRuleLabels = { 'curfew': 'Có giờ đóng cửa', 'private_bathroom': 'Phòng tắm riêng', 'allow_pets': 'Cho nuôi thú cưng', 'has_mezzanine': 'Có gác lửng', 'has_washing_machine': 'Máy giặt', 'live_with_owner': 'Ở cùng chủ', 'has_elevator': 'Thang máy', 'fingerprint_lock': 'Khóa vân tay' };
+class RentalBadges extends StatelessWidget {
+ final Property property;
+ const RentalBadges({super.key, required this.property});
+ @override
+ Widget build(BuildContext context) {
+  if (property.listingType != 'rent') return const SizedBox.shrink();
+  return Wrap(spacing: 8, children: [
+   if (property.rentalType != null) Text(rentalTypeLabels[property.rentalType] ?? property.rentalType!),
+   if (property.rentalRules?['has_mezzanine'] == true) const Text('Có gác lửng'),
+   if (property.rentalRules?['allow_pets'] == true) const Text('Cho nuôi thú cưng'),
+  ]);
+ }
+}
+class RentalDetails extends StatelessWidget {
+ final Property property;
+ const RentalDetails({super.key, required this.property});
+ @override
+ Widget build(BuildContext context) {
+  if (property.listingType != 'rent') return const SizedBox.shrink();
+  final c = property.rentalCosts ?? <String, dynamic>{};
+  final r = property.rentalRules ?? <String, dynamic>{};
+  final waterUnit = c['water_unit'] == 'per_person' ? 'đ/người/tháng' : c['water_unit'] == 'per_m3' ? 'đ/m³' : 'chưa rõ đơn vị';
+  final costs = { 'electricity_per_kwh': 'Điện (đ/kWh)', 'water_cost': 'Nước ($waterUnit)', 'parking_fee_monthly': 'Gửi xe (đ/tháng)', 'service_fee_monthly': 'Dịch vụ (đ/tháng)', 'deposit_months': 'Cọc (tháng)' };
+  return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
+   const Text('Chi phí & nội quy thuê', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
+   RentalBadges(property: property),
+   for (final entry in costs.entries) Text('${entry.value}: ${c[entry.key] ?? "Chưa cung cấp"}'),
+   Text('Tiền đặt cọc: ${property.depositAmount == null ? "Chưa cung cấp" : "${property.depositAmount} đ"}'),
+   Text('Tính điện: ${c["electricity_billing"] == "state_rate" ? "Giá nhà nước" : c["electricity_billing"] == "fixed" ? "Đơn giá cố định" : "Chưa cung cấp"}'),
+   for (final entry in rentalRuleLabels.entries) Text('${entry.value}: ${r[entry.key] == null ? "Chưa cung cấp" : r[entry.key] == true ? "Có" : "Không"}'),
+   Text('Giờ đóng cửa: ${r["curfew_time"] ?? "Chưa cung cấp"}'),
+   Text('Số người tối đa: ${r["max_occupants"] ?? "Chưa cung cấp"}'),
+   const Text('Điện, nước phụ thuộc lượng dùng hoặc số người. Chi phí chưa cung cấp không có nghĩa là miễn phí.'),
+  ])));
+ }
+}
diff --git a/frontend/mobile/lib/widgets/search_and_filter.dart b/frontend/mobile/lib/widgets/search_and_filter.dart
index dfac35f..fdaf27b 100644
--- a/frontend/mobile/lib/widgets/search_and_filter.dart
+++ b/frontend/mobile/lib/widgets/search_and_filter.dart
@@ -1,3 +1,4 @@
+import 'rental_details.dart';
 import 'package:flutter/material.dart';
 import 'package:flutter_riverpod/flutter_riverpod.dart';
 import '../providers/app_providers.dart';
@@ -51,6 +52,37 @@ class _SearchAndFilterHeaderState extends ConsumerState<SearchAndFilterHeader> {
       child: Column(
         crossAxisAlignment: CrossAxisAlignment.start,
         children: [
+          if (filterState.listingType == 'rent') ExpansionTile(
+            title: const Text('Bộ lọc phòng thuê • giá tháng'),
+            children: [
+              DropdownButtonFormField<String>(
+                initialValue: filterState.rentalFilters['rental_type'] as String?,
+                decoration: const InputDecoration(labelText: 'Loại chỗ ở'),
+                items: [const DropdownMenuItem(value: '', child: Text('Tất cả')), ...rentalTypeLabels.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))],
+                onChanged: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter('rental_type', v == '' ? null : v),
+              ),
+              for (final entry in {'min_price': 'Giá từ (đ/tháng)', 'max_price': 'Giá đến (đ/tháng)', 'max_deposit': 'Cọc tối đa (tháng)'}.entries)
+                TextFormField(
+                  key: ValueKey(entry.key), initialValue: filterState.rentalFilters[entry.key]?.toString() ?? '',
+                  decoration: InputDecoration(labelText: entry.value), keyboardType: const TextInputType.numberWithOptions(decimal: true),
+                  onChanged: (v) { final number = double.tryParse(v); if (v.isEmpty || (number != null && number.isFinite && number >= 0)) ref.read(searchFilterProvider.notifier).setRentalFilter(entry.key, number); },
+                ),
+              for (final entry in rentalRuleLabels.entries)
+                DropdownButtonFormField<String>(
+                  decoration: InputDecoration(labelText: entry.value),
+                  initialValue: filterState.rentalFilters[entry.key]?.toString() ?? '',
+                  items: const [DropdownMenuItem(value: '', child: Text('Không giới hạn')), DropdownMenuItem(value: 'true', child: Text('Có')), DropdownMenuItem(value: 'false', child: Text('Không'))],
+                  onChanged: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter(entry.key, v == '' ? null : v == 'true'),
+                ),
+              DropdownButtonFormField<String>(
+                decoration: const InputDecoration(labelText: 'Tính điện'),
+                initialValue: filterState.rentalFilters['electricity_billing'] as String? ?? '',
+                items: const [DropdownMenuItem(value: '', child: Text('Không giới hạn')), DropdownMenuItem(value: 'state_rate', child: Text('Giá nhà nước')), DropdownMenuItem(value: 'fixed', child: Text('Đơn giá cố định'))],
+                onChanged: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter('electricity_billing', v == '' ? null : v),
+              ),
+              TextFormField(initialValue: filterState.rentalFilters['near_landmark'] as String? ?? '', decoration: const InputDecoration(labelText: 'Gần địa điểm (3 km)'), onFieldSubmitted: (v) => ref.read(searchFilterProvider.notifier).setRentalFilter('near_landmark', v.trim().isEmpty ? null : v.trim())),
+            ],
+          ),
           // Semantic Search Bar
           Row(
             children: [
diff --git a/frontend/mobile/test/widget_test.dart b/frontend/mobile/test/widget_test.dart
index 5e71e0b..ce9ccfc 100644
--- a/frontend/mobile/test/widget_test.dart
+++ b/frontend/mobile/test/widget_test.dart
@@ -1,4 +1,5 @@
 import 'package:flutter/material.dart';
+import 'package:space247_mobile/widgets/rental_details.dart';
 import 'package:flutter_test/flutter_test.dart';
 import 'package:flutter_riverpod/flutter_riverpod.dart';
 import 'package:space247_mobile/models/user.dart';
@@ -15,6 +16,22 @@ class FakeFavoriteIdsNotifier extends FavoriteIdsNotifier {
 }
 
 void main() {
+  test('Rental metadata preserves zero, false, unknown and deposit units', () {
+    final property = Property.fromJson({'id': 'rent', 'listing_type': 'rent', 'price': 3000000, 'rental_type': 'room', 'rental_costs': {'deposit_months': 2, 'service_fee_monthly': 0}, 'rental_rules': {'allow_pets': false, 'has_mezzanine': true}});
+    expect(property.depositAmount, 6000000);
+    expect(property.toJson()['rental_costs']['service_fee_monthly'], 0);
+    expect(property.toJson()['rental_rules']['allow_pets'], false);
+    expect(property.rentalCosts?['water_cost'], isNull);
+  });
+  testWidgets('Rental details display fee units and only known positive badges', (tester) async {
+    final property = Property.fromJson({'id': 'rent', 'listing_type': 'rent', 'price': 3000000, 'rental_type': 'room', 'rental_costs': {'deposit_months': 0, 'service_fee_monthly': 0}, 'rental_rules': {'allow_pets': false, 'has_mezzanine': true}});
+    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(child: RentalDetails(property: property)))));
+    expect(find.text('Có gác lửng'), findsOneWidget);
+    expect(find.text('Cho nuôi thú cưng'), findsNothing);
+    expect(find.text('Cho nuôi thú cưng: Không'), findsOneWidget);
+    expect(find.text('Dịch vụ (đ/tháng): 0'), findsOneWidget);
+    expect(find.text('Điện (đ/kWh): Chưa cung cấp'), findsOneWidget);
+  });
   group('Data Models & Formatters Test', () {
     test('User model parses correctly', () {
       final json = {
@@ -126,7 +143,7 @@ void main() {
       await tester.pump();
 
       expect(find.text('Căn hộ River Gate 2PN'), findsOneWidget);
-      expect(find.text('18 triệu VND'), findsOneWidget);
+      expect(find.text('18 triệu VND/tháng'), findsOneWidget);
       expect(find.text('92% match'), findsOneWidget);
       expect(find.text('CHO THUÊ'), findsOneWidget);
     });
diff --git a/frontend/shared/api-client.ts b/frontend/shared/api-client.ts
index 3c203a2..be8603b 100644
--- a/frontend/shared/api-client.ts
+++ b/frontend/shared/api-client.ts
@@ -1,3 +1,4 @@
+import type { RentalFilters } from "./types";
 /**
  * Space247 - Shared API Client
  * Compatible with Next.js (Web) and React Native / Mobile
@@ -243,7 +244,9 @@ export class RealEstateApiClient {
     });
   }
 
-  async listProperties(params?: {
+  async listProperties(params?: RentalFilters & {
+    min_price?: number;
+    max_price?: number;
     skip?: number;
     limit?: number;
     listing_type?: ListingType;
@@ -259,6 +262,9 @@ export class RealEstateApiClient {
     if (params?.city) searchParams.set("city", params.city);
     if (params?.status) searchParams.set("status", params.status);
 
+    for (const [key, value] of Object.entries(params ?? {})) {
+      if (value !== undefined && value !== null) searchParams.set(key, String(value));
+    }
     const queryStr = searchParams.toString();
     const endpoint = `/api/v1/properties${queryStr ? `?${queryStr}` : ""}`;
     return this.request<PropertyResponse[]>(endpoint);
diff --git a/frontend/shared/types.ts b/frontend/shared/types.ts
index e2df132..e97e679 100644
--- a/frontend/shared/types.ts
+++ b/frontend/shared/types.ts
@@ -19,7 +19,49 @@ export type PropertyStatus =
   | "rented"
   | "inactive";
 
+export type RentalType = "room" | "serviced_apartment" | "house_share" | "entire_house";
+export interface RentalCosts {
+  electricity_per_kwh?: number | null;
+  electricity_billing?: "state_rate" | "fixed" | null;
+  water_cost?: number | null;
+  water_unit?: "per_m3" | "per_person" | null;
+
+  parking_fee_monthly?: number | null;
+  service_fee_monthly?: number | null;
+  deposit_months?: number | null;
+}
+export interface RentalRules {
+  curfew?: boolean | null;
+  private_bathroom?: boolean | null;
+  allow_pets?: boolean | null;
+  has_mezzanine?: boolean | null;
+  has_washing_machine?: boolean | null;
+  live_with_owner?: boolean | null;
+  has_elevator?: boolean | null;
+  fingerprint_lock?: boolean | null;
+  curfew_time?: string | null;
+  max_occupants?: number | null;
+}
+export interface RentalFilters {
+  rental_type?: RentalType;
+  curfew?: boolean | null;
+  private_bathroom?: boolean | null;
+  allow_pets?: boolean;
+  has_mezzanine?: boolean;
+  has_washing_machine?: boolean;
+  live_with_owner?: boolean;
+  has_elevator?: boolean;
+  fingerprint_lock?: boolean;
+  electricity_billing?: "state_rate" | "fixed";
+  max_deposit?: number;
+  near_landmark?: string;
+  radius_km?: number;
+}
+
 export interface PropertyBase {
+  rental_type?: RentalType | null;
+  rental_costs?: RentalCosts | null;
+  rental_rules?: RentalRules | null;
   title: string;
   description: string;
   property_type: PropertyType;
@@ -73,7 +115,7 @@ export interface PropertyDetailResponse extends PropertyResponse {
   agent?: PropertyAgent | null;
 }
 
-export interface SemanticSearchQuery {
+export interface SemanticSearchQuery extends RentalFilters {
   query_vector: number[]; // 768 dimensions
   listing_type?: ListingType;
   property_type?: PropertyType;
@@ -90,7 +132,7 @@ export interface SemanticSearchQuery {
   threshold?: number;
 }
 
-export interface PropertySearchQuery {
+export interface PropertySearchQuery extends RentalFilters {
   query: string; // Natural language query text in Vietnamese or English
   listing_type?: ListingType;
   property_type?: PropertyType;
@@ -261,7 +303,7 @@ export interface ChatMessage {
   content: string;
 }
 
-export interface ExtractedCriteria {
+export interface ExtractedCriteria extends RentalFilters {
   listing_type?: ListingType | null;
   property_type?: PropertyType | null;
   city?: string | null;
diff --git a/frontend/web/src/app/properties/[id]/edit/page.tsx b/frontend/web/src/app/properties/[id]/edit/page.tsx
index 8ba1bea..bb33013 100644
--- a/frontend/web/src/app/properties/[id]/edit/page.tsx
+++ b/frontend/web/src/app/properties/[id]/edit/page.tsx
@@ -1,4 +1,5 @@
 "use client";
+import RentalForm, { rentalSchema, type RentalValue } from "@/components/RentalForm";
 
 import { useState, useEffect, useTransition } from "react";
 import { useParams, useRouter } from "next/navigation";
@@ -86,6 +87,7 @@ export default function EditPropertyPage() {
   const [title, setTitle] = useState("");
   const [description, setDescription] = useState("");
   const [propertyType, setPropertyType] = useState<PropertyType>("apartment");
+  const [rental, setRental] = useState<RentalValue>({});
   const [listingType, setListingType] = useState<ListingType>("sale");
   const [status, setStatus] = useState<PropertyStatus>("active");
   const [priceStr, setPriceStr] = useState("");
@@ -232,6 +234,7 @@ export default function EditPropertyPage() {
         setDescription(data.description);
         setPropertyType(data.property_type);
         setListingType(data.listing_type);
+        setRental({ rental_type: data.rental_type, rental_costs: data.rental_costs, rental_rules: data.rental_rules });
         setStatus(data.status);
         setPriceStr(String(data.price));
         setAreaStr(String(data.area_sqm));
@@ -304,9 +307,11 @@ export default function EditPropertyPage() {
       return;
     }
 
+    const rentalParsed = rentalSchema.safeParse(listingType === "rent" ? rental : { rental_type: null, rental_costs: null, rental_rules: null });
+    if (!rentalParsed.success) { setServerError("Vui lòng kiểm tra chi phí và nội quy thuê."); return; }
     startTransition(async () => {
       try {
-        const updated = await apiClient.updateProperty(propertyId, parsed.data);
+        const updated = await apiClient.updateProperty(propertyId, { ...parsed.data, ...rentalParsed.data });
         setProperty(updated);
         setSuccessMessage("Cập nhật tin đăng và tái tạo vector embedding thành công!");
         setTimeout(() => {
@@ -383,6 +388,7 @@ export default function EditPropertyPage() {
         )}
 
         <form onSubmit={handleSubmit} className="space-y-8">
+        {listingType === "rent" && <RentalForm value={rental} onChange={setRental} />}
           {/* Card 1: Trạng thái & Loại hình */}
           <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
             <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-6">
diff --git a/frontend/web/src/app/properties/[id]/page.tsx b/frontend/web/src/app/properties/[id]/page.tsx
index d72e3ec..3106d30 100644
--- a/frontend/web/src/app/properties/[id]/page.tsx
+++ b/frontend/web/src/app/properties/[id]/page.tsx
@@ -1,3 +1,4 @@
+import RentalDetails from "@/components/RentalDetails";
 import Link from "next/link";
 import { notFound } from "next/navigation";
 import {
@@ -227,6 +228,7 @@ export default async function PropertyDetailPage({ params }: PropertyDetailPageP
             </div>
           )}
 
+          <RentalDetails property={property} />
           {/* Mortgage & Financial Affordability Calculator (Chỉ hiển thị cho tin Bán, ẩn với tin Cho thuê) */}
           {property.listing_type !== "rent" && (
             <MortgageCalculator
diff --git a/frontend/web/src/app/properties/create/page.tsx b/frontend/web/src/app/properties/create/page.tsx
index 1835a0a..36170f9 100644
--- a/frontend/web/src/app/properties/create/page.tsx
+++ b/frontend/web/src/app/properties/create/page.tsx
@@ -1,4 +1,5 @@
 "use client";
+import RentalForm, { rentalSchema, type RentalValue } from "@/components/RentalForm";
 
 import { useState, useEffect, useTransition, Suspense } from "react";
 import { useRouter, useSearchParams } from "next/navigation";
@@ -136,6 +137,7 @@ function CreatePropertyFormContent() {
   const [title, setTitle] = useState("");
   const [description, setDescription] = useState("");
   const [propertyType, setPropertyType] = useState<PropertyType>("apartment");
+  const [rental, setRental] = useState<RentalValue>({});
   const [listingType, setListingType] = useState<ListingType>("sale");
   const [priceStr, setPriceStr] = useState("");
   const [areaStr, setAreaStr] = useState("");
@@ -169,6 +171,7 @@ function CreatePropertyFormContent() {
         setDescription(prop.description || "");
         setPropertyType(prop.property_type);
         setListingType(prop.listing_type);
+        setRental({ rental_type: prop.rental_type, rental_costs: prop.rental_costs, rental_rules: prop.rental_rules });
         setPriceStr(prop.price?.toString() || "");
         setAreaStr(prop.area_sqm?.toString() || "");
         setBedroomsStr(prop.num_bedrooms?.toString() || "2");
@@ -443,9 +446,11 @@ function CreatePropertyFormContent() {
       return;
     }
 
+    const rentalParsed = rentalSchema.safeParse(listingType === "rent" ? rental : { rental_type: null, rental_costs: null, rental_rules: null });
+    if (!rentalParsed.success) { setServerError("Vui lòng kiểm tra chi phí và nội quy thuê."); return; }
     startTransition(async () => {
       try {
-        const createdProperty = await apiClient.createProperty(validation.data);
+        const createdProperty = await apiClient.createProperty({ ...validation.data, ...rentalParsed.data });
         setSuccessInfo({ id: createdProperty.id, title: createdProperty.title });
 
         // Smooth redirect to detail page
@@ -564,6 +569,7 @@ function CreatePropertyFormContent() {
       )}
 
       <form onSubmit={handleSubmit} className="space-y-8">
+        {listingType === "rent" && <RentalForm value={rental} onChange={setRental} />}
         {/* SECTION 1: Category & Purpose */}
         <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
           <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
diff --git a/frontend/web/src/app/rentals/page.tsx b/frontend/web/src/app/rentals/page.tsx
new file mode 100644
index 0000000..b3f655a
--- /dev/null
+++ b/frontend/web/src/app/rentals/page.tsx
@@ -0,0 +1,30 @@
+"use client";
+import { useEffect, useState } from "react";
+import Link from "next/link";
+import type { PropertyResponse, RentalFilters, RentalType } from "@shared/types";
+import { apiClient } from "@/lib/api";
+import PropertyCard from "@/components/PropertyCard";
+import { rentalLabels, ruleLabels } from "@/components/RentalDetails";
+export default function RentalsPage() {
+ const [items,setItems] = useState<PropertyResponse[]>([]);
+ const [filters,setFilters] = useState<RentalFilters>({});
+ const [query,setQuery] = useState(""); const [min,setMin] = useState(""); const [max,setMax] = useState("");
+ const [busy,setBusy] = useState(false); const [error,setError] = useState(""); const [page,setPage] = useState(0);
+ const [hasMore,setHasMore] = useState(false);
+ const input = "rounded-xl border p-3 bg-white w-full";
+ async function search(nextPage = 0) {
+  setBusy(true); setError("");
+  try {
+   let found: PropertyResponse[];
+   const params = { ...filters, listing_type: "rent" as const, min_price: min === "" ? undefined : Number(min), max_price: max === "" ? undefined : Number(max) };
+   if (query.trim() || filters.near_landmark) {
+    const response = await apiClient.searchProperties({ ...params, query: [query.trim(), filters.near_landmark].filter(Boolean).join(" ") || "phòng cho thuê", limit: 100 });
+    found = response.results.map(item => item.property); setHasMore(false);
+   } else { found = await apiClient.listProperties({ ...params, skip: nextPage * 20, limit: 20 }); setHasMore(found.length === 20); }
+   setItems(found); setPage(nextPage);
+  } catch (e) { setError(e instanceof Error ? e.message : "Không thể tải tin cho thuê"); }
+  finally { setBusy(false); }
+ }
+ useEffect(() => { void search(); }, []);
+ return <main className="mx-auto max-w-7xl p-6 space-y-8"><header><nav aria-label="Loại giao dịch" className="flex gap-3 mb-5"><Link className="rounded-full border px-5 py-2" href="/?listing_type=sale">Mua bán</Link><Link className="rounded-full bg-blue-700 text-white px-5 py-2" aria-current="page" href="/rentals">Cho thuê</Link></nav><p className="text-blue-700 font-semibold">SPACE247 • CHO THUÊ</p><h1 className="text-3xl font-bold mt-2">Phòng trọ & căn hộ dịch vụ</h1><p className="mt-3 text-slate-600">Tìm chỗ ở theo ngân sách tháng, chi phí và nội quy minh bạch.</p></header><form className="rounded-2xl bg-slate-50 border p-5 grid sm:grid-cols-2 lg:grid-cols-3 gap-4" onSubmit={e => { e.preventDefault(); void search(); }}><label>Tìm kiếm<input className={input} value={query} onChange={e => setQuery(e.target.value)} placeholder="Phòng có gác gần Bách Khoa" /></label><label>Loại chỗ ở<select className={input} value={filters.rental_type ?? ""} onChange={e => setFilters({ ...filters, rental_type: (e.target.value || undefined) as RentalType | undefined })}><option value="">Tất cả</option>{Object.entries(rentalLabels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label><label>Gần địa điểm (bán kính 3 km)<input className={input} value={filters.near_landmark ?? ""} onChange={e => setFilters({ ...filters, near_landmark: e.target.value || undefined })} placeholder="Bách Khoa, Hà Nội" /></label><label>Giá tối thiểu (đ/tháng)<input className={input} type="number" min="0" value={min} onChange={e => setMin(e.target.value)} /></label><label>Giá tối đa (đ/tháng)<input className={input} type="number" min={min || 0} value={max} onChange={e => setMax(e.target.value)} /></label><label>Cọc tối đa (tháng)<input className={input} type="number" min="0" step="any" value={filters.max_deposit ?? ""} onChange={e => setFilters({ ...filters, max_deposit: e.target.value === "" ? undefined : Number(e.target.value) })} /></label>{Object.entries(ruleLabels).map(([key,label]) => <label key={key}>{label}<select className={input} value={filters[key as keyof typeof ruleLabels] == null ? "" : String(filters[key as keyof typeof ruleLabels])} onChange={e => setFilters({ ...filters, [key]: e.target.value === "" ? undefined : e.target.value === "true" })}><option value="">Không giới hạn</option><option value="true">Có</option><option value="false">Không</option></select></label>)}<label>Tính điện<select className={input} value={filters.electricity_billing ?? ""} onChange={e => setFilters({ ...filters, electricity_billing: (e.target.value || undefined) as RentalFilters["electricity_billing"] })}><option value="">Không giới hạn</option><option value="state_rate">Giá nhà nước</option><option value="fixed">Đơn giá cố định</option></select></label><button disabled={busy} className="rounded-xl bg-blue-700 text-white p-3 self-end">{busy ? "Đang tìm…" : "Tìm chỗ ở"}</button></form>{error && <p role="alert" className="text-red-700">{error}</p>}<p aria-live="polite">{items.length} tin trên trang {page + 1}</p><div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{items.map(item => <PropertyCard key={item.id} item={item} />)}</div>{!busy && items.length === 0 && <p>Không có tin phù hợp. Hãy điều chỉnh bộ lọc.</p>}<div className="flex gap-4"><button disabled={busy || page === 0} onClick={() => void search(page - 1)}>Trang trước</button><button disabled={busy || !hasMore} onClick={() => void search(page + 1)}>Trang sau</button></div></main>;
+}
diff --git a/frontend/web/src/components/Navbar.tsx b/frontend/web/src/components/Navbar.tsx
index 66d8df8..b0456e8 100644
--- a/frontend/web/src/components/Navbar.tsx
+++ b/frontend/web/src/components/Navbar.tsx
@@ -34,7 +34,7 @@ function NavbarContent() {
 
   const isExploreActive = pathname === "/" && !listingType && view !== "map";
   const isSaleActive = pathname === "/" && listingType === "sale";
-  const isRentActive = pathname === "/" && listingType === "rent";
+  const isRentActive = pathname === "/rentals" || (pathname === "/" && listingType === "rent");
   const isMapActive = pathname === "/" && view === "map";
 
   const { user, logout } = useAuth();
@@ -154,7 +154,7 @@ function NavbarContent() {
             Mua bán
           </Link>
           <Link
-            href="/?listing_type=rent"
+            href="/rentals"
             className={`transition hover:text-blue-600 ${
               isRentActive ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
             }`}
@@ -484,7 +484,7 @@ function NavbarContent() {
               <span>Nhà đất bán</span>
             </Link>
             <Link
-              href="/?listing_type=rent"
+              href="/rentals"
               onClick={() => setMobileMenuOpen(false)}
               className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                 isRentActive
diff --git a/frontend/web/src/components/PropertyCard.tsx b/frontend/web/src/components/PropertyCard.tsx
index 21c74e0..41fc9de 100644
--- a/frontend/web/src/components/PropertyCard.tsx
+++ b/frontend/web/src/components/PropertyCard.tsx
@@ -1,3 +1,4 @@
+import { RentalBadges } from "./RentalDetails";
 import Link from "next/link";
 import { Bed, Bath, Maximize2, MapPin, BadgeCheck, ArrowUpRight, Heart } from "lucide-react";
 import { PropertyResponse, SearchResultItem } from "@shared/types";
@@ -98,6 +99,7 @@ export default function PropertyCard({ item, index = 0 }: PropertyCardProps) {
 
         {/* Title */}
         <Link href={`/properties/${property.id}`} className="mt-2.5 block group-hover:text-blue-600 transition">
+          <RentalBadges property={property} />
           <h3 className="line-clamp-2 text-base font-semibold text-slate-900 leading-snug">
             {property.title}
           </h3>
diff --git a/frontend/web/src/components/RentalDetails.tsx b/frontend/web/src/components/RentalDetails.tsx
new file mode 100644
index 0000000..25e68ef
--- /dev/null
+++ b/frontend/web/src/components/RentalDetails.tsx
@@ -0,0 +1,25 @@
+import type { PropertyResponse, RentalType } from "@shared/types";
+import { Bath, Clock, DoorOpen, Fingerprint, Layers, PawPrint, WashingMachine, Building2 } from "lucide-react";
+export const rentalLabels: Record<RentalType, string> = { room: "Phòng trọ", serviced_apartment: "Căn hộ dịch vụ", house_share: "Ở ghép", entire_house: "Nhà nguyên căn" };
+export const ruleLabels = { curfew: "Có giờ đóng cửa", private_bathroom: "Phòng tắm riêng", allow_pets: "Cho nuôi thú cưng", has_mezzanine: "Có gác lửng", has_washing_machine: "Máy giặt", live_with_owner: "Ở cùng chủ", has_elevator: "Thang máy", fingerprint_lock: "Khóa vân tay" };
+export const costLabels = { electricity_per_kwh: "Điện (đ/kWh)", water_cost: "Nước", parking_fee_monthly: "Gửi xe (đ/tháng)", service_fee_monthly: "Dịch vụ (đ/tháng)", deposit_months: "Đặt cọc (tháng)" };
+export function RentalBadges({ property }: { property: PropertyResponse }) {
+  if (property.listing_type !== "rent") return null;
+  return <div className="flex flex-wrap gap-2 text-xs text-blue-800">{property.rental_type && <span>{rentalLabels[property.rental_type]}</span>}{property.rental_rules?.has_mezzanine === true && <span>• Có gác lửng</span>}{property.rental_rules?.allow_pets === true && <span>• Cho nuôi thú cưng</span>}</div>;
+}
+export default function RentalDetails({ property }: { property: PropertyResponse }) {
+  if (property.listing_type !== "rent") return null;
+  const c = property.rental_costs;
+  const r = property.rental_rules;
+  const unknown = "Chưa cung cấp";
+  const icons = { curfew: Clock, private_bathroom: Bath, allow_pets: PawPrint, has_mezzanine: Layers, has_washing_machine: WashingMachine, live_with_owner: DoorOpen, has_elevator: Building2, fingerprint_lock: Fingerprint };
+  return <div className="space-y-5"><section className="rounded-2xl border bg-white p-6 space-y-4"><h2 className="text-xl font-bold">Biểu phí sinh hoạt & Đặt cọc</h2><RentalBadges property={property} /><p>Giá thuê: {property.price.toLocaleString("vi-VN")} đ/tháng</p><dl className="grid gap-3 sm:grid-cols-2">{Object.entries(costLabels).map(([key, label]) => {
+    const value = c?.[key as keyof typeof costLabels];
+    const waterUnit = c?.water_unit === "per_person" ? "đ/người/tháng" : c?.water_unit === "per_m3" ? "đ/m³" : "(chưa rõ đơn vị)";
+    return <div key={key}><dt className="text-slate-500">{label}{key === "water_cost" ? ` (${waterUnit})` : ""}</dt><dd>{value == null ? unknown : value.toLocaleString("vi-VN")}</dd></div>;
+  })}<div><dt>Tiền đặt cọc</dt><dd>{c?.deposit_months == null ? unknown : `${(property.price * c.deposit_months).toLocaleString("vi-VN")} đ`}</dd></div><div><dt>Cách tính điện</dt><dd>{c?.electricity_billing === "state_rate" ? "Giá nhà nước" : c?.electricity_billing === "fixed" ? "Đơn giá cố định" : unknown}</dd></div></dl><p className="text-sm text-slate-500">Điện, nước phụ thuộc lượng sử dụng hoặc số người; chưa thể cộng vào tổng chi phí tháng. Mục chưa cung cấp không có nghĩa là miễn phí.</p></section><section className="rounded-2xl border bg-white p-6 space-y-4"><h2 className="text-xl font-bold">Quy định & Tiện nghi phòng trọ</h2><dl className="grid gap-4 sm:grid-cols-2">{Object.entries(ruleLabels).map(([key, label]) => {
+    const value = r?.[key as keyof typeof ruleLabels];
+    const Icon = icons[key as keyof typeof icons];
+    return <div key={key}><dt className="flex items-center gap-2 text-slate-500"><Icon size={18} aria-hidden="true" />{label}</dt><dd>{value == null ? unknown : key === "curfew" && !value ? "Giờ giấc tự do" : key === "live_with_owner" && !value ? "Không chung chủ" : value ? "Có" : "Không"}</dd></div>;
+  })}{r?.curfew !== false && <div><dt>Giờ đóng cửa</dt><dd>{r?.curfew_time ?? unknown}</dd></div>}<div><dt>Số người tối đa</dt><dd>{r?.max_occupants ?? unknown}</dd></div></dl></section></div>;
+}
diff --git a/frontend/web/src/components/RentalForm.tsx b/frontend/web/src/components/RentalForm.tsx
new file mode 100644
index 0000000..b1c8dd7
--- /dev/null
+++ b/frontend/web/src/components/RentalForm.tsx
@@ -0,0 +1,16 @@
+"use client";
+import { z } from "zod";
+import type { RentalCosts, RentalRules, RentalType } from "@shared/types";
+import { rentalLabels, ruleLabels, costLabels } from "./RentalDetails";
+const amount = z.number().int().min(0).nullable().optional();
+export const rentalSchema = z.object({
+ rental_type: z.enum(["room", "serviced_apartment", "house_share", "entire_house"]).nullable().optional(),
+ rental_costs: z.object({ electricity_per_kwh: amount, water_cost: amount, parking_fee_monthly: amount, service_fee_monthly: amount, deposit_months: amount, electricity_billing: z.enum(["state_rate", "fixed"]).nullable().optional(), water_unit: z.enum(["per_m3", "per_person"]).nullable().optional() }).nullable().optional(),
+ rental_rules: z.object({ curfew: z.boolean().nullable().optional(), private_bathroom: z.boolean().nullable().optional(), allow_pets: z.boolean().nullable().optional(), has_mezzanine: z.boolean().nullable().optional(), has_washing_machine: z.boolean().nullable().optional(), live_with_owner: z.boolean().nullable().optional(), has_elevator: z.boolean().nullable().optional(), fingerprint_lock: z.boolean().nullable().optional(), curfew_time: z.string().regex(/^(?:[01]\d|2[0-3]):[0-5]\d$/).nullable().optional(), max_occupants: z.number().int().min(1).nullable().optional() }).nullable().optional(),
+});
+export type RentalValue = { rental_type?: RentalType | null; rental_costs?: RentalCosts | null; rental_rules?: RentalRules | null };
+export default function RentalForm({ value, onChange }: { value: RentalValue; onChange: (value: RentalValue) => void }) {
+ const c = value.rental_costs ?? {}; const r = value.rental_rules ?? {};
+ const input = "block w-full rounded-lg border p-2 mt-1 bg-white";
+ return <fieldset className="rounded-2xl border bg-blue-50 p-5 space-y-4"><legend className="font-bold">Thông tin cho thuê</legend><p>Giá thuê tính bằng VND/tháng. Để trống nếu chưa rõ; nhập 0 khi miễn phí.</p><label>Loại phòng<select className={input} value={value.rental_type ?? ""} onChange={e => onChange({ ...value, rental_type: (e.target.value || null) as RentalType | null })}><option value="">Chưa cung cấp</option>{Object.entries(rentalLabels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label><div className="grid sm:grid-cols-2 gap-4">{Object.entries(costLabels).map(([key,label]) => <label key={key}>{label}<input className={input} type="number" min="0" step="1" value={c[key as keyof typeof costLabels] ?? ""} onChange={e => onChange({ ...value, rental_costs: { ...c, [key]: e.target.value === "" ? null : Number(e.target.value) } })} /></label>)}<label>Tính điện<select className={input} value={c.electricity_billing ?? ""} onChange={e => onChange({ ...value, rental_costs: { ...c, electricity_billing: (e.target.value || null) as RentalCosts["electricity_billing"] } })}><option value="">Chưa cung cấp</option><option value="state_rate">Giá nhà nước</option><option value="fixed">Đơn giá cố định</option></select></label><label>Tính nước<select className={input} value={c.water_unit ?? ""} onChange={e => onChange({ ...value, rental_costs: { ...c, water_unit: (e.target.value || null) as RentalCosts["water_unit"] } })}><option value="">Chưa cung cấp</option><option value="per_m3">đ/m³</option><option value="per_person">đ/người/tháng</option></select></label>{Object.entries(ruleLabels).map(([key,label]) => <label key={key}>{label}<select className={input} value={r[key as keyof typeof ruleLabels] == null ? "" : String(r[key as keyof typeof ruleLabels])} onChange={e => onChange({ ...value, rental_rules: { ...r, [key]: e.target.value === "" ? null : e.target.value === "true" } })}><option value="">Chưa cung cấp</option><option value="true">Có</option><option value="false">Không</option></select></label>)}<label>Giờ đóng cửa<input className={input} type="time" value={r.curfew_time ?? ""} onChange={e => onChange({ ...value, rental_rules: { ...r, curfew_time: e.target.value || null } })}/></label><label>Số người tối đa<input className={input} type="number" min="1" step="1" value={r.max_occupants ?? ""} onChange={e => onChange({ ...value, rental_rules: { ...r, max_occupants: e.target.value === "" ? null : Number(e.target.value) } })}/></label></div></fieldset>;
+}
diff --git a/frontend/web/src/components/SearchSection.tsx b/frontend/web/src/components/SearchSection.tsx
index d115f53..73b26ce 100644
--- a/frontend/web/src/components/SearchSection.tsx
+++ b/frontend/web/src/components/SearchSection.tsx
@@ -1,5 +1,6 @@
 "use client";
 
+import Link from "next/link";
 import { useEffect, useState } from "react";
 import { Search, Compass, Filter, SlidersHorizontal, Loader2 } from "lucide-react";
 import { ListingType, PropertyType } from "@shared/types";
@@ -43,6 +44,15 @@ export default function SearchSection({
   };
 
   const getPriceBounds = (val: string): { min?: number; max?: number } => {
+    if (listingType === "rent") {
+      switch (val) {
+        case "under_2b": return { max: 3_000_000 };
+        case "2b_5b": return { min: 3_000_000, max: 5_000_000 };
+        case "5b_10b": return { min: 5_000_000, max: 10_000_000 };
+        case "above_10b": return { min: 10_000_000 };
+        default: return {};
+      }
+    }
     switch (val) {
       case "under_2b":
         return { max: 2_000_000_000 };
@@ -112,6 +122,7 @@ export default function SearchSection({
         </p>
 
         {/* Search Box Form */}
+        {listingType === "rent" && <Link className="block text-blue-200 underline mb-4" href="/rentals">Lọc phòng trọ, chi phí tháng & nội quy thuê →</Link>}
         <form onSubmit={handleSubmit} className="mt-8">
           <div className="flex flex-col gap-3 sm:flex-row items-center rounded-2xl bg-white/10 p-2 backdrop-blur-xl border border-white/20 shadow-2xl">
             <div className="relative flex-1 w-full flex items-center">
@@ -240,10 +251,10 @@ export default function SearchSection({
               className="rounded-lg bg-slate-800/80 px-3 py-1.5 text-xs text-white border border-white/15 focus:outline-hidden"
             >
               <option value="all">Mọi mức giá</option>
-              <option value="under_2b">Dưới 2 tỷ</option>
-              <option value="2b_5b">2 tỷ - 5 tỷ</option>
-              <option value="5b_10b">5 tỷ - 10 tỷ</option>
-              <option value="above_10b">Trên 10 tỷ</option>
+              <option value="under_2b">{listingType === "rent" ? "Dưới 3 triệu/tháng" : "Dưới 2 tỷ"}</option>
+              <option value="2b_5b">{listingType === "rent" ? "3 - 5 triệu/tháng" : "2 tỷ - 5 tỷ"}</option>
+              <option value="5b_10b">{listingType === "rent" ? "5 - 10 triệu/tháng" : "5 tỷ - 10 tỷ"}</option>
+              <option value="above_10b">{listingType === "rent" ? "Trên 10 triệu/tháng" : "Trên 10 tỷ"}</option>
             </select>
 
             {/* Hybrid Search Toggle */}

Do not invoke any skill, and do not spawn subagents of your own — you are the reviewer. If the instruction file is unreadable, report that exact failure and stop. Return your findings as text in your final message; do not route them through any findings-reporting tool the host may offer.