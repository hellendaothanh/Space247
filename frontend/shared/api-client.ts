/**
 * Space247 - Shared API Client
 * Compatible with Next.js (Web) and React Native / Mobile
 */

import {
  AuthTokenResponse,
  ChatAssistantRequest,
  ChatAssistantResponse,
  HealthResponse,
  ListingType,
  PropertyCreate,
  PropertyDetailResponse,
  PropertyResponse,
  PropertySearchQuery,
  PropertySearchResponse,
  PropertyStatus,
  PropertyType,
  PropertyUpdate,
  SemanticSearchQuery,
  SemanticSearchResponse,
  ToggleFavoriteResponse,
  UserLoginRequest,
  UserRegisterRequest,
  UserResponse,
  UserUpdate,
  ComparePropertiesRequest,
  ComparePropertiesResponse,
  IsochroneSearchRequest,
  IsochroneSearchResponse,
  AmenityHeatmapQuery,
  AmenityHeatmapResponse,
  GenerateListingRequest,
  GenerateListingResponse,
  ValuationRequest,
  ValuationResponse,
  SavedSearchAlert,
  CreateAlertRequest,
  UpdateAlertRequest,
  UserNotification,
  NotificationListResponse,
  MortgageCalcRequest,
  MortgageCalcResponse,
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  ProjectDetailResponse,
  PaginatedProjectResponse,
  ProjectFilterQuery,
  UserProfileUpdateRequest,
  ChangePasswordRequest,
  UserProfileDetailResponse,
  UserCreateByAdminRequest,
  UserUpdateByAdminRequest,
  UserAdminDetailResponse,
  UserPaginationResponse,
} from "./types";


export interface ApiClientConfig {
  baseUrl: string;
  timeoutMs?: number;
  getAuthToken?: () => Promise<string | null> | string | null;
}

