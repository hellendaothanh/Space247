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
  user_id?: string | null; // UUID of owner user
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
  /** Whether to execute hybrid search combining Vector Cosine Distance & Full-Text Search via RRF. Default: true */
  enable_hybrid?: boolean;
  /** Reciprocal Rank Fusion (RRF) smoothing constant k (default: 60). */
  rrf_k?: number;
}

export interface SearchResultItem {
  property: PropertyResponse;
  /** Cosine similarity score (1 - distance) between query vector and listing embedding. */
  similarity_score: number;
  /** Fused reciprocal rank score (1/(k + rank_v) + 1/(k + rank_f)). Present when hybrid search is active. */
  rrf_score?: number | null;
  /** 1-indexed rank position in dense vector similarity search candidates. */
  vector_rank?: number | null;
  /** 1-indexed rank position in full-text keyword search candidates. */
  fts_rank?: number | null;
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

// ---------------------------------------------------------------------------
// User & Authentication Types
// ---------------------------------------------------------------------------

export type UserRole = "user" | "agent" | "admin";

export interface UserBase {
  email: string;
  full_name: string;
  phone?: string | null;
  role?: UserRole;
}

export interface UserRegisterRequest extends UserBase {
  password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserResponse extends UserBase {
  id: string; // UUID
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface ToggleFavoriteResponse {
  property_id: string;
  is_favorite: boolean;
  message: string;
}

// ---------------------------------------------------------------------------
// Chat Assistant Types
// ---------------------------------------------------------------------------

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  role: ChatRole | string;
  content: string;
}

export interface ExtractedCriteria {
  listing_type?: ListingType | null;
  property_type?: PropertyType | null;
  city?: string | null;
  district?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  min_bedrooms?: number | null;
  amenities?: string[];
  raw_query?: string;
}

export interface ChatAssistantRequest {
  messages: ChatMessage[];
  limit?: number;
}

export interface ChatAssistantResponse {
  message: string;
  properties: PropertyResponse[];
  criteria?: ExtractedCriteria | null;
  suggestions: string[];
}

