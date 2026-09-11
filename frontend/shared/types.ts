/**
 * Space247 - Shared DTOs and Type Definitions
 * TypeScript DTOs consumed by the Web app (Next.js). The Flutter mobile app
 * uses its own Dart client (frontend/mobile/lib/core/api_client.dart).
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
  | "inactive"
  | "draft"
  | "hidden";

export type RentalType = "room" | "serviced_apartment" | "house_share" | "entire_house";
export interface RentalCosts {
  electricity_per_kwh?: number | null;
  electricity_billing?: "state_rate" | "fixed" | null;
  water_cost?: number | null;
  water_unit?: "per_m3" | "per_person" | null;

  parking_fee_monthly?: number | null;
  service_fee_monthly?: number | null;
  deposit_months?: number | null;
}
export interface RentalRules {
  curfew?: boolean | null;
  private_bathroom?: boolean | null;
  allow_pets?: boolean | null;
  has_mezzanine?: boolean | null;
  has_washing_machine?: boolean | null;
  live_with_owner?: boolean | null;
  has_elevator?: boolean | null;
  fingerprint_lock?: boolean | null;
  curfew_time?: string | null;
  max_occupants?: number | null;
}
export interface RentalFilters {
  rental_type?: RentalType;
  curfew?: boolean | null;
  private_bathroom?: boolean | null;
  allow_pets?: boolean;
  has_mezzanine?: boolean;
  has_washing_machine?: boolean;
  live_with_owner?: boolean;
  has_elevator?: boolean;
  fingerprint_lock?: boolean;
  electricity_billing?: "state_rate" | "fixed";
  max_deposit?: number;
  near_landmark?: string;
  radius_km?: number;
}

export interface PropertyBase {
  rental_type?: RentalType | null;
  rental_costs?: RentalCosts | null;
  rental_rules?: RentalRules | null;
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
  video_url?: string | null;
  virtual_tour_url?: string | null;
  project_id?: string | null;
}

export interface PropertyCreate extends PropertyBase {
  embedding?: number[] | null; // 768 dimensions
}

export interface PropertyUpdate extends Partial<PropertyBase> {
  status?: PropertyStatus;
  is_visible?: boolean;
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
  is_visible?: boolean;
  refreshed_at?: string;
  view_count?: number;
  images: string[];
  video_url?: string | null;
  virtual_tour_url?: string | null;
  agent?: PropertyAgent | null;
  project?: ProjectSummary | null;
  created_at: string; // ISO 8601 string
  updated_at: string;
}

export interface PropertyDetailResponse extends PropertyResponse {
  agent?: PropertyAgent | null;
}

export interface PropertySearchQuery extends RentalFilters {
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

export interface PropertySearchResponse {
  total: number;
  vector_dim: number;
  query?: string | null;
  results: SearchResultItem[];
}

// ---------------------------------------------------------------------------
// User & Authentication Types
// ---------------------------------------------------------------------------

export type UserRole = "superadmin" | "admin" | "agent" | "user";

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

export interface UserProfileUpdateRequest {
  full_name?: string;
  phone?: string | null;
  avatar_url?: string | null;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface UserResponse extends UserBase {
  id: string; // UUID
  role: UserRole;
  phone?: string | null;
  phone_number?: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  is_banned?: boolean;
  ban_reason?: string | null;
  phone_verified: boolean;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfileDetailResponse extends UserResponse {
  total_properties: number;
  total_favorites: number;
  total_alerts: number;
}

export type KycVerificationStatus = "pending" | "verified" | "rejected";

export interface KycDocumentGrant {
  url: string;
  expires_in: number;
}

export interface KycDocumentsResponse {
  status: KycVerificationStatus;
  masked_citizen_id: string;
  front: KycDocumentGrant;
  back: KycDocumentGrant;
  updated_at: string;
}

export interface UserCreateByAdminRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string | null;
  avatar_url?: string | null;
  role?: UserRole;
  is_active?: boolean;
  phone_verified?: boolean;
}

export interface UserUpdateByAdminRequest {
  full_name?: string;
  phone?: string | null;
  avatar_url?: string | null;
  role?: UserRole;
  is_active?: boolean;
  phone_verified?: boolean;
  reset_password?: string;
}

export interface UserPaginationResponse {
  items: UserResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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

export interface ExtractedCriteria extends RentalFilters {
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

export interface LivingCostItem {
  category: string;
  unit_price: number;
  quantity: number;
  unit_label: string;
  subtotal: number;
  note?: string | null;
}

export interface LivingCostBreakdown {
  room_price: number;
  occupants: number;
  electricity_kwh: number;
  water_usage: number;
  water_unit: string;
  items: LivingCostItem[];
  total_monthly_cost: number;
  cost_per_person: number;
  summary: string;
}

export interface ChatAssistantResponse {
  message: string;
  properties: PropertyResponse[];
  criteria?: ExtractedCriteria | null;
  suggestions: string[];
  living_cost?: LivingCostBreakdown | null;
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

// ---------------------------------------------------------------------------
// Real Estate Project Types
// ---------------------------------------------------------------------------

export type ProjectStatus =
  | "upcoming"
  | "under_construction"
  | "handing_over"
  | "completed";

export interface ProjectBase {
  name: string;
  slug: string;
  developer?: string | null;
  description?: string | null;
  status: ProjectStatus;
  total_units?: number | null;
  launch_year?: number | null;
  handover_year?: number | null;
  address: string;
  ward?: string | null;
  district?: string | null;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
  images?: string[];
  video_url?: string | null;
  virtual_tour_url?: string | null;
  master_plan_url?: string | null;
  legal_status?: string | null;
  price_range_min?: number | null;
  price_range_max?: number | null;
  amenities?: string[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  developer?: string | null;
  status: ProjectStatus;
  city: string;
  district?: string | null;
  images: string[];
  video_url?: string | null;
  virtual_tour_url?: string | null;
  price_range_min?: number | null;
  price_range_max?: number | null;
}

export interface ProjectResponse extends ProjectBase {
  id: string;
  created_at: string;
  updated_at: string;
  active_properties_count: number;
  for_sale_count: number;
  for_rent_count: number;
  average_price_per_sqm?: number | null;
}

export interface ProjectDetailResponse extends ProjectResponse {}

export interface PaginatedProjectResponse {
  items: ProjectResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProjectFilterQuery {
  skip?: number;
  limit?: number;
  city?: string;
  district?: string;
  status?: ProjectStatus;
  developer?: string;
  min_price?: number;
  max_price?: number;
  q?: string;
}

// -------------------------------------------------------------
// Two-Sided Rental System (Host & Tenant Platform)
// -------------------------------------------------------------
export type RentalPropertyModel = "boarding_house" | "serviced_apartment" | "homestay";
export type RentalUnitStatus = "available" | "occupied" | "reserved";
export type RentalUnitFurnishing = "empty" | "basic" | "full";
export type RentalInquiryType = "view_appointment" | "booking_request";
export type RentalInquiryStatus = "pending" | "confirmed" | "rejected" | "completed";

export type RoomAmenity = "ac_inverter" | "fridge" | "water_heater" | "bed_mattress" | "study_desk" | "wardrobe" | "balcony" | "washing_machine" | "kitchen";
export interface SurroundingPlace { label: string; category: string; distance_meters?: number | null; walk_minutes?: number | null; note?: string | null; }
export interface CostLineItem { key: string; label: string; amount: number; note?: string | null; }
export interface MonthlyCostEstimate { property_id?: string | null; unit_id?: string | null; unit_number: string; occupants: number; currency: "VND"; electricity: { ac_kwh: number; fridge_kwh: number; general_kwh: number; total_kwh: number; unit_price: number }; fixed_costs: CostLineItem[]; variable_costs: CostLineItem[]; estimated_total_monthly: number; per_person_monthly: number; }

export interface RentalUnit {
  id: string;
  property_id: string;
  unit_number: string;
  floor?: number | null;
  area_sqm: number;
  price: number;
  deposit?: number | null;
  status: RentalUnitStatus;
  furnishing: RentalUnitFurnishing;
  has_mezzanine: boolean;
  has_private_bathroom: boolean;
  max_occupants?: number | null;
  images: string[];
  floor_plan_url?: string | null;
  room_amenities: RoomAmenity[];
  created_at: string;
  updated_at: string;
}

export interface AdminUserListItem extends UserResponse {
  kyc_status?: KycVerificationStatus | null;
}

export interface AdminUserDetail extends AdminUserListItem {
  total_properties: number;
  total_favorites: number;
  total_alerts: number;
  properties: Array<{ id: string; title: string; status: string; price: number }>;
  deposit_transactions: Array<{ id: string; amount: number; status: string; reference_code: string; created_at: string }>;
}

export interface UpdateUserRolePayload { role: UserRole; }
export interface ToggleUserStatusPayload { is_banned: boolean; reason?: string; }
export interface KYCReviewPayload { action: "approve" | "reject"; reason?: string; }
export interface AdminUserStats { total_users: number; agents: number; banned_users: number; pending_kyc: number; }

export interface PendingKycUser {
  user_id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  status: KycVerificationStatus;
  masked_citizen_id: string;
  created_at: string;
  updated_at: string;
}

export type RentalUnitDetail = RentalUnit;

export interface RentalUnitCreate {
  unit_number: string;
  floor?: number | null;
  area_sqm: number;
  price: number;
  deposit?: number | null;
  status?: RentalUnitStatus;
  furnishing?: RentalUnitFurnishing;
  has_mezzanine?: boolean;
  has_private_bathroom?: boolean;
  max_occupants?: number | null;
  images?: string[];
  floor_plan_url?: string | null;
  room_amenities?: RoomAmenity[];
}

export interface RentalPropertyHostSummary {
  id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  avatar_url?: string | null;
}

export interface RentalProperty {
  id: string;
  host_id: string;
  host?: RentalPropertyHostSummary | null;
  name: string;
  description: string;
  property_model: RentalPropertyModel;
  address: string;
  ward?: string | null;
  district?: string | null;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
  shared_costs?: Record<string, any>;
  shared_rules?: Record<string, any>;
  images: string[];
  video_url?: string | null;
  surroundings: SurroundingPlace[];
  security_features: string[];
  is_active: boolean;
  total_units_count: number;
  available_units_count: number;
  min_price?: number | null;
  max_price?: number | null;
  units: RentalUnit[];
  created_at: string;
  updated_at: string;
}

export interface RentalPropertyCreate {
  name: string;
  description?: string;
  property_model?: RentalPropertyModel;
  address: string;
  ward?: string | null;
  district?: string | null;
  city: string;
  latitude?: number | null;
  longitude?: number | null;
  shared_costs?: Record<string, any>;
  shared_rules?: Record<string, any>;
  images?: string[];
  video_url?: string | null;
  surroundings?: SurroundingPlace[];
  security_features?: string[];
  is_active?: boolean;
  initial_units?: RentalUnitCreate[];
}

export interface RentalInquiry {
  id: string;
  unit_id: string;
  tenant_id: string;
  host_id: string;
  inquiry_type: RentalInquiryType;
  scheduled_time?: string | null;
  appointment_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  google_calendar_url?: string | null;
  calendar_event_uid?: string | null;
  reminder_status?: "pending" | "sent" | "failed";
  tenant_name?: string | null;
  tenant_phone?: string | null;
  message?: string | null;
  status: RentalInquiryStatus;
  created_at: string;
  updated_at: string;
  unit?: RentalUnit | null;
}

export interface RentalInquiryCreate {
  inquiry_type?: RentalInquiryType;
  scheduled_time?: string | null;
  tenant_name?: string | null;
  tenant_phone?: string | null;
  message?: string | null;
}

export interface HostDashboardStats {
  total_properties: number;
  total_units: number;
  available_units: number;
  occupied_units: number;
  reserved_units: number;
  occupancy_rate: number;
  estimated_monthly_revenue: number;
  pending_inquiries_count: number;
  unpaid_invoices_count: number;
}

export interface LandlordDashboardStats extends HostDashboardStats {}

export interface RentalContract {
  id: string;
  unit_id: string;
  property_id: string;
  host_id: string;
  tenant_id: string;
  tenant_name: string;
  tenant_phone: string;
  start_date: string;
  end_date?: string | null;
  rental_price: number;
  deposit_amount: number;
  payment_cycle_months: number;
  electricity_rate: number;
  water_rate: number;
  water_billing_type: string;
  service_fee: number;
  status: "active" | "expired" | "terminated";
  created_at: string;
  updated_at: string;
  unit?: RentalUnit | null;
}

export interface MeterReadingInput {
  contract_id: string;
  electricity_previous: number;
  electricity_current: number;
  water_previous?: number | null;
  water_current?: number | null;
  notes?: string | null;
}

export interface GenerateInvoicesRequest {
  billing_month: string;
  readings: MeterReadingInput[];
  due_days?: number;
}

export interface MonthlyInvoice {
  id: string;
  contract_id: string;
  unit_id: string;
  host_id: string;
  tenant_id: string;
  billing_month: string;
  room_amount: number;
  electricity_previous_index: number;
  electricity_current_index: number;
  electricity_rate: number;
  electricity_amount: number;
  water_previous_index?: number | null;
  water_current_index?: number | null;
  water_rate: number;
  water_amount: number;
  service_amount: number;
  other_amount: number;
  total_amount: number;
  status: "pending" | "paid" | "overdue" | "cancelled";
  due_date: string;
  paid_at?: string | null;
  notes?: string | null;
  last_reminded_at?: string | null;
  created_at: string;
  updated_at: string;
  unit?: RentalUnit | null;
  contract?: RentalContract | null;
}

export interface DebtReminderResponse {
  invoice_id: string;
  tenant_id: string;
  tenant_name?: string | null;
  tenant_phone?: string | null;
  amount_due: number;
  notification_sent: boolean;
  message: string;
}

export interface DepositTransaction {
  id: string;
  unit_id: string;
  inquiry_id?: string | null;
  tenant_id: string;
  host_id: string;
  amount: number;
  reference_code: string;
  payment_method: string;
  vietqr_url: string;
  status: "pending" | "success" | "expired" | "failed";
  expires_at: string;
  paid_at?: string | null;
  created_at: string;
}

export interface RentalSearchFilterQuery {
  skip?: number;
  limit?: number;
  query?: string;
  property_model?: RentalPropertyModel;
  city?: string;
  district?: string;
  min_price?: number;
  max_price?: number;
  furnishing?: RentalUnitFurnishing;
  has_mezzanine?: boolean;
  has_private_bathroom?: boolean;
  allow_pets?: boolean;
  fingerprint_lock?: boolean;
  curfew?: boolean;
  only_available?: boolean;
}

export interface ViewingScheduleWindow {
  weekday: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  is_active: boolean;
}

export interface ViewingSlot {
  date: string;
  start_time: string;
  end_time: string;
}

export interface ViewingBookingRequest {
  date: string;
  start_time: string;
  tenant_name?: string;
  tenant_phone?: string;
  message?: string;
}

export interface CuratedCollection {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  tag: string;
  icon: string;
  cover_image?: string;
  item_count?: number;
  properties: PropertyResponse[];
}

export interface CollectionsResponse {
  collections: CuratedCollection[];
}

export interface CityMarketStats {
  city: string;
  short_name: string;
  avg_price_per_sqm: number;
  min_price_per_sqm: number;
  max_price_per_sqm: number;
  total_listings: number;
  change_pct: number;
  trending_district: string;
}

export interface HotArea {
  district: string;
  city: string;
  search_volume_score: number;
  avg_price_million: number;
  highlight: string;
}

export interface MarketPulseResponse {
  cities: CityMarketStats[];
  hot_areas: HotArea[];
  national_avg_sqm: number;
  updated_at: string;
}

export interface NewsCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  icon?: string | null;
  display_order: number;
  article_count: number;
}

export interface ArticleAuthor {
  id: string;
  full_name?: string | null;
  email: string;
  avatar_url?: string | null;
}

export interface ArticleListItem {
  id: string;
  title: string;
  slug: string;
  summary: string;
  thumbnail_url?: string | null;
  category_id: string;
  category?: NewsCategory | null;
  author_id?: string | null;
  author?: ArticleAuthor | null;
  tags: string[];
  view_count: number;
  is_published: boolean;
  published_at?: string | null;
  created_at: string;
}

export interface ArticleDetail extends ArticleListItem {
  content: string;
  related_articles: ArticleListItem[];
}

export interface CreateArticlePayload {
  title: string;
  slug?: string | null;
  summary: string;
  content: string;
  thumbnail_url?: string | null;
  category_id: string;
  tags?: string[];
  is_published?: boolean;
}

export interface ArticlePaginationResponse {
  items: ArticleListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MyListingItem {
  id: string;
  title: string;
  description: string;
  property_type: PropertyType | string;
  listing_type: ListingType | string;
  rental_type?: RentalType | string | null;
  price: number;
  currency: string;
  area_sqm: number;
  num_bedrooms?: number | null;
  num_bathrooms?: number | null;
  address: string;
  ward?: string | null;
  district?: string | null;
  city: string;
  images: string[];
  status: PropertyStatus | string;
  is_visible: boolean;
  refreshed_at: string;
  view_count: number;
  favorites_count: number;
  created_at: string;
  updated_at: string;
}

export interface MyListingsStats {
  total_listings: number;
  active_listings: number;
  sold_or_rented_count: number;
  hidden_listings: number;
  total_views: number;
  total_favorites: number;
}

export interface MyListingsResponse {
  items: MyListingItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  stats: MyListingsStats;
}

export interface UpdateListingStatusPayload {
  status?: string;
  is_visible?: boolean;
}



