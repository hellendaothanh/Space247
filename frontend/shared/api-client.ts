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
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
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

  async getProperty(id: string): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${encodeURIComponent(id)}`);
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
}

