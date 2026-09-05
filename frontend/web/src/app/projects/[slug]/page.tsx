"use client";

import { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Building2,
  MapPin,
  Calendar,
  ShieldCheck,
  Tag,
  Home,
  KeyRound,
  TrendingUp,
  Layers,
  ChevronRight,
  Loader2,
  Share2,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { ProjectDetailResponse, PropertyResponse } from "@shared/types";
import { formatPrice, formatProjectStatus } from "@/lib/utils";
import PropertyCard from "@/components/PropertyCard";
import PropertyDetailMap from "@/components/PropertyDetailMap";

interface ProjectDetailPageProps {
  params: Promise<{ slug: string }>;
}

export default function ProjectDetailPage({ params }: ProjectDetailPageProps) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const [project, setProject] = useState<ProjectDetailResponse | null>(null);
  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "masterplan" | "amenities" | "units">("overview");
  const [listingFilter, setListingFilter] = useState<"all" | "sale" | "rent">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingProps, setLoadingProps] = useState(false);
  const [copied, setCopied] = useState(false);

  // Fetch project details
  const loadProject = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getProject(slug);
      setProject(data);
    } catch (err: any) {
      console.error("Failed to load project details:", err);
      setError(err?.message || "Không thể tải thông tin dự án.");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // Fetch project properties
  const fetchUnits = useCallback(async () => {
    if (!slug) return;
    setLoadingProps(true);
    try {
      const units = await apiClient.getProjectProperties(slug, {
        listing_type: listingFilter !== "all" ? listingFilter : undefined,
        limit: 50,
      });
      setProperties(units);
    } catch (err) {
      console.error("Failed to fetch project units:", err);
      setProperties([]);
    } finally {
      setLoadingProps(false);
    }
  }, [slug, listingFilter]);

  useEffect(() => {
    fetchUnits();
  }, [fetchUnits]);

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <p className="mt-3 text-xs font-medium text-slate-500">Đang tải thông tin chi tiết dự án...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <div className="rounded-3xl border border-red-200 bg-red-50/60 p-10 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-4 text-lg font-bold text-red-900">Không thể kết nối máy chủ Space247</h2>
          <p className="mt-2 text-xs text-red-700 leading-relaxed max-w-md mx-auto">{error}</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <button
              onClick={() => {
                loadProject();
                fetchUnits();
              }}
              className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-red-700 transition cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Thử kết nối lại
            </button>
            <Link
              href="/projects"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
            >
              Quay lại danh mục dự án
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center">
        <Building2 className="mx-auto h-16 w-16 text-slate-300" />
        <h1 className="mt-4 text-2xl font-bold text-slate-900">Không tìm thấy thông tin dự án</h1>
        <p className="mt-2 text-sm text-slate-600">
          Dự án bạn tìm kiếm không tồn tại hoặc đã bị gỡ bỏ khỏi hệ thống.
        </p>
        <Link
          href="/projects"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition"
        >
          Quay lại danh mục dự án
        </Link>
      </div>
    );
  }

  const statusInfo = formatProjectStatus(project.status);

  const formatPriceRange = () => {
    if (project.price_range_min && project.price_range_max) {
      return `${formatPrice(project.price_range_min)} - ${formatPrice(project.price_range_max)}`;
    }
    if (project.price_range_min) {
      return `Từ ${formatPrice(project.price_range_min)}`;
    }
    if (project.price_range_max) {
      return `Đến ${formatPrice(project.price_range_max)}`;
    }
    return "Đang cập nhật";
  };

  const heroImage =
    project.images && project.images.length > 0
      ? project.images[0]
      : "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1400&q=80";

  return (
    <div className="min-h-screen bg-slate-50/50 pb-24">
      {/* Breadcrumbs */}
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <nav className="flex items-center gap-1.5 text-xs text-slate-500">
            <Link href="/" className="hover:text-blue-600 transition">
              Trang chủ
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
            <Link href="/projects" className="hover:text-blue-600 transition">
              Dự án
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
            <span className="font-semibold text-slate-900 truncate max-w-xs">{project.name}</span>
          </nav>
        </div>
      </div>

      {/* Hero Header Banner */}
      <div className="relative bg-slate-900 text-white">
        <div className="absolute inset-0 overflow-hidden">
          <img
            src={heroImage}
            alt={project.name}
            className="h-full w-full object-cover opacity-35 filter blur-xs"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/80 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold backdrop-blur-md shadow-xs ${statusInfo.color}`}>
                  {statusInfo.label}
                </span>
                {project.developer && (
                  <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-medium backdrop-blur-md">
                    Chủ đầu tư: {project.developer}
                  </span>
                )}
                {project.legal_status && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 text-emerald-300 px-3 py-1 text-xs font-medium backdrop-blur-md border border-emerald-400/30">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    {project.legal_status}
                  </span>
                )}
              </div>

              <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl text-white">
                {project.name}
              </h1>

              <div className="flex items-center gap-1.5 text-sm text-slate-300">
                <MapPin className="h-4 w-4 text-rose-400 shrink-0" />
                <span>
                  {[project.address, project.ward, project.district, project.city].filter(Boolean).join(", ")}
                </span>
              </div>
            </div>

            {/* Action & Price Range Card */}
            <div className="flex flex-col items-start gap-3 rounded-2xl border border-white/10 bg-white/10 p-5 backdrop-blur-md md:items-end">
              <div className="text-xs text-slate-300 font-medium">Khoảng giá tham khảo</div>
              <div className="text-2xl font-bold text-amber-300">{formatPriceRange()}</div>
              {project.average_price_per_sqm && (
                <div className="text-xs text-slate-300">
                  Đơn giá trung bình:{" "}
                  <span className="font-semibold text-white">
                    ~ {(project.average_price_per_sqm / 1_000_000).toFixed(1)} tr/m²
                  </span>
                </div>
              )}
              <button
                type="button"
                onClick={handleShare}
                className="mt-1 inline-flex items-center gap-1.5 rounded-xl bg-white/20 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/30 transition"
              >
                {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <Share2 className="h-3.5 w-3.5" />}
                <span>{copied ? "Đã sao chép liên kết" : "Chia sẻ dự án"}</span>
              </button>
            </div>
          </div>

          {/* Quick Stats Grid */}
          <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6 border-t border-white/10 pt-6">
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Tổng số căn</div>
              <div className="mt-1 text-base font-bold text-white">
                {project.total_units ? project.total_units.toLocaleString() : "Đang cập nhật"}
              </div>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Năm khởi công</div>
              <div className="mt-1 text-base font-bold text-white">
                {project.launch_year || "Đang cập nhật"}
              </div>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Năm bàn giao</div>
              <div className="mt-1 text-base font-bold text-white">
                {project.handover_year || "Đang cập nhật"}
              </div>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Căn đang bán</div>
              <div className="mt-1 text-base font-bold text-blue-400">
                {project.for_sale_count} tin
              </div>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Căn cho thuê</div>
              <div className="mt-1 text-base font-bold text-emerald-400">
                {project.for_rent_count} tin
              </div>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[11px] text-slate-400">Tổng tin đăng</div>
              <div className="mt-1 text-base font-bold text-amber-300">
                {project.active_properties_count} căn
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-md shadow-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab("overview")}
              className={`border-b-2 py-4 text-xs font-bold transition-colors ${
                activeTab === "overview"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Tổng quan dự án
            </button>
            <button
              onClick={() => setActiveTab("masterplan")}
              className={`border-b-2 py-4 text-xs font-bold transition-colors ${
                activeTab === "masterplan"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Mặt bằng tổng thể (Master plan)
            </button>
            <button
              onClick={() => setActiveTab("amenities")}
              className={`border-b-2 py-4 text-xs font-bold transition-colors ${
                activeTab === "amenities"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Tiện ích nội khu ({project.amenities?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("units")}
              className={`border-b-2 py-4 text-xs font-bold transition-colors flex items-center gap-1.5 ${
                activeTab === "units"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <span>Bảng hàng bất động sản</span>
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                {properties.length}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        {/* Tab 1: Overview */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            <div className="space-y-8 lg:col-span-2">
              {/* Description Section */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                <h2 className="text-lg font-bold text-slate-900 mb-4">Giới thiệu tổng quan</h2>
                <div className="prose prose-slate max-w-none text-sm leading-relaxed text-slate-700 whitespace-pre-line">
                  {project.description || "Thông tin mô tả dự án đang được cập nhật."}
                </div>
              </div>

              {/* Location & Interactive Map Section */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                <h2 className="text-lg font-bold text-slate-900 mb-2">Vị trí & Kết nối giao thông</h2>
                <p className="text-xs text-slate-500 mb-4">
                  {project.address}, {project.district}, {project.city}
                </p>
                {project.latitude && project.longitude ? (
                  <PropertyDetailMap
                    latitude={project.latitude}
                    longitude={project.longitude}
                    title={project.name}
                    address={project.address}
                  />
                ) : (
                  <div className="flex h-64 w-full items-center justify-center rounded-2xl bg-slate-100 text-xs text-slate-400">
                    Tọa độ bản đồ đang được cập nhật
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar Overview */}
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                <h3 className="text-sm font-bold text-slate-900 mb-4">Thông tin pháp lý & quy hoạch</h3>
                <dl className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-slate-100 pb-2">
                    <dt className="text-slate-500">Chủ đầu tư</dt>
                    <dd className="font-semibold text-slate-900">{project.developer || "Đang cập nhật"}</dd>
                  </div>
                  <div className="flex justify-between border-b border-slate-100 pb-2">
                    <dt className="text-slate-500">Trạng thái xây dựng</dt>
                    <dd className="font-semibold text-slate-900">{statusInfo.label}</dd>
                  </div>
                  <div className="flex justify-between border-b border-slate-100 pb-2">
                    <dt className="text-slate-500">Hình thức sở hữu</dt>
                    <dd className="font-semibold text-slate-900">{project.legal_status || "Sổ hồng lâu dài"}</dd>
                  </div>
                  <div className="flex justify-between border-b border-slate-100 pb-2">
                    <dt className="text-slate-500">Quy mô căn hộ</dt>
                    <dd className="font-semibold text-slate-900">
                      {project.total_units ? `${project.total_units.toLocaleString()} căn` : "Đang cập nhật"}
                    </dd>
                  </div>
                  <div className="flex justify-between border-b border-slate-100 pb-2">
                    <dt className="text-slate-500">Năm khởi công</dt>
                    <dd className="font-semibold text-slate-900">{project.launch_year || "Đang cập nhật"}</dd>
                  </div>
                  <div className="flex justify-between pb-2">
                    <dt className="text-slate-500">Dự kiến bàn giao</dt>
                    <dd className="font-semibold text-slate-900">{project.handover_year || "Đang cập nhật"}</dd>
                  </div>
                </dl>
              </div>

              {/* Call to action for properties */}
              <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-6 shadow-xs">
                <h3 className="text-sm font-bold text-blue-950 mb-2">Bảng hàng căn hộ dự án</h3>
                <p className="text-xs text-blue-700 leading-relaxed mb-4">
                  Đang có {project.active_properties_count} căn hộ/nhà phố đang được giao dịch tại {project.name}.
                </p>
                <button
                  onClick={() => setActiveTab("units")}
                  className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white hover:bg-blue-700 transition"
                >
                  <span>Xem danh sách tin đăng</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Master Plan */}
        {activeTab === "masterplan" && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <h2 className="text-lg font-bold text-slate-900 mb-2">Mặt bằng tổng thể (Master plan)</h2>
            <p className="text-xs text-slate-500 mb-6">
              Bản vẽ quy hoạch phân khu, giao thông nội bộ và bố cục các tòa tháp / phân khu thấp tầng.
            </p>
            {project.master_plan_url ? (
              <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
                <img
                  src={project.master_plan_url}
                  alt={`Master Plan ${project.name}`}
                  className="w-full h-auto object-contain max-h-[750px] mx-auto"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 py-16 text-center">
                <Layers className="h-12 w-12 text-slate-300" />
                <h4 className="mt-3 text-sm font-bold text-slate-800">Mặt bằng quy hoạch đang được cập nhật</h4>
                <p className="mt-1 text-xs text-slate-500 max-w-sm">
                  Ban quản lý đang số hóa bản vẽ chi tiết 1/500 cho dự án {project.name}.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Amenities */}
        {activeTab === "amenities" && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <h2 className="text-lg font-bold text-slate-900 mb-2">Hệ sinh thái tiện ích nội khu</h2>
            <p className="text-xs text-slate-500 mb-6">
              Các tiện ích đặc quyền dành cho cư dân và khách thuê tại {project.name}.
            </p>
            {project.amenities && project.amenities.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {project.amenities.map((amenity, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/70 p-4 transition hover:bg-blue-50/50 hover:border-blue-200"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <span className="text-xs font-semibold text-slate-800">{amenity}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500">
                Danh sách tiện ích nội khu đang được cập nhật.
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Sub-Properties Units Grid */}
        {activeTab === "units" && (
          <div className="space-y-6">
            {/* Filter Sub-bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setListingFilter("all")}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    listingFilter === "all"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  Tất cả tin ({project.active_properties_count})
                </button>
                <button
                  type="button"
                  onClick={() => setListingFilter("sale")}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    listingFilter === "sale"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  Cần bán ({project.for_sale_count})
                </button>
                <button
                  type="button"
                  onClick={() => setListingFilter("rent")}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                    listingFilter === "rent"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  Cho thuê ({project.for_rent_count})
                </button>
              </div>

              <Link
                href={`/properties/create?project_id=${project.id}`}
                className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
              >
                <span>+ Đăng tin trong dự án này</span>
              </Link>
            </div>

            {/* Properties Grid */}
            {loadingProps ? (
              <div className="flex h-64 w-full flex-col items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                <p className="mt-2 text-xs font-medium text-slate-500">Đang tải bảng hàng dự án...</p>
              </div>
            ) : properties.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
                <Home className="h-12 w-12 text-slate-300" />
                <h4 className="mt-3 text-sm font-bold text-slate-800">Chưa có tin đăng phù hợp</h4>
                <p className="mt-1 text-xs text-slate-500 max-w-sm">
                  Hiện tại chưa có tin đăng nào thuộc trạng thái này tại {project.name}.
                </p>
                <Link
                  href={`/properties/create?project_id=${project.id}`}
                  className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition"
                >
                  Đăng tin đầu tiên ngay
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {properties.map((prop, idx) => (
                  <PropertyCard key={prop.id} item={prop} index={idx} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
