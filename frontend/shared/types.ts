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
  images?: string[];
}

export interface PropertyCreate extends PropertyBase {
  embedding?: number[] | null; // 768 dimensions
}

export interface PropertyUpdate extends Partial<PropertyBase> {
  status?: PropertyStatus;
  embedding?: number[] | null;
}

export interface PropertyAgent {
  id: string; // UUID
  full_name: string;
  email: string;
  phone_number?: string | null;
  phone?: string | null;
  avatar_url?: string | null;
  role: string;
}

export interface PropertyResponse extends PropertyBase {
  id: string; // UUID
  user_id?: string | null; // UUID of owner user
  status: PropertyStatus;
  images: string[];
  agent?: PropertyAgent | null;
  created_at: string; // ISO 8601 string
  updated_at: string;
}

export interface PropertyDetailResponse extends PropertyResponse {
  agent?: PropertyAgent | null;
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

export interface UserUpdate {
  full_name?: string;
  phone?: string | null;
  phone_number?: string | null;
  avatar_url?: string | null;
}

export interface UserResponse extends UserBase {
  id: string; // UUID
  role: UserRole;
  phone_number?: string | null;
  avatar_url?: string | null;
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

export interface ComparePropertiesRequest {
  property_ids: string[];
}

export interface ComparisonData {
  property_id: string;
  title: string;
  price: number;
  area_sqm: number;
  price_per_sqm: number;
}

export interface ComparePropertiesResponse {
  properties: ComparisonData[];
  analysis_markdown: string;
}

// ---------------------------------------------------------------------------
// Spatial & Geo-Intelligence Types
// ---------------------------------------------------------------------------

export type TransportMode = "motorcycle" | "car" | "transit" | "walking";
export type AmenityCategory = "school" | "hospital" | "metro" | "supermarket" | "all";

export interface TargetLocationInfo {
  name: string;
  latitude: number;
  longitude: number;
  formatted_address?: string | null;
}

export interface IsochroneSearchRequest {
  target_landmark: string;
  max_duration_minutes?: number;
  transport_mode?: TransportMode;
  property_type?: PropertyType | null;
  listing_type?: ListingType | null;
  min_price?: number | null;
  max_price?: number | null;
  min_bedrooms?: number | null;
  limit?: number;
}

export interface IsochronePropertyItem {
  property: PropertyResponse;
  estimated_travel_minutes: number;
  distance_km: number;
}

export interface IsochroneSearchResponse {
  target_location: TargetLocationInfo;
  max_duration_minutes: number;
  transport_mode: TransportMode;
  isochrone_geojson: any; // GeoJSON FeatureCollection
  total: number;
  properties: IsochronePropertyItem[];
}

export interface AmenityPOI {
  id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  weight: number;
  distance_meters?: number | null;
  address?: string | null;
}

export interface AmenityHeatmapQuery {
  category?: AmenityCategory | string;
  min_lat?: number;
  min_lng?: number;
  max_lat?: number;
  max_lng?: number;
  center_lat?: number;
  center_lng?: number;
  radius_km?: number;
}

export interface AmenityHeatmapResponse {
  category: string;
  total_points: number;
  heatmap_points: [number, number, number][]; // [lat, lng, weight]
  pois: AmenityPOI[];
}

// ---------------------------------------------------------------------------
// Agent AI Co-Pilot Types
// ---------------------------------------------------------------------------

export interface ExtractedSpecs {
  area_sqm?: number | null;
  num_bedrooms?: number | null;
  num_bathrooms?: number | null;
  orientation?: string | null;
  legal_status?: string | null;
  frontage_meters?: number | null;
  suggested_price?: number | null;
  amenities: string[];
}

export interface GenerateListingRequest {
  text_prompts: string[] | string;
  image_base64?: string | null;
  property_type?: string;
  target_audience?: string | null;
}

export interface GenerateListingResponse {
  title_seo: string;
  description_markdown: string;
  extracted_specs: ExtractedSpecs;
}

export interface ValuationRequest {
  property_type?: string;
  area_sqm: number;
  num_bedrooms?: number | null;
  num_bathrooms?: number | null;
  latitude: number;
  longitude: number;
  radius_km?: number;
  user_proposed_price?: number | null;
}

export interface ComparableProperty {
  id: string;
  title: string;
  price: number;
  area_sqm: number;
  price_per_sqm: number;
  distance_km: number;
  address: string;
  property_type: string;
}

export interface ValuationResponse {
  estimated_price_per_sqm: number;
  estimated_total_price: number;
  price_range_low: number;
  price_range_high: number;
  confidence_score: number;
  market_trend: "up" | "stable" | "down";
  radius_used_km: number;
  comparable_properties: ComparableProperty[];
  deviation_percentage?: number | null;
  pricing_advice?: string | null;
}

// ---------------------------------------------------------------------------
// Retention & Financial Tools Types
// ---------------------------------------------------------------------------

export interface SavedSearchAlert {
  id: string;
  user_id: string;
  title: string;
  criteria: Record<string, any>;
  frequency: "instant" | "daily" | "weekly" | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_notified_at?: string | null;
}

export interface CreateAlertRequest {
  title: string;
  criteria: Record<string, any>;
  frequency?: "instant" | "daily" | "weekly" | string;
}

export interface UpdateAlertRequest {
  title?: string;
  criteria?: Record<string, any>;
  frequency?: "instant" | "daily" | "weekly" | string;
  is_active?: boolean;
}

export interface UserNotification {
  id: string;
  user_id: string;
  alert_id?: string | null;
  property_id?: string | null;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  property?: PropertyResponse | null;
}

export interface NotificationListResponse {
  items: UserNotification[];
  total: number;
  unread_count: number;
}

export interface MortgageCalcRequest {
  property_price: number;
  down_payment_percent?: number;
  down_payment_amount?: number;
  loan_term_years: number;
  annual_interest_rate?: number;
  preferential_period_months?: number;
  post_preferential_rate?: number;
  calculation_method?: "declining_balance" | "fixed_payment";
}

export interface AmortizationScheduleItem {
  month: number;
  principal_payment: number;
  interest_payment: number;
  total_payment: number;
  remaining_balance: number;
  interest_rate: number;
}

export interface MortgageCalcResponse {
  property_price: number;
  down_payment_amount: number;
  down_payment_percent: number;
  loan_amount: number;
  loan_term_years: number;
  loan_term_months: number;
  calculation_method: string;
  monthly_payment_first_month: number;
  monthly_payment_max: number;
  monthly_payment_min: number;
  total_interest: number;
  total_payment: number;
  schedule: AmortizationScheduleItem[];
}

