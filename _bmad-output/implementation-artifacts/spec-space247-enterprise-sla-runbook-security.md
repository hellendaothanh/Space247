---
title: 'Add Enterprise SLA, Operations Runbook, and Security & Privacy Standards'
type: 'chore'
created: '2026-09-05'
status: 'done'
baseline_commit: '2c21b9c7cf4c281358a984df30b427b2b0475308'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** While core microservices and technical documentation exist, Space247 lacks enterprise operational governance artifacts: explicitly defined SLA & performance benchmarks, an incident response runbook for PostgreSQL/PostGIS/Redis outages, comprehensive security & data privacy policies (Decree 13/2023/ND-CP, rate limiting, phone masking), and unified links in the documentation index.

**Approach:** 
1. Establish `docs/performance-sla.md` defining latency SLAs (Hybrid Search < 200ms P95, Vector ANN < 80ms P95, Redis hit < 15ms, CRUD < 50ms), monitoring profiling, cache hit ratio >= 80%, and load testing methodologies.
2. Establish `docs/runbook.md` detailing database troubleshooting, deadlock checks, `REINDEX INDEX CONCURRENTLY` for GiST and HNSW, Redis graceful degradation & cache flushing, and vector re-indexing batch workflows (`--reindex-vectors`).
3. Establish `docs/security-privacy.md` documenting identity management (Bcrypt cost 12, JWT 24h, RBAC), phone number masking policies, rate limiting, and PDPA compliance.
4. Update cross-links in `README.md` and `docs/project-overview.md` to reference all new enterprise docs without dead links.
5. Add `--reindex-vectors` CLI flag to `backend/scripts/seed_properties.py` so the documented batch recovery command is fully executable.
6. Verify quality gates: `uv run pytest` 101/101 PASS, web `npx tsc --noEmit` & `npm run build` 0 errors.

## Boundaries & Constraints

**Always:**
- Keep all existing tests at 100% PASS (101/101 tests in backend).
- Ensure TypeScript compilation (`npx tsc --noEmit`) and Next.js 16 build (`npm run build`) succeed with 0 errors.
- Ensure all technical documentation is written in objective, professional Vietnamese with standard technical terms.
- Strictly forbid AI cliché emojis (such as 🚀, 🤖, ✨, 💡, 🧠, ⚡, 📌).

**Never:**
- Do not skip, disable, or delete test suites.
- Do not hardcode secrets or mock credentials.
- Do not leave broken markdown links.

</frozen-after-approval>

## Code Map

- `backend/scripts/seed_properties.py` -- Support `--reindex-vectors` CLI argument to regenerate 768-dim embeddings for all existing database properties.
- `docs/performance-sla.md` -- SLA targets, P95 metrics, monitoring profiling middleware, load testing methodology.
- `docs/runbook.md` -- Incident triage, PostGIS/pgvector deadlocks, REINDEX CONCURRENTLY, Redis graceful degradation, vector recovery.
- `docs/security-privacy.md` -- Bcrypt cost 12, JWT 24h, RBAC, phone masking policy, rate limiting, PDPA Decree 13/2023/ND-CP.
- `docs/project-overview.md` -- Updated index linking to SLA, Runbook, and Security docs.
- `README.md` -- Updated technical documentation hub links to all enterprise documents.

## Tasks & Acceptance

**Execution:**
- [x] `backend/scripts/seed_properties.py` -- Implement `--reindex-vectors` flag to recalculate embeddings for existing properties.
- [x] `docs/performance-sla.md` -- Author enterprise SLA and performance benchmark documentation.
- [x] `docs/runbook.md` -- Author operations runbook covering PostgreSQL, PostGIS, Redis outage fallback, and vector disaster recovery.
- [x] `docs/security-privacy.md` -- Author enterprise security and privacy governance document.
- [x] `docs/project-overview.md` -- Update documentation index table and cross-references.
- [x] `README.md` -- Update documentation directory table with all 9 enterprise documents.

**Acceptance Criteria:**
- Given `docs/`, when inspected, then `performance-sla.md`, `runbook.md`, and `security-privacy.md` exist with complete, non-placeholder enterprise technical content without AI emojis.
- Given `README.md` and `docs/project-overview.md`, when inspected, then all links to enterprise docs resolve cleanly.
- Given `backend/scripts/seed_properties.py`, when run with `--help` or `--reindex-vectors`, then the CLI accepts the flag without errors.
- Given verification suites (`uv run pytest`, `npx tsc --noEmit`, `npm run build`), when run, then all pass 100% with 0 errors.

## Implementation Notes

- Added `reindex_all_vectors` function and `--reindex-vectors` CLI flag to `backend/scripts/seed_properties.py`.
- Authored `docs/performance-sla.md` defining SLA targets (Hybrid Search < 200ms P95, Vector ANN < 80ms P95, Redis hit < 15ms, CRUD < 50ms), monitoring profiling middleware, and k6 100 VUs load testing.
- Authored `docs/runbook.md` with PostgreSQL deadlock diagnosis, `REINDEX INDEX CONCURRENTLY` for GiST and HNSW, Redis outage graceful degradation & cache flushing, and vector recovery commands.
- Authored `docs/security-privacy.md` with password hashing (Bcrypt cost 12), JWT token architecture, phone number masking (`0912***678`), rate limiting tiers, and Decree 13/2023/ND-CP compliance.
- Updated documentation index in `README.md` and `docs/project-overview.md`.
- Executed verification: Backend pytest 101/101 PASS, Web Next.js 16 build 9/9 routes SUCCESS + TypeScript 0 errors, Flutter analyze 0 errors/warnings.

## Spec Change Log

## Review Triage Log

| Layer | Finding / Focus | Verdict | Evidence |
|---|---|---|---|
| Blind Hunter | Verification of Markdown formatting and cross-links | Pass | All 9 enterprise docs link properly without broken anchors or dead links. |
| Edge Case Hunter | Verification of AI emoji elimination and language consistency | Pass | 0 emojis found in performance-sla.md, runbook.md, and security-privacy.md. |
| Verification Gap | Verification of test suites and quality gates | Pass | Backend pytest 101/101 PASS, Web Next.js 16 build 9/9 routes SUCCESS + TypeScript 0 errors, Mobile Flutter analyze 0 errors/warnings. |

## Verification

**Commands:**
- `uv run pytest` in `backend` -- expected: 101 passed
- `npx tsc --noEmit` in `frontend/web` -- expected: 0 errors
- `npm run build` in `frontend/web` -- expected: 9/9 routes compiled successfully
