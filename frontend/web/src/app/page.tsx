"use client";

import { useCallback, useEffect, useMemo, useState, Suspense, use } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Compass, Building, AlertCircle, RefreshCw, LayoutGrid, Map as MapIcon, Sparkles, TrendingUp, Home as HomeIcon, Building2 } from "lucide-react";
import { ProjectResponse, PropertyResponse, SearchResultItem } from "@shared/types";
import { apiClient } from "@/lib/api";
import PropertyCard from "@/components/common/PropertyCard";
import PropertyMap from "@/components/PropertyMap";
import ProjectCard from "@/components/project/ProjectCard";
import SegmentedSearchBar, { HomeSearchPayload, SearchMode } from "@/components/home/SegmentedSearchBar";
import CategoryQuickNav, { HOME_CATEGORIES } from "@/components/home/CategoryQuickNav";

function HomePageContent() {
  const searchParams = useSearchParams();
  const viewParam = searchParams.get("view");

  const [allProperties, setAllProperties] = useState<PropertyResponse[]>([]);
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search state
  const [searchActive, setSearchActive] = useState(false);
  const [searchMode, setSearchMode] = useState<SearchMode>("sale");
  const [searchResults, setSearchResults] = useState<(SearchResultItem | PropertyResponse)[]>([]);
  const [searchProjects, setSearchProjects] = useState<ProjectResponse[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchLabel, setSearchLabel] = useState("");

  // Category filter & map view
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "map">(viewParam === "map" ? "map" : "grid");
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  const loadInitial = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSearchActive(false);
    setSearchLabel("");
    try {
      const [propertyData, projectData] = await Promise.all([
        apiClient.listProperties({ limit: 100 }),
        apiClient.getProjects({ limit: 6 }),
      ]);
      setAllProperties(propertyData);
      setProjects(projectData.items ?? []);
    } catch (err) {
      console.error("Failed to load homepage data:", err);
      setError("Không thể kết nối đến máy chủ Space247 API (http://localhost:8080). Hãy đảm bảo backend đang chạy.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  // Scroll to map when opened via header link
  useEffect(() => {
    if (viewParam === "map" || (typeof window !== "undefined" && window.location.hash === "#map-view")) {
      setViewMode("map");
      setTimeout(() => document.getElementById("map-view")?.scrollIntoView({ behavior: "smooth" }), 150);
    }
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

  // Category counting & filtering (homepage groups)
  const categoriesWithCounts = useMemo(
    () => HOME_CATEGORIES.map((category) => ({ ...category, count: allProperties.filter((p) => category.match(p)).length })),
    [allProperties]
  );

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

  const mapItems: (SearchResultItem | PropertyResponse)[] = searchActive
    ? searchMode === "projects"
      ? []
      : searchResults
    : [...saleProperties, ...rentProperties];

  return (
    <div className="space-y-10">
      {/* ============ Hero Banner & Segmented Floating Search ============ */}
      <section className="relative overflow-hidden rounded-3xl border border-blue-100/60 shadow-lg shadow-blue-900/10">
        <img
          src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=2000&q=80"
          alt="Bất động sản cao cấp Space247"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950/90 via-blue-800/80 to-indigo-700/70" />
        <div className="relative space-y-6 px-4 py-12 text-center sm:px-8 sm:py-16">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1.5 text-xs font-semibold text-blue-100 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Sàn bất động sản thông minh hàng đầu Việt Nam</span>
          </div>
          <h1 className="mx-auto max-w-3xl text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
            Tìm Không Gian Sống Hoàn Hảo{" "}
            <span className="bg-gradient-to-r from-sky-300 to-emerald-300 bg-clip-text text-transparent">Cho Bạn</span>
          </h1>
          <p className="mx-auto max-w-2xl text-sm text-blue-100/90 sm:text-base">
            Hơn {allProperties.length + projects.length} tin đăng & dự án được xác thực minh bạch chi phí —
            mua bán, thuê trọ, căn hộ dịch vụ trên toàn quốc.
          </p>

          <SegmentedSearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>
      </section>

      {/* ============ Category Quick-Nav ============ */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">Khám phá theo loại hình</h2>
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
            <section id="map-view" className="space-y-6 scroll-mt-24">
              <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-4 sm:flex-row sm:items-center">
                <div>
                  <div className="flex items-center gap-2">
                    {searchMode === "projects" ? (
                      <Building className="h-5 w-5 text-blue-600" />
                    ) : (
                      <Sparkles className="h-5 w-5 text-purple-600" />
                    )}
                    <h2 className="text-xl font-bold text-slate-900">
                      {searchMode === "projects" ? "Dự án phù hợp" : searchLabel ? `Kết quả cho "${searchLabel}"` : "Kết quả tìm kiếm"}
                    </h2>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Tìm thấy {searchTotal} kết quả phù hợp theo tiêu chí của bạn
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
                <PropertyMap items={mapItems} selectedId={selectedPropertyId} onSelectProperty={setSelectedPropertyId} />
              ) : searchResults.length > 0 ? (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {searchResults.map((item, index) => {
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
              {/* ============ Group 1: Dự Án Đô Thị Nổi Bật ============ */}
              {projects.length > 0 && (
                <section className="space-y-5">
                  <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Building className="h-5 w-5 text-blue-600" />
                        <h2 className="text-xl font-bold text-slate-900">Dự Án Đô Thị Nổi Bật</h2>
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

              {/* ============ Group 2: Bất Động Sản Bán Mới Nhất ============ */}
              <section id="map-view" className="space-y-5 scroll-mt-24">
                <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <HomeIcon className="h-5 w-5 text-blue-600" />
                      <h2 className="text-xl font-bold text-slate-900">Bất Động Sản Bán Mới Nhất</h2>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{saleProperties.length} tin đăng bán được cập nhật liên tục</p>
                  </div>
                  <Link href="/?listing_type=sale" className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800">
                    Xem tất cả <TrendingUp className="h-3.5 w-3.5" />
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

              {/* ============ Group 3: Cho Thuê & Phòng Trọ Tiện Nghi ============ */}
              <section className="space-y-5">
                <div className="flex items-end justify-between border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-emerald-600" />
                      <h2 className="text-xl font-bold text-slate-900">Cho Thuê & Phòng Trọ Tiện Nghi</h2>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{rentProperties.length} tin cho thuê — điện nước minh bạch, không phí ẩn</p>
                  </div>
                  <Link href="/rentals" className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-800">
                    Khám phá khu trọ <TrendingUp className="h-3.5 w-3.5" />
                  </Link>
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
