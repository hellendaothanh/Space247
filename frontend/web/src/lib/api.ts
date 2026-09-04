import { RealEstateApiClient } from "@shared/api-client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

export const apiClient = new RealEstateApiClient({
  baseUrl: API_BASE_URL.replace(/\/api\/v1\/?$/, ""), // RealEstateApiClient prepends /api/v1
  timeoutMs: 20000,
});
