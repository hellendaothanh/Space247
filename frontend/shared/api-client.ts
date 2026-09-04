/**
 * Space247 - Shared API Client
 * Compatible with Next.js (Web) and React Native / Mobile
 */

import {
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
        throw new Error(
          `API Error [${response.status}]: ${
            typeof errorData.detail === "object"
              ? JSON.stringify(errorData.detail)
              : errorData.detail || response.statusText
          }`
        );
      }

      if (response.status === 204) {
        return null as unknown as T;
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timeoutId);
    }
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

  async getProperty(id: string): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${id}`);
  }

  async updateProperty(
    id: string,
    data: PropertyUpdate
  ): Promise<PropertyResponse> {
    return this.request<PropertyResponse>(`/api/v1/properties/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProperty(id: string): Promise<void> {
    return this.request<void>(`/api/v1/properties/${id}`, {
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
}
