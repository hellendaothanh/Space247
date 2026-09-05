"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SearchResultItem, PropertyResponse, ListingType } from "@shared/types";
import { apiClient } from "@/lib/api";
import SearchSection, { FilterState } from "@/components/SearchSection";
import PropertyCard from "@/components/PropertyCard";
import PropertyMap from "@/components/PropertyMap";
import { Compass, Building, AlertCircle, RefreshCw, LayoutGrid, Map as MapIcon } from "lucide-react";

function HomePageContent() {
  const searchParams = useSearchParams();
  const listingTypeParam = (searchParams.get("listing_type") as ListingType) || null;
  const viewParam = searchParams.get("view");

  const [results, setResults] = useState<(SearchResultItem | PropertyResponse)[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [viewMode, setViewMode] = useState<"grid" | "map">("grid");
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  // Initial load: Fetch latest properties via list endpoint filtered by listing_type if present
  const loadInitialProperties = useCallback(
    async (customType?: ListingType | null) => {
      setIsLoading(true);
      setError(null);
      try {
        const typeToQuery = customType !== undefined ? customType : listingTypeParam;
        const data = await apiClient.listProperties({
          limit: 24,
          listing_type: typeToQuery || undefined,
        });
        setResults(data);
        setTotalCount(data.length);
        setIsSearchActive(false);
      } catch (err: any) {
        console.error("Failed to load initial properties:", err);
        setError(
          "Không thể kết nối đến máy chủ Space247 API (http://localhost:8080). Hãy đảm bảo backend đang chạy."
        );
      } finally {
        setIsLoading(false);
      }
    },
    [listingTypeParam]
  );

  useEffect(() => {
    loadInitialProperties(listingTypeParam);
  }, [listingTypeParam, loadInitialProperties]);

  // Handle Map view query parameter and hash navigation
  useEffect(() => {
    if (viewParam === "map" || (typeof window !== "undefined" && window.location.hash === "#map-view")) {
      setViewMode("map");
      const mapEl = document.getElementById("map-view");
      if (mapEl) {
        setTimeout(() => {
          mapEl.scrollIntoView({ behavior: "smooth" });
        }, 150);
      }
    }
  }, [viewParam]);

  // Handle Natural Language / Filter Search
  const handleSearch = async (filters: FilterState) => {
    setIsLoading(true);
    setError(null);

    // If query is empty and no specific filters, fallback to list
    if (
      !filters.query &&
      !filters.listing_type &&
      !filters.property_type &&
      !filters.city &&
      filters.min_price === undefined &&
      filters.max_price === undefined
    ) {
      return loadInitialProperties(listingTypeParam);
    }

    try {
      setIsSearchActive(true);
      const searchRes = await apiClient.searchProperties({
        query: filters.query || "bất động sản",
        listing_type: filters.listing_type,
        property_type: filters.property_type,
        city: filters.city,
        min_price: filters.min_price,
        max_price: filters.max_price,
        enable_hybrid: filters.enable_hybrid,
        limit: 24,
      });

      setResults(searchRes.results);
      setTotalCount(searchRes.total);
    } catch (err: any) {
      console.error("Search failed:", err);
      setError(
        err?.message || "Tìm kiếm thất bại. Vui lòng thử lại với từ khóa khác."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getSectionTitle = () => {
    if (isSearchActive) return "Kết quả tìm kiếm thông minh";
    if (listingTypeParam === "sale") return "Bất động sản Mua bán";
    if (listingTypeParam === "rent") return "Bất động sản Cho thuê";
    return "Bất động sản nổi bật mới nhất";
  };

  const getSectionSubtitle = () => {
    if (isSearchActive)
      return `Tìm thấy ${totalCount} kết quả phù hợp theo mô tả và tiêu chí của bạn`;
    if (listingTypeParam === "sale")
      return "Danh sách nhà đất, căn hộ đang mở bán được cập nhật liên tục";
    if (listingTypeParam === "rent")
      return "Danh sách nhà đất, căn hộ cho thuê giá tốt được cập nhật liên tục";
    return "Danh sách bất động sản được cập nhật liên tục trên toàn quốc";
  };

  return (
    <div className="space-y-12">
      {/* Hero & Semantic Search */}
      <section id="ai-search">
        <SearchSection
          onSearch={handleSearch}
          isLoading={isLoading}
          totalResults={totalCount}
          initialListingType={listingTypeParam || undefined}
        />
      </section>

      {/* Results Header */}
      <section id="map-view" className="space-y-6 scroll-mt-24">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Building className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-bold text-slate-900">
                {getSectionTitle()}
              </h2>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {getSectionSubtitle()}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* View Mode Toggle: Grid vs Map */}
            <div className="flex rounded-xl bg-slate-200/80 p-1 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition cursor-pointer ${
                  viewMode === "grid"
                    ? "bg-white text-blue-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                <span>Danh sách</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode("map")}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition cursor-pointer ${
                  viewMode === "map"
                    ? "bg-white text-blue-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <MapIcon className="h-3.5 w-3.5" />
                <span>Bản đồ</span>
              </button>
            </div>

            {isSearchActive && (
              <button
                type="button"
                onClick={() => loadInitialProperties(listingTypeParam)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-xs hover:bg-slate-50 transition cursor-pointer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Đặt lại</span>
              </button>
            )}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">Lỗi truy vấn dữ liệu</p>
              <p className="mt-1 text-xs text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="animate-pulse rounded-2xl border border-slate-200 bg-white overflow-hidden"
              >
                <div className="aspect-16/10 bg-slate-200" />
                <div className="p-5 space-y-3">
                  <div className="h-5 w-2/5 bg-slate-200 rounded-md" />
                  <div className="h-4 w-4/5 bg-slate-200 rounded-md" />
                  <div className="h-3 w-3/5 bg-slate-100 rounded-md" />
                  <div className="pt-3 border-t border-slate-100 flex justify-between">
                    <div className="h-3 w-1/4 bg-slate-200 rounded-md" />
                    <div className="h-3 w-1/4 bg-slate-200 rounded-md" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && results.length === 0 && !error && (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
              <Compass className="h-6 w-6" />
            </div>
            <h3 className="mt-4 text-base font-semibold text-slate-900">
              Không tìm thấy bất động sản phù hợp
            </h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              Hãy thử nới lỏng các tiêu chí lọc hoặc sử dụng câu miêu tả tự nhiên khác.
            </p>
            <button
              type="button"
              onClick={() => loadInitialProperties(listingTypeParam)}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 cursor-pointer"
            >
              Xem tất cả bài đăng
            </button>
          </div>
        )}

        {/* Property Grid or Map View */}
        {!isLoading && results.length > 0 && (
          <>
            {viewMode === "grid" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {results.map((item, index) => {
                  const id = "property" in item ? item.property.id : item.id;
                  return <PropertyCard key={id} item={item} index={index} />;
                })}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-500 px-1">
                  <span>
                    Hiển thị các bài đăng có tọa độ địa lý trên bản đồ tương tác. Nhấp vào điểm ghim để xem nhanh thông tin.
                  </span>
                </div>
                <PropertyMap
                  items={results}
                  selectedId={selectedPropertyId}
                  onSelectProperty={(id) => setSelectedPropertyId(id)}
                />
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-12 animate-pulse">
          <div className="h-64 rounded-3xl bg-slate-200" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-80 rounded-2xl bg-slate-200" />
            ))}
          </div>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
