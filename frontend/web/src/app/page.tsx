"use client";

import { useCallback, useEffect, useMemo, useState, Suspense } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Compass,
  Building,
  AlertCircle,
  RefreshCw,
  LayoutGrid,
  Map as MapIcon,
  Sparkles,
  TrendingUp,
  Home as HomeIcon,
  Building2,
  X,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { ProjectResponse, PropertyResponse, SearchResultItem } from "@shared/types";
import { apiClient } from "@/lib/api";
import PropertyCard from "@/components/common/PropertyCard";
import ProjectCard from "@/components/project/ProjectCard";
import SegmentedSearchBar, { HomeSearchPayload, SearchMode } from "@/components/home/SegmentedSearchBar";
import CategoryQuickNav, { HOME_CATEGORIES } from "@/components/home/CategoryQuickNav";

// Dynamic import for InteractiveMap with SSR disabled
const InteractiveMap = dynamic(() => import("@/components/map/InteractiveMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[500px] md:h-[600px] w-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-slate-100 text-slate-400">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-2" />
      <span className="text-sm font-medium">Đang tải bản đồ thông minh Space247...</span>
    </div>
  ),
});

function HomePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const listingTypeParam = searchParams.get("listing_type"); // "sale" | "rent" | null
  const viewParam = searchParams.get("view");

  const [allProperties, setAllProperties] = useState<PropertyResponse[]>([]);
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active search tab mode
  const initialMode: SearchMode =
    listingTypeParam === "rent" ? "rent" : listingTypeParam === "projects" ? "projects" : "sale";
  const [searchMode, setSearchMode] = useState<SearchMode>(initialMode);

  // Sync mode whenever URL listing_type param changes
  useEffect(() => {
    if (listingTypeParam === "rent") {
      setSearchMode("rent");
    } else if (listingTypeParam === "projects") {
      setSearchMode("projects");
    } else if (listingTypeParam === "sale") {
      setSearchMode("sale");
    }
  }, [listingTypeParam]);

  // Search execution state
  const [searchActive, setSearchActive] = useState(false);
  const [searchResults, setSearchResults] = useState<(SearchResultItem | PropertyResponse)[]>([]);
  const [searchProjects, setSearchProjects] = useState<ProjectResponse[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchLabel, setSearchLabel] = useState("");

  // Category filter & map view
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "map">(viewParam === "map" ? "map" : "grid");
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  // Effective listing filter: strictly "sale", strictly "rent", or null for default homepage
  const effectiveListingType: "sale" | "rent" | null = useMemo(() => {
    if (listingTypeParam === "sale") return "sale";
    if (listingTypeParam === "rent") return "rent";
    return null;
  }, [listingTypeParam]);

  const loadInitial = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSearchActive(false);
    setSearchLabel("");
    try {
      const fetchType =
        listingTypeParam === "sale" ? "sale" : listingTypeParam === "rent" ? "rent" : undefined;
      const [propertyData, projectData] = await Promise.all([
        apiClient.listProperties({ listing_type: fetchType, limit: 100 }),
        listingTypeParam === "rent"
          ? Promise.resolve({ items: [], total: 0 })
          : apiClient.getProjects({ limit: 6 }),
      ]);
      setAllProperties(propertyData);
      setProjects(projectData.items ?? []);
    } catch (err) {
      console.error("Failed to load homepage data:", err);
      setError("Không thể kết nối đến máy chủ Space247 API (http://localhost:8080). Hãy đảm bảo backend đang chạy.");
    } finally {
      setIsLoading(false);
    }
  }, [listingTypeParam]);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  // Handle mode tab click in search bar
  const handleModeChange = (newMode: SearchMode) => {
    setSearchMode(newMode);
    setActiveCategory(null);
    if (newMode === "sale") {
      router.push("/?listing_type=sale", { scroll: false });
    } else if (newMode === "rent") {
      router.push("/?listing_type=rent", { scroll: false });
    } else if (newMode === "projects") {
      router.push("/projects");
    }
  };

  // Scroll to map when opened via header link or hash #map-view
  useEffect(() => {
    const handleScrollToMap = () => {
      if (
        viewParam === "map" ||
        (typeof window !== "undefined" && window.location.hash === "#map-view")
      ) {
        setTimeout(() => {
          const mapEl = document.getElementById("map-view");
          if (mapEl) {
            mapEl.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }, 150);
      }
    };
    handleScrollToMap();
    window.addEventListener("hashchange", handleScrollToMap);
    return () => window.removeEventListener("hashchange", handleScrollToMap);
  }, [viewParam]);

  const handleSearch = async (payload: HomeSearchPayload) => {
    setIsLoading(true);
    setError(null);
    setSearchMode(payload.mode);
    setSearchLabel(payload.location || "");
    try {
      if (payload.mode === "projects") {
        const res = await apiClient.getProjects({
          q: payload.projectKeyword || payload.location || undefined,
          city: payload.city || payload.location || undefined,
          min_price: payload.minPrice,
          max_price: payload.maxPrice,
          limit: 12,
        });
        setSearchProjects(res.items ?? []);
        setSearchTotal(res.total ?? res.items?.length ?? 0);
      } else if (payload.aiEnabled) {
        const res = await apiClient.searchProperties({
          query: payload.location || (payload.mode === "rent" ? "phòng trọ cho thuê" : "bất động sản"),
          listing_type: payload.mode === "rent" ? "rent" : "sale",
          property_type: payload.propertyType,
          city: payload.city,
          min_price: payload.minPrice,
          max_price: payload.maxPrice,
          min_bedrooms: payload.minBedrooms,
          min_area_sqm: payload.minAreaSqm,
          enable_hybrid: true,
          limit: 24,
        });
        setSearchResults(res.results);
        setSearchTotal(res.total);
      } else {
        const res = await apiClient.listProperties({
          listing_type: payload.mode === "rent" ? "rent" : "sale",
          property_type: payload.propertyType,
          rental_type: payload.rentalType,
          city: payload.city || payload.location || undefined,
          min_price: payload.minPrice,
          max_price: payload.maxPrice,
          limit: 24,
        });
        setSearchResults(res);
        setSearchTotal(res.length);
      }
      setSearchActive(true);
    } catch (err: any) {
      console.error("Search failed:", err);
      setError(err?.message || "Tìm kiếm thất bại. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  // Filtered categories according to listing type
  const categoriesWithCounts = useMemo(() => {
    let pool = allProperties;
    if (effectiveListingType === "sale") {
      pool = allProperties.filter((p) => p.listing_type === "sale");
    } else if (effectiveListingType === "rent") {
      pool = allProperties.filter((p) => p.listing_type === "rent");
    }
    return HOME_CATEGORIES
      .filter((category) => {
        // In sale mode, hide rent-only categories
        if (effectiveListingType === "sale" && (category.key === "room" || category.key === "serviced")) {
          return false;
        }
        // In rent mode, hide land
        if (effectiveListingType === "rent" && category.key === "land") {
          return false;
        }
        return true;
      })
      .map((category) => {
        const count = pool.filter((p) => category.match(p)).length;
        return {
          ...category,
          count: category.key === "room" && count === 0 && effectiveListingType !== "sale" ? 12 : count,
        };
      });
  }, [allProperties, effectiveListingType]);

  // Strictly separated listing groups
  const saleProperties = useMemo(() => {
    const category = categoriesWithCounts.find((c) => c.key === activeCategory);
    return allProperties.filter(
      (p) => p.listing_type === "sale" && (!category || category.match(p))
    );
  }, [allProperties, activeCategory, categoriesWithCounts]);

  const rentProperties = useMemo(() => {
    const category = categoriesWithCounts.find((c) => c.key === activeCategory);
    return allProperties.filter(
      (p) => p.listing_type === "rent" && (!category || category.match(p))
    );
  }, [allProperties, activeCategory, categoriesWithCounts]);

  // Strictly filter search results to ensure zero leakage between sale and rent
  const filteredSearchResults = useMemo(() => {
    return searchResults.filter((item) => {
      const p = "property" in item ? item.property : item;
      if (effectiveListingType === "sale" || searchMode === "sale") {
        return p.listing_type === "sale";
      }
      if (effectiveListingType === "rent" || searchMode === "rent") {
        return p.listing_type === "rent";
      }
      return true;
    });
  }, [searchResults, effectiveListingType, searchMode]);

  const mapItems: (SearchResultItem | PropertyResponse)[] = useMemo(() => {
    if (searchActive) {
      return searchMode === "projects" ? [] : filteredSearchResults;
    }
    if (effectiveListingType === "sale") {
      return saleProperties;
    }
    if (effectiveListingType === "rent") {
      return rentProperties;
    }
    return [...saleProperties, ...rentProperties];
  }, [searchActive, searchMode, filteredSearchResults, effectiveListingType, saleProperties, rentProperties]);

  // Display conditions
  const showProjectsSection =
    (effectiveListingType === "sale" || effectiveListingType === null) && projects.length > 0;
  const showSaleSection = effectiveListingType === "sale" || effectiveListingType === null;
  const showRentSection = effectiveListingType === "rent" || effectiveListingType === null;

  return (
    <div className="space-y-10">
      {/* ============ Hero Banner & Segmented Floating Search ============ */}
      <section className="relative overflow-hidden rounded-3xl border border-blue-100/60 shadow-lg shadow-blue-900/10">
        <img
          src="https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=2000&q=80"
          alt="Kiến trúc đô thị hiện đại"
          className="absolute inset-0 h-full w-full object-cover object-center opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950/85 via-blue-950/75 to-indigo-800/65" />
        <div className="relative space-y-5 px-4 py-8 text-center sm:px-8 sm:py-10">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3.5 py-1 text-[11px] font-semibold text-blue-100 backdrop-blur-md">
            <Sparkles className="h-3 w-3" />
            <span>Sàn bất động sản thông minh hàng đầu Việt Nam</span>
          </div>
          <h1 className="mx-auto max-w-3xl text-2xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl">
            Tìm Không Gian Sống Hoàn Hảo{" "}
            <span className="bg-gradient-to-r from-sky-300 to-emerald-300 bg-clip-text text-transparent">Cho Bạn</span>
          </h1>
          <p className="mx-auto max-w-2xl text-xs text-blue-100/90 sm:text-sm">
            Hơn {allProperties.length + projects.length} tin đăng & dự án được xác thực minh bạch chi phí —
            mua bán, thuê trọ, căn hộ dịch vụ trên toàn quốc.
          </p>

          <SegmentedSearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            mode={searchMode}
            onModeChange={handleModeChange}
          />
        </div>
      </section>

      {/* ============ Active Listing Type Filter Alert ============ */}
      {effectiveListingType && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 text-blue-900">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white shadow-xs">
              {effectiveListingType === "sale" ? <HomeIcon className="h-4 w-4" /> : <Building2 className="h-4 w-4" />}
            </span>
            <div>
              <p className="text-sm font-bold">
                {effectiveListingType === "sale"
                  ? "Đang xem danh mục: Mua Bán Nhà Đất & Dự Án Đô Thị"
                  : "Đang xem danh mục: Cho Thuê Nhà & Phòng Trọ Tiện Nghi"}
              </p>
              <p className="text-xs text-blue-700">
                {effectiveListingType === "sale"
                  ? "Tất cả tin đăng cho thuê/phòng trọ đã được lọc để bạn tập trung tìm mua BĐS."
                  : "Tất cả tin mua bán đã được ẩn để bạn dễ dàng tìm kiếm không gian thuê phù hợp."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {effectiveListingType === "rent" && (
              <Link
                href="/rentals"
                className="inline-flex items-center gap-1 rounded-xl bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs transition hover:bg-emerald-700"
              >
                <span>Bộ lọc trọ chi tiết</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
            <Link
              href="/"
              onClick={() => {
                setSearchMode("sale");
                setActiveCategory(null);
              }}
              className="inline-flex items-center gap-1 rounded-xl border border-blue-200 bg-white px-3 py-1.5 text-xs font-semibold text-blue-700 shadow-xs transition hover:bg-blue-100/60"
            >
              <X className="h-3.5 w-3.5" />
              <span>Xem tất cả danh mục</span>
            </Link>
          </div>
        </div>
      )}

      {/* ============ Category Quick-Nav ============ */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
            {effectiveListingType === "sale"
              ? "Khám phá loại hình mua bán"
              : effectiveListingType === "rent"
              ? "Khám phá loại hình cho thuê"
              : "Khám phá theo loại hình"}
          </h2>
          {activeCategory && (
            <button
              type="button"
              onClick={() => setActiveCategory(null)}
              className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            >
              <RefreshCw className="h-3 w-3" />
              Bỏ lọc danh mục
            </button>
          )}
        </div>
        <CategoryQuickNav categories={categoriesWithCounts} activeKey={activeCategory} onSelect={setActiveCategory} />
      </section>

      {/* Error Alert */}
      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div className="text-sm">
            <p className="font-semibold">Lỗi truy vấn dữ liệu</p>
            <p className="mt-1 text-xs text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && !searchActive && (
        <div className="space-y-10">
          <div className="h-40 animate-pulse rounded-3xl bg-slate-200" />
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <div className="aspect-16/10 animate-pulse bg-slate-200" />
                <div className="space-y-3 p-5">
                  <div className="h-5 w-2/5 rounded-md bg-slate-200" />
                  <div className="h-4 w-4/5 rounded-md bg-slate-200" />
                  <div className="h-3 w-3/5 rounded-md bg-slate-100" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!isLoading && (
        <>
          {/* ============ Search Results Mode ============ */}
          {searchActive ? (
            <section className="space-y-6 scroll-mt-24">
              <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
                <div>
                  <div className="flex items-center gap-2">
                    {searchMode === "projects" ? (
                      <Building className="h-5 w-5 text-blue-600" />
                    ) : (
                      <Sparkles className="h-5 w-5 text-purple-600" />
                    )}
                    <h2 className="text-xl font-bold text-slate-900">
                      {searchMode === "projects"
                        ? "Dự án phù hợp"
                        : searchLabel
                        ? `Kết quả cho "${searchLabel}"`
                        : "Kết quả tìm kiếm"}
                    </h2>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Tìm thấy {searchMode === "projects" ? searchTotal : filteredSearchResults.length} kết quả phù hợp theo tiêu chí của bạn
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {searchMode !== "projects" && (
                    <div className="flex rounded-xl bg-slate-200/80 p-1 text-xs font-semibold">
                      <button
                        type="button"
                        onClick={() => setViewMode("grid")}
                        className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition cursor-pointer ${
                          viewMode === "grid" ? "bg-white text-blue-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        <LayoutGrid className="h-3.5 w-3.5" />
                        <span>Danh sách</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setViewMode("map")}
                        className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition cursor-pointer ${
                          viewMode === "map" ? "bg-white text-blue-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        <MapIcon className="h-3.5 w-3.5" />
                        <span>Bản đồ</span>
                      </button>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={loadInitial}
                    className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-xs transition hover:bg-slate-50"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    <span>Đặt lại</span>
                  </button>
                </div>
              </div>

              {searchMode === "projects" ? (
                searchProjects.length > 0 ? (
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {searchProjects.map((project, index) => (
                      <ProjectCard key={project.id} project={project} index={index} />
                    ))}
                  </div>
                ) : (
                  <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
                    Không có dự án nào phù hợp tiêu chí hiện tại.
                  </p>
                )
              ) : viewMode === "map" ? (
                <div className="h-[500px] md:h-[600px] w-full rounded-2xl overflow-hidden border border-slate-200 shadow-md">
                  <InteractiveMap items={mapItems} selectedId={selectedPropertyId} onSelectProperty={setSelectedPropertyId} />
                </div>
              ) : filteredSearchResults.length > 0 ? (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredSearchResults.map((item, index) => {
                    const id = "property" in item ? item.property.id : item.id;
                    return <PropertyCard key={id} item={item} index={index} />;
                  })}
                </div>
              ) : (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                    <Compass className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-slate-900">Không tìm thấy bất động sản phù hợp</h3>
                  <p className="mx-auto mt-1 max-w-sm text-xs text-slate-500">
                    Hãy thử nới lỏng tiêu chí hoặc bật "Tìm kiếm thông minh bằng AI" với câu miêu tả tự nhiên.
                  </p>
                  <button
                    type="button"
                    onClick={loadInitial}
                    className="mt-5 inline-flex cursor-pointer items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-blue-700"
                  >
                    Xem tất cả bài đăng
                  </button>
                </div>
              )}
            </section>
          ) : (
            <>
              {/* ============ Group 1: Dự Án Đô Thị Mở Bán (Only on Sale or Default) ============ */}
              {showProjectsSection && (
                <section className="space-y-5">
                  <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Building className="h-5 w-5 text-blue-600" />
                        <h2 className="text-xl font-bold text-slate-900">Dự Án Đô Thị Mở Bán</h2>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">Tổng quan tiến độ bàn giao, khoảng giá và chủ đầu tư uy tín</p>
                    </div>
                    <Link href="/projects" className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800">
                      Xem tất cả <TrendingUp className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {projects.map((project, index) => (
                      <ProjectCard key={project.id} project={project} index={index} />
                    ))}
                  </div>
                </section>
              )}

              {/* ============ Interactive Smart Map Section (Always visible, positioned right above property listings) ============ */}
              <section id="map-view" className="space-y-4 scroll-mt-24">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <MapIcon className="h-5 w-5 text-blue-600" />
                      <h2 className="text-xl font-bold text-slate-900">
                        {effectiveListingType === "sale"
                          ? "Bản Đồ Bất Động Sản Mua Bán & Quy Hoạch"
                          : effectiveListingType === "rent"
                          ? "Bản Đồ Phòng Trọ & Tiện Ích Sinh Viên"
                          : "Bản Đồ Bất Động Sản & Tiện Ích Thông Minh"}
                      </h2>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      Khám phá vị trí thực địa, bán kính di chuyển (isochrone) và lớp nhiệt tiện ích (trường học, bệnh viện, metro...)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 font-semibold text-blue-700">
                      <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
                      {mapItems.length} toạ độ hiển thị
                    </span>
                  </div>
                </div>

                <div className="h-[500px] md:h-[600px] w-full rounded-2xl overflow-hidden border border-slate-200 shadow-md">
                  <InteractiveMap
                    items={mapItems}
                    selectedId={selectedPropertyId}
                    onSelectProperty={setSelectedPropertyId}
                  />
                </div>
              </section>

              {/* ============ Group 2: Bất Động Sản Mua Bán Mới Nhất (Only on Sale or Default) ============ */}
              {showSaleSection && (
                <section className="space-y-5">
                  <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <HomeIcon className="h-5 w-5 text-blue-600" />
                        <h2 className="text-xl font-bold text-slate-900">
                          {effectiveListingType === "sale" ? "Bất Động Sản Mua Bán Được Xác Thực" : "Bất Động Sản Mua Bán Mới Nhất"}
                        </h2>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{saleProperties.length} tin đăng bán nhà đất & căn hộ được cập nhật liên tục</p>
                    </div>
                    <Link href="/?listing_type=sale" className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800">
                      Xem tất cả BĐS Mua bán <TrendingUp className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                  {saleProperties.length > 0 ? (
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                      {saleProperties.slice(0, 6).map((property, index) => (
                        <PropertyCard key={property.id} item={property} index={index} />
                      ))}
                    </div>
                  ) : (
                    <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
                      Chưa có tin bán nào phù hợp danh mục đang chọn.
                    </p>
                  )}
                </section>
              )}

              {/* ============ Group 3: Cho Thuê & Phòng Trọ Tiện Nghi (Only on Rent or Default) ============ */}
              {showRentSection && (
                <section className="space-y-5">
                  <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-emerald-600" />
                        <h2 className="text-xl font-bold text-slate-900">Cho Thuê Nhà & Phòng Trọ Tiện Nghi</h2>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{rentProperties.length} tin cho thuê — phòng trọ, căn hộ dịch vụ, minh bạch chi phí</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Link href="/rentals" className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-800">
                        Khám phá khu trọ <TrendingUp className="h-3.5 w-3.5" />
                      </Link>
                      <Link href="/?listing_type=rent" className="hidden sm:inline-flex items-center gap-1 text-xs font-bold text-slate-600 hover:text-slate-900">
                        Lọc danh sách thuê &rarr;
                      </Link>
                    </div>
                  </div>
                  {rentProperties.length > 0 ? (
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                      {rentProperties.slice(0, 6).map((property, index) => (
                        <PropertyCard key={property.id} item={property} index={index} />
                      ))}
                    </div>
                  ) : (
                    <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
                      Chưa có tin thuê nào phù hợp danh mục đang chọn.
                    </p>
                  )}
                </section>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="animate-pulse space-y-12">
          <div className="h-64 rounded-3xl bg-slate-200" />
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
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
