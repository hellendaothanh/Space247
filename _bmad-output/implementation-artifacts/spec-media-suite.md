---
title: 'Implement Space247 Media Suite'
type: 'feature'
created: '2026-09-08'
status: 'done'
route: 'dispatch'
baseline_commit: '00a844e'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Implement a cross-platform Media Suite for Space247. Add nullable `video_url` and `virtual_tour_url` columns to `properties` and `projects` in Alembic revision 0012 while retaining `images` as `TEXT[]`. Add safe YouTube, YouTube Shorts, and TikTok video parsing, schemas, SDK types, seeded media, responsive web media tabs/mosaic/lightbox/video embeds, creation/edit video fields and multi-image previews, plus Flutter image/video media support.

## Constraints

- Parse only recognized public YouTube or TikTok URLs into safe embeds; retain unknown values without embedding them.
- Preserve image fallbacks and existing property/project API compatibility.
- Use responsive 16:9 YouTube and 9:16 Shorts/TikTok presentation.
- Verify backend pytest and Web TypeScript/production build.

</frozen-after-approval>

## Code Map

- `backend/migrations/versions` -- migration 0012.
- `backend/src/models`, `schemas`, and seed scripts -- persistence, DTOs, parser, and sample media.
- `frontend/shared` -- media DTOs and embed helper.
- `frontend/web/src/app/properties`, `projects`, and `components` -- media tabs, gallery, video players, forms.
- `frontend/mobile` -- model and detail media rendering.

## Tasks & Acceptance

- [x] Add migration, models, schemas, parser, seed media, and backend tests.
- [x] Add shared media interfaces and safe embed helper.
- [x] Add Web media tabs, gallery/video views, and property form media controls.
- [x] Add Flutter media carousel/video support.
- [x] Run backend and Web quality gates.

## Implementation Notes

- `uv run pytest`: 174 passed.
- `npx tsc --noEmit`, `npm run build`, and `flutter analyze`: passed.
- Review fixes: media tab fallback, mobile tour allow-list, migration DDL coverage, image fallback, and project API media serialization were applied; nothing was deferred.
