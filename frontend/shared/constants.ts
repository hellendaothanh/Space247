/**
 * Space247 - Shared Constants and Enums
 * Used across Web and Mobile frontends
 */

export const VECTOR_DIM = 768;

export const DEFAULT_PAGE_LIMIT = 10;
export const MAX_PAGE_LIMIT = 100;

export const PROPERTY_TYPES = [
  "apartment",
  "house",
  "villa",
  "land",
  "commercial",
] as const;

export const LISTING_TYPES = ["sale", "rent"] as const;

export const PROPERTY_STATUSES = [
  "active",
  "pending",
  "sold",
  "rented",
  "inactive",
] as const;
