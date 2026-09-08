---
title: 'Polish Space247 Commercial UX'
type: 'feature'
created: '2026-09-08'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The home search hero and footer expose implementation terminology that distracts from Space247's commercial real-estate experience.

**Approach:** Replace the prescribed hero copy and AI-search control label, then rebuild the footer as a responsive four-column commercial information area with the requested Vietnamese content and a 2026 copyright bar.

</frozen-after-approval>

## Implementation Notes

- Replaced technical home-search and metadata copy with the requested customer-facing Vietnamese messaging.
- Applied the requested search placeholder to the Flutter mobile header to keep search language consistent across platforms.
- Rebuilt the site-wide footer into a responsive brand and four-column commercial information layout; unavailable policy and utility destinations remain non-interactive until their pages exist.
- Removed remaining customer-visible vector terminology from property creation, editing, and deletion feedback.

## Review Triage Log

- deferred: Footer policy, mortgage, and comparison destinations have no standalone routes; creating these content and interaction flows is outside the approved commercial-polish scope.
- patched: Removed the incorrect home-page link for AI comparison and retained it as non-interactive content until a dedicated flow exists.
- patched: Replaced remaining customer-visible vector terminology in property creation, editing, and deletion feedback.