export class RealEstateApiClient {
  private baseUrl: string;
  private timeoutMs: number;
  private getAuthToken?: () => Promise<string | null> | string | null;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "").replace(/\/api\/v1\/?$/, "");
    this.timeoutMs = config.timeoutMs ?? 15000;
    this.getAuthToken = config.getAuthToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.getAuthToken) {
      const token = await this.getAuthToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        let detailMsg = response.statusText;
        if (typeof errorData.detail === "string") {
          detailMsg = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          detailMsg = errorData.detail
            .map((err: any) => `${err.loc ? err.loc.join(".") + ": " : ""}${err.msg || "Invalid"}`)
            .join("; ");
        } else if (typeof errorData.detail === "object") {
          detailMsg = JSON.stringify(errorData.detail);
        }

        throw new Error(`API Error [${response.status}]: ${detailMsg}`);
      }

      if (response.status === 204) {
        return null as unknown as T;
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === "AbortError") {
        throw new Error(`Yêu cầu mạng hết thời gian chờ (${this.timeoutMs}ms) tới ${url}`);
      }
      if (err.message === "Failed to fetch" || err.name === "TypeError") {
        throw new Error(
          `Không thể kết nối đến máy chủ Space247 API tại ${this.baseUrl}. Vui lòng kiểm tra backend server đã được khởi động chưa (ví dụ: 'uv run uvicorn src.main:app --host 0.0.0.0 --port 8080').`
        );
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Authentication
  async register(data: UserRegisterRequest): Promise<AuthTokenResponse> {
    return this.request<AuthTokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(data: UserLoginRequest): Promise<AuthTokenResponse> {
    return this.request<AuthTokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser(): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/me");
  }

  async updateCurrentUser(data: UserUpdate): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // User Profile Self-Management
  async getMyProfile(): Promise<UserProfileDetailResponse> {
    return this.request<UserProfileDetailResponse>("/api/v1/users/me");
  }

  async updateMyProfile(data: UserProfileUpdateRequest): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/users/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async changeMyPassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>("/api/v1/users/me/change-password", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Superadmin User Management
  async getAdminUsers(params?: {
    q?: string;
    role?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<UserPaginationResponse> {
    const searchParams = new URLSearchParams();
    if (params?.q) searchParams.append("q", params.q);
    if (params?.role) searchParams.append("role", params.role);
    if (params?.is_active !== undefined) searchParams.append("is_active", String(params.is_active));
    if (params?.page) searchParams.append("page", String(params.page));
    if (params?.page_size) searchParams.append("page_size", String(params.page_size));

    const qs = searchParams.toString();
    return this.request<UserPaginationResponse>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
  }

  async createAdminUser(data: UserCreateByAdminRequest): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/admin/users", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAdminUserDetail(userId: string): Promise<UserAdminDetailResponse> {
    return this.request<UserAdminDetailResponse>(`/api/v1/admin/users/${userId}`);
  }

  async updateAdminUser(userId: string, data: UserUpdateByAdminRequest): Promise<UserResponse> {
    return this.request<UserResponse>(`/api/v1/admin/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteAdminUser(userId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/admin/users/${userId}`, {
      method: "DELETE",
    });
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/api/v1/health");
  }

  // Properties CRUD
  async createProperty(data: PropertyCreate): Promise<PropertyResponse> {
    return this.request<PropertyResponse>("/api/v1/properties", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listProperties(params?: {
    skip?: number;
    limit?: number;
    listing_type?: ListingType;
    property_type?: PropertyType;
    city?: string;
    status?: PropertyStatus;
  }): Promise<PropertyResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set("skip", String(params.skip));
    if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
    if (params?.listing_type) searchParams.set("listing_type", params.listing_type);
    if (params?.property_type) searchParams.set("property_type", params.property_type);
    if (params?.city) searchParams.set("city", params.city);
    if (params?.status) searchParams.set("status", params.status);

    const queryStr = searchParams.toString();
    const endpoint = `/api/v1/properties${queryStr ? `?${queryStr}` : ""}`;
    return this.request<PropertyResponse[]>(endpoint);
  }

  async getMyProperties(params?: {
    skip?: number;
    limit?: number;
    status?: PropertyStatus;
  }): Promise<PropertyResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set("skip", String(params.skip));
    if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
    if (params?.status) searchParams.set("status", params.status);

    const queryStr = searchParams.toString();
    const endpoint = `/api/v1/properties/my${queryStr ? `?${queryStr}` : ""}`;
    return this.request<PropertyResponse[]>(endpoint);
  }

  async listFavorites(params?: {
    skip?: number;
    limit?: number;
  }): Promise<PropertyResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set("skip", String(params.skip));
    if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));

    const queryStr = searchParams.toString();
    const endpoint = `/api/v1/properties/favorites${queryStr ? `?${queryStr}` : ""}`;
    return this.request<PropertyResponse[]>(endpoint);
  }

  async toggleFavorite(propertyId: string): Promise<ToggleFavoriteResponse> {
    return this.request<ToggleFavoriteResponse>(
      `/api/v1/properties/${encodeURIComponent(propertyId)}/favorite`,
      { method: "POST" }
    );
  }

  async getProperty(id: string): Promise<PropertyDetailResponse> {
    return this.request<PropertyDetailResponse>(`/api/v1/properties/${encodeURIComponent(id)}`);
  }

  async updateProperty(
    id: string,
    data: PropertyUpdate
  ): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProperty(id: string): Promise<void> {
    return this.request<void>(`/api/v1/properties/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  }

  // Natural Language Property Search
  async searchProperties(
    query: PropertySearchQuery
  ): Promise<PropertySearchResponse> {
    return this.request<PropertySearchResponse>("/api/v1/properties/search", {
      method: "POST",
      body: JSON.stringify(query),
    });
  }

  // Semantic Vector Search
  async searchSemantic(
    query: SemanticSearchQuery
  ): Promise<SemanticSearchResponse> {
    return this.request<SemanticSearchResponse>("/api/v1/search/semantic", {
      method: "POST",
      body: JSON.stringify(query),
    });
  }

  // AI Chatbot Assistant
  async chatAssistant(
    request: ChatAssistantRequest
  ): Promise<ChatAssistantResponse> {
    return this.request<ChatAssistantResponse>("/api/v1/chat/assistant", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // AI Property Comparison
  async compareProperties(
    request: ComparePropertiesRequest
  ): Promise<ComparePropertiesResponse> {
    return this.request<ComparePropertiesResponse>("/api/v1/properties/compare", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Spatial & Geo-Intelligence: Isochrone Travel-Time Search
  async isochroneSearch(
    request: IsochroneSearchRequest
  ): Promise<IsochroneSearchResponse> {
    return this.request<IsochroneSearchResponse>("/api/v1/spatial/isochrone-search", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Spatial & Geo-Intelligence: Amenity Density Heatmap
  async getAmenityHeatmap(
    params?: AmenityHeatmapQuery
  ): Promise<AmenityHeatmapResponse> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append("category", params.category);
    if (params?.min_lat !== undefined) searchParams.append("min_lat", params.min_lat.toString());
    if (params?.min_lng !== undefined) searchParams.append("min_lng", params.min_lng.toString());
    if (params?.max_lat !== undefined) searchParams.append("max_lat", params.max_lat.toString());
    if (params?.max_lng !== undefined) searchParams.append("max_lng", params.max_lng.toString());
    if (params?.center_lat !== undefined) searchParams.append("center_lat", params.center_lat.toString());
    if (params?.center_lng !== undefined) searchParams.append("center_lng", params.center_lng.toString());
    if (params?.radius_km !== undefined) searchParams.append("radius_km", params.radius_km.toString());

    const qs = searchParams.toString();
    return this.request<AmenityHeatmapResponse>(
      `/api/v1/spatial/amenities/heatmap${qs ? `?${qs}` : ""}`
    );
  }

  // Agent AI Co-Pilot: AI Listing Generator
  async generateAgentListing(
    request: GenerateListingRequest
  ): Promise<GenerateListingResponse> {
    return this.request<GenerateListingResponse>("/api/v1/agent/listing/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Agent AI Co-Pilot: Smart AVM Pricing Advisor
  async estimatePropertyValuation(
    request: ValuationRequest
  ): Promise<ValuationResponse> {
    return this.request<ValuationResponse>("/api/v1/agent/valuation/estimate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // ---------------------------------------------------------------------------
  // Retention & Financial Tools Methods
  // ---------------------------------------------------------------------------

  // Mortgage & Loan Financial Calculator (Public API)
  async calculateMortgage(
    request: MortgageCalcRequest
  ): Promise<MortgageCalcResponse> {
    return this.request<MortgageCalcResponse>("/api/v1/financial/mortgage-calc", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Saved Search Alerts
  async getAlerts(): Promise<SavedSearchAlert[]> {
    return this.request<SavedSearchAlert[]>("/api/v1/alerts", {
      method: "GET",
    });
  }

  async createAlert(
    request: CreateAlertRequest
  ): Promise<SavedSearchAlert> {
    return this.request<SavedSearchAlert>("/api/v1/alerts", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getAlert(id: string): Promise<SavedSearchAlert> {
    return this.request<SavedSearchAlert>(`/api/v1/alerts/${id}`, {
      method: "GET",
    });
  }

  async updateAlert(
    id: string,
    request: UpdateAlertRequest
  ): Promise<SavedSearchAlert> {
    return this.request<SavedSearchAlert>(`/api/v1/alerts/${id}`, {
      method: "PUT",
      body: JSON.stringify(request),
    });
  }

  async deleteAlert(id: string): Promise<void> {
    await this.request<void>(`/api/v1/alerts/${id}`, {
      method: "DELETE",
    });
  }

  // User Notifications
  async getNotifications(
    limit: number = 50,
    offset: number = 0,
    unread_only: boolean = false
  ): Promise<NotificationListResponse> {
    const searchParams = new URLSearchParams();
    searchParams.append("limit", limit.toString());
    searchParams.append("offset", offset.toString());
    if (unread_only) {
      searchParams.append("unread_only", "true");
    }
    const qs = searchParams.toString();
    return this.request<NotificationListResponse>(
      `/api/v1/notifications${qs ? `?${qs}` : ""}`,
      { method: "GET" }
    );
  }

  async markNotificationRead(id: string): Promise<UserNotification> {
    return this.request<UserNotification>(`/api/v1/notifications/${id}/read`, {
      method: "PATCH",
    });
  }

  async markAllNotificationsRead(): Promise<{ success: boolean; updated_count: number }> {
    return this.request<{ success: boolean; updated_count: number }>(
      "/api/v1/notifications/read-all",
      { method: "POST" }
    );
  }

  async deleteNotification(id: string): Promise<void> {
    await this.request<void>(`/api/v1/notifications/${id}`, {
      method: "DELETE",
    });
  }

  // Real Estate Projects
  async getProjects(
    params?: ProjectFilterQuery
  ): Promise<PaginatedProjectResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      if (params.skip !== undefined) searchParams.append("skip", params.skip.toString());
      if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
      if (params.city) searchParams.append("city", params.city);
      if (params.district) searchParams.append("district", params.district);
      if (params.status) searchParams.append("status", params.status);
      if (params.developer) searchParams.append("developer", params.developer);
      if (params.min_price !== undefined) searchParams.append("min_price", params.min_price.toString());
      if (params.max_price !== undefined) searchParams.append("max_price", params.max_price.toString());
      if (params.q) searchParams.append("q", params.q);
    }
    const qs = searchParams.toString();
    return this.request<PaginatedProjectResponse>(
      `/api/v1/projects${qs ? `?${qs}` : ""}`,
      { method: "GET" }
    );
  }

  async getProject(idOrSlug: string): Promise<ProjectDetailResponse> {
    return this.request<ProjectDetailResponse>(
      `/api/v1/projects/${encodeURIComponent(idOrSlug)}`,
      { method: "GET" }
    );
  }

  async createProject(data: ProjectCreate): Promise<ProjectResponse> {
    return this.request<ProjectResponse>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProject(
    id: string,
    data: ProjectUpdate
  ): Promise<ProjectResponse> {
    return this.request<ProjectResponse>(`/api/v1/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getProjectProperties(
    idOrSlug: string,
    params?: {
      skip?: number;
      limit?: number;
      listing_type?: string;
      property_type?: string;
      min_price?: number;
      max_price?: number;
      num_bedrooms?: number;
    }
  ): Promise<PropertyResponse[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      if (params.skip !== undefined) searchParams.append("skip", params.skip.toString());
      if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
      if (params.listing_type) searchParams.append("listing_type", params.listing_type);
      if (params.property_type) searchParams.append("property_type", params.property_type);
      if (params.min_price !== undefined) searchParams.append("min_price", params.min_price.toString());
      if (params.max_price !== undefined) searchParams.append("max_price", params.max_price.toString());
      if (params.num_bedrooms !== undefined) searchParams.append("num_bedrooms", params.num_bedrooms.toString());
    }
    const qs = searchParams.toString();
    return this.request<PropertyResponse[]>(
      `/api/v1/projects/${encodeURIComponent(idOrSlug)}/properties${qs ? `?${qs}` : ""}`,
      { method: "GET" }
    );
  }
}

