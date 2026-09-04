/**
 * Space247 - Shared DTOs and Type Definitions
 * Shared between Web (Next.js) and Mobile (React Native / Flutter)
 */

export type ListingType = "sale" | "rent";

export type PropertyType =
  | "apartment"
  | "house"
  | "villa"
  | "land"
  | "commercial";

export type PropertyStatus =
  | "active"
  | "pending"
  | "sold"
  | "rented"
  | "inactive";

export interface PropertyBase {
  title: string;
  description: string;
  property_type: PropertyType;
  listing_type: ListingType;
  price: number;
  currency?: string;
  area_sqm: number;
  num_bedrooms?: number | null;
  num_bathrooms?: number | null;
  address: string;
  ward?: string | null;
  district?: string | null;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface PropertyCreate extends PropertyBase {
  embedding?: number[] | null; // 768 dimensions
}

export interface PropertyUpdate extends Partial<PropertyBase> {
  status?: PropertyStatus;
  embedding?: number[] | null;
}

export interface PropertyResponse extends PropertyBase {
  id: string; // UUID
  status: PropertyStatus;
  created_at: string; // ISO 8601 string
  updated_at: string;
}

export interface SemanticSearchQuery {
  query_vector: number[]; // 768 dimensions
  listing_type?: ListingType;
  property_type?: PropertyType;
  address?: string;
  city?: string;
  district?: string;
  num_bedrooms?: number;
  min_bedrooms?: number;
  min_price?: number;
  max_price?: number;
  min_area_sqm?: number;
  max_area_sqm?: number;
  limit?: number;
  threshold?: number;
}

export interface PropertySearchQuery {
  query: string; // Natural language query text in Vietnamese or English
  listing_type?: ListingType;
  property_type?: PropertyType;
  address?: string;
  city?: string;
  district?: string;
  num_bedrooms?: number;
  min_bedrooms?: number;
  min_price?: number;
  max_price?: number;
  min_area_sqm?: number;
  max_area_sqm?: number;
  limit?: number;
  threshold?: number;
}

export interface SearchResultItem {
  property: PropertyResponse;
  similarity_score: number;
}

export interface SemanticSearchResponse {
  total: number;
  vector_dim: number;
  results: SearchResultItem[];
}

export interface PropertySearchResponse {
  total: number;
  vector_dim: number;
  query?: string | null;
  results: SearchResultItem[];
}

export interface HealthResponse {
  status: "healthy" | "unhealthy";
  database: "connected" | "disconnected";
  pgvector: "enabled" | "disabled";
  vector_dim: number;
  detail?: string;
}
