# Space247 - Frontend Architecture

Decoupled multi-platform frontend architecture serving Web and Mobile clients with unified backend API contracts.

## Directory Structure

```
frontend/
├── web/                  # Next.js 14+ App Router (Desktop & Mobile Web)
│   ├── app/              # SSR pages, dynamic routes, SEO metadata
│   ├── components/       # UI components (property cards, search bars, map)
│   └── public/           # Static assets, icons, fonts
│
├── mobile/               # Cross-Platform Mobile Client (React Native / Flutter)
│   ├── src/screens/      # Screen views (Explore, Saved, Search, Details)
│   ├── src/navigation/   # Stack & tab navigators
│   └── src/components/   # Native-optimized gesture and map components
│
├── shared/               # Universal DTOs, API Client, and Domain Constants
│   ├── types.ts          # TypeScript schemas mirroring backend Pydantic DTOs
│   ├── api-client.ts     # Universal fetch-based API client for REST endpoints
│   └── constants.ts      # Enums, filter limits, vector dimensions (768)
│
└── README.md             # Multi-platform architecture and integration guide
```

## Architectural Principles

1. **Decoupled Client Boundaries:**
   - Web (`frontend/web`) and Mobile (`frontend/mobile`) maintain independent rendering pipelines, build configurations, and navigation paradigms.
   - The backend API never couples directly to client-specific UI logic.

2. **Single Source of Truth Contracts (`frontend/shared/`):**
   - Domain types, DTO contracts, and API client routines reside in `shared/` to eliminate drift between Web and Mobile clients.
   - All client network requests flow through `RealEstateApiClient`.

3. **Rendering & SEO Strategy:**
   - **Web (Next.js App Router):** Server-Side Rendering (SSR) and Incremental Static Regeneration (ISR) for property detail pages (`/properties/[id]`) to optimize search engine indexing (Google, Bing) and social preview meta tags.
   - **Mobile (React Native / Flutter):** Client-side rendering optimized for high-FPS interactive gestures, smooth map clustering, and offline caching of saved listings.

4. **Data Fetching & Cache Synchronization:**
   - Client applications use TanStack Query (React Query) for query caching, deduplication, and optimistic updates.
   - Semantic vector search results are cached using query vector hashes to minimize redundant embedding calculations.

## Usage Example

```typescript
import { RealEstateApiClient } from "../shared/api-client";

const client = new RealEstateApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

// Semantic Vector Search
const searchResults = await client.searchSemantic({
  query_vector: embedding768Array,
  listing_type: "sale",
  city: "Hồ Chí Minh",
  limit: 10,
});
```
