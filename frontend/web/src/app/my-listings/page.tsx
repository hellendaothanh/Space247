"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Rocket,
  Edit3,
  Trash2,
  Search,
  X,
  Plus,
  Calendar,
  MapPin,
  Heart,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Sparkles,
  AlertTriangle,
  RotateCw,
  Tag,
  Check,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import type { MyListingItem, MyListingsStats } from "@shared/types";

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Gần đây";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "Gần đây";
  }
}

function MyListingsContent() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentTab = searchParams.get("tab") || "all";
  const urlQ = searchParams.get("q") || "";

  const [items, setItems] = useState<MyListingItem[]>([]);
  const [stats, setStats] = useState<MyListingsStats>({
    total_listings: 0,
    active_listings: 0,
    sold_or_rented_count: 0,
    hidden_listings: 0,
    total_views: 0,
    total_favorites: 0,
  });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchKeyword, setSearchKeyword] = useState(urlQ);

  // Action states
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<MyListingItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Auto hide toast
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 3500);
      return () => clearTimeout(t);
    }
  }, [toast]);

  // Fetch listings
  const loadListings = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getMyListings({
        page,
        page_size: 8,
        status: currentTab === "all" ? undefined : currentTab,
        q: urlQ || undefined,
      });
      setItems(res.items || []);
      setStats(res.stats || stats);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      console.error("Failed to fetch my listings:", err);
      // If unauthorized, redirect to login
      if (err?.status === 401) {
        router.push("/login?redirect=/my-listings");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login?redirect=/my-listings");
      return;
    }
    if (user) {
      loadListings();
    }
  }, [user, isAuthLoading, currentTab, urlQ, page]);

  const handleTabChange = (tab: string) => {
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    if (tab === "all") {
      params.delete("tab");
    } else {
      params.set("tab", tab);
    }
    router.push(`/my-listings?${params.toString()}`);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    if (searchKeyword.trim()) {
      params.set("q", searchKeyword.trim());
    } else {
      params.delete("q");
    }
    router.push(`/my-listings?${params.toString()}`);
  };

  const clearSearch = () => {
    setSearchKeyword("");
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    params.delete("q");
    router.push(`/my-listings?${params.toString()}`);
  };

  // 1. Refresh listing
  const handleRefreshListing = async (item: MyListingItem) => {
    setActionLoadingId(item.id);
    try {
      await apiClient.refreshListing(item.id);
      setToast({ type: "success", message: `Đã đẩy tin "${item.title.slice(0, 30)}..." lên đầu trang thành công!` });
      await loadListings();
    } catch {
      setToast({ type: "error", message: "Không thể đẩy tin. Vui lòng thử lại sau." });
    } finally {
      setActionLoadingId(null);
    }
  };

  // 2. Toggle visibility
  const handleToggleVisibility = async (item: MyListingItem) => {
    setActionLoadingId(item.id);
    const nextVisibility = !item.is_visible;
    try {
      await apiClient.toggleListingVisibility(item.id, nextVisibility);
      setToast({
        type: "success",
        message: nextVisibility
          ? "Đã bật hiển thị tin đăng ra trang chủ & tìm kiếm."
          : "Đã tạm ẩn tin đăng. Người tìm kiếm sẽ không thấy tin này.",
      });
      await loadListings();
    } catch {
      setToast({ type: "error", message: "Thao tác ẩn/hiện tin thất bại. Vui lòng thử lại." });
    } finally {
      setActionLoadingId(null);
    }
  };

  // 3. Mark sold / rented
  const handleMarkSold = async (item: MyListingItem) => {
    setActionLoadingId(item.id);
    const targetStatus = item.listing_type === "rent" ? "rented" : "sold";
    try {
      await apiClient.markListingSold(item.id, targetStatus);
      setToast({
        type: "success",
        message: targetStatus === "sold" ? "Đã đánh dấu BĐS là ĐÃ BÁN!" : "Đã đánh dấu BĐS là ĐÃ CHO THUÊ!",
      });
      await loadListings();
    } catch {
      setToast({ type: "error", message: "Không thể cập nhật trạng thái đã bán. Thử lại sau." });
    } finally {
      setActionLoadingId(null);
    }
  };

  // 4. Delete listing
  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;
    setIsDeleting(true);
    try {
      await apiClient.deleteListing(itemToDelete.id);
      setToast({ type: "success", message: "Đã xóa tin đăng vĩnh viễn khỏi hệ thống." });
      setDeleteModalOpen(false);
      setItemToDelete(null);
      await loadListings();
    } catch {
      setToast({ type: "error", message: "Xóa tin đăng thất bại. Vui lòng thử lại sau." });
    } finally {
      setIsDeleting(false);
    }
  };

  if (isAuthLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/60 pb-24 dark:bg-slate-950">
      {/* Toast Alert */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl transition animate-in fade-in slide-in-from-bottom-5 dark:border-slate-800 dark:bg-slate-900">
          {toast.type === "success" ? (
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <Check className="h-4 w-4" />
            </span>
          ) : (
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
              <AlertTriangle className="h-4 w-4" />
            </span>
          )}
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">{toast.message}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="border-b border-slate-200/80 bg-white py-8 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full border border-blue-200/80 bg-blue-50 px-2.5 py-0.5 text-[11px] font-semibold text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/40 dark:text-blue-300">
                <Building2 className="h-3 w-3" />
                <span>My Listings Hub</span>
              </div>
              <h1 className="mt-1.5 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
                Quản Lý Tin Đăng Của Tôi
              </h1>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Theo dõi hiệu quả tương tác, làm mới tin và cập nhật trạng thái bất động sản tức thì.
              </p>
            </div>

            <Link
              href="/properties/create"
              className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/25 transition hover:bg-blue-700 active:scale-95"
            >
              <Plus className="h-4 w-4" />
              <span>Đăng Tin Mới</span>
            </Link>
          </div>

          {/* KPI Metrics Row */}
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
            {/* KPI 1: Tổng tin */}
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/70 p-4 transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Tổng tin đăng</span>
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  <Building2 className="h-3.5 w-3.5" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-extrabold text-slate-900 dark:text-white">{stats.total_listings}</p>
            </div>

            {/* KPI 2: Đang hiển thị */}
            <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/40 p-4 transition hover:bg-emerald-50/70 dark:border-emerald-900/40 dark:bg-emerald-950/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-emerald-800 dark:text-emerald-300">Đang hiển thị</span>
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-emerald-200 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-extrabold text-emerald-700 dark:text-emerald-400">{stats.active_listings}</p>
            </div>

            {/* KPI 3: Lượt xem tích lũy */}
            <div className="rounded-2xl border border-blue-200/80 bg-blue-50/40 p-4 transition hover:bg-blue-50/70 dark:border-blue-900/40 dark:bg-blue-950/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-blue-800 dark:text-blue-300">Lượt xem tích lũy</span>
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  <Eye className="h-3.5 w-3.5" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-extrabold text-blue-700 dark:text-blue-400">
                {stats.total_views.toLocaleString("vi-VN")}
              </p>
            </div>

            {/* KPI 4: Giao dịch thành công */}
            <div className="rounded-2xl border border-purple-200/80 bg-purple-50/40 p-4 transition hover:bg-purple-50/70 dark:border-purple-900/40 dark:bg-purple-950/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-purple-800 dark:text-purple-300">Đã bán / Cho thuê</span>
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-purple-200 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                  <Sparkles className="h-3.5 w-3.5" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-extrabold text-purple-700 dark:text-purple-400">
                {stats.sold_or_rented_count}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        {/* Filter Bar & Search */}
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          {/* Status Tabs */}
          <div className="no-scrollbar flex items-center gap-1.5 overflow-x-auto rounded-2xl border border-slate-200/80 bg-white p-1.5 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
            {[
              { id: "all", label: "Tất cả tin", count: stats.total_listings },
              { id: "active", label: "Đang hiển thị", count: stats.active_listings },
              { id: "sold_or_rented", label: "Đã bán / Cho thuê", count: stats.sold_or_rented_count },
              { id: "hidden", label: "Tạm ẩn", count: stats.hidden_listings },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => handleTabChange(tab.id)}
                className={`flex shrink-0 items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition ${
                  currentTab === tab.id
                    ? "bg-blue-600 text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                    currentTab === tab.id
                      ? "bg-blue-700 text-white"
                      : "bg-slate-100 text-slate-500 dark:bg-slate-800"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
            <input
              type="text"
              placeholder="Tìm theo tiêu đề hoặc địa chỉ..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white py-2 pl-9 pr-8 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            />
            <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            {searchKeyword && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-2.5 top-2 rounded-full p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </form>
        </div>

        {/* Listings List / Table */}
        <div className="mt-6 space-y-4">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="flex h-36 animate-pulse rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <div className="aspect-16/10 h-full rounded-xl bg-slate-200 dark:bg-slate-800" />
                  <div className="ml-4 flex-1 space-y-3">
                    <div className="h-4 w-2/3 rounded bg-slate-200 dark:bg-slate-800" />
                    <div className="h-3 w-1/3 rounded bg-slate-200 dark:bg-slate-800" />
                    <div className="h-3 w-1/2 rounded bg-slate-200 dark:bg-slate-800" />
                  </div>
                </div>
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-3xl border border-slate-200/80 bg-white p-12 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <Building2 className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700" />
              <h3 className="mt-4 text-base font-bold text-slate-800 dark:text-white">Chưa có tin đăng nào</h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {urlQ
                  ? "Không tìm thấy tin phù hợp với từ khóa tìm kiếm."
                  : "Bắt đầu tiếp cận hàng ngàn khách hàng tiềm năng bằng cách đăng tin bất động sản đầu tiên."}
              </p>
              <Link
                href="/properties/create"
                className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/20 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                <span>Đăng tin ngay</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => {
                const isSold = item.status === "sold" || item.status === "rented";
                const isHidden = item.status === "hidden" || !item.is_visible;
                const isActive = item.status === "active" && item.is_visible;

                return (
                  <div
                    key={item.id}
                    className="flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xs transition hover:border-slate-300 hover:shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:flex-row"
                  >
                    {/* Thumbnail 16:10 */}
                    <div className="relative aspect-16/10 w-full shrink-0 overflow-hidden bg-slate-100 sm:w-60 dark:bg-slate-800">
                      <Image
                        src={item.images?.[0] || getPlaceholderImage(item.property_type)}
                        alt={item.title}
                        fill
                        className="object-cover"
                      />
                      {/* Listing Type Tag */}
                      <span className="absolute left-2.5 top-2.5 rounded-md bg-slate-900/85 px-2 py-0.5 text-[10px] font-bold text-white backdrop-blur-xs">
                        {item.listing_type === "sale" ? "Mua bán" : "Cho thuê"}
                      </span>
                    </div>

                    {/* Content Body */}
                    <div className="flex flex-1 flex-col justify-between p-4 sm:p-5">
                      <div className="space-y-1.5">
                        {/* Status Badge & Code */}
                        <div className="flex flex-wrap items-center gap-2">
                          {isActive && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                              Đang hiển thị
                            </span>
                          )}
                          {isSold && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-950/60 dark:text-purple-400">
                              <Sparkles className="h-3 w-3" />
                              {item.status === "sold" ? "Đã bán" : "Đã cho thuê"}
                            </span>
                          )}
                          {isHidden && !isSold && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                              <EyeOff className="h-3 w-3" />
                              Tạm ẩn
                            </span>
                          )}

                          <span className="text-[10px] text-slate-400">
                            Mã tin: #{item.id.slice(0, 8).toUpperCase()}
                          </span>
                        </div>

                        {/* Title */}
                        <div className="flex items-start justify-between gap-2">
                          <Link
                            href={`/properties/${item.id}`}
                            target="_blank"
                            className="group flex items-center gap-1 text-sm font-bold text-slate-900 transition hover:text-blue-600 dark:text-white dark:hover:text-blue-400 sm:text-base"
                          >
                            <span className="line-clamp-1">{item.title}</span>
                            <ExternalLink className="h-3.5 w-3.5 shrink-0 opacity-40 group-hover:opacity-100" />
                          </Link>
                        </div>

                        {/* Price & Specs */}
                        <div className="flex flex-wrap items-baseline gap-3">
                          <span className="text-sm font-extrabold text-blue-600 dark:text-blue-400 sm:text-base">
                            {formatPrice(item.price, item.currency, item.listing_type)}
                          </span>
                          <span className="text-xs text-slate-500">•</span>
                          <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                            {item.area_sqm} m²
                          </span>
                          {item.num_bedrooms && (
                            <>
                              <span className="text-xs text-slate-500">•</span>
                              <span className="text-xs text-slate-600 dark:text-slate-300">
                                {item.num_bedrooms} PN
                              </span>
                            </>
                          )}
                        </div>

                        {/* Address */}
                        <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                          <MapPin className="h-3 w-3 shrink-0 text-slate-400" />
                          <span className="line-clamp-1">
                            {[item.ward, item.district, item.city].filter(Boolean).join(", ")}
                          </span>
                        </div>
                      </div>

                      {/* Footer Info & Action Bar */}
                      <div className="mt-4 flex flex-col justify-between gap-3 border-t border-slate-100 pt-3 dark:border-slate-800 lg:flex-row lg:items-center">
                        {/* Metrics */}
                        <div className="flex items-center gap-4 text-[11px] text-slate-400">
                          <span className="flex items-center gap-1" title="Lượt xem">
                            <Eye className="h-3.5 w-3.5 text-blue-500" />
                            <span>{item.view_count.toLocaleString("vi-VN")} xem</span>
                          </span>
                          <span className="flex items-center gap-1" title="Lượt lưu tin">
                            <Heart className="h-3.5 w-3.5 text-rose-500" />
                            <span>{item.favorites_count} lưu</span>
                          </span>
                          <span className="flex items-center gap-1 text-[10px]">
                            <Calendar className="h-3 w-3" />
                            <span>Làm mới: {formatDate(item.refreshed_at)}</span>
                          </span>
                        </div>

                        {/* Action Buttons Toolbar */}
                        <div className="flex flex-wrap items-center gap-1.5">
                          {/* Đẩy tin */}
                          <button
                            type="button"
                            disabled={actionLoadingId === item.id || isSold}
                            onClick={() => handleRefreshListing(item)}
                            title="Đẩy tin lên đầu trang danh sách"
                            className="inline-flex items-center gap-1 rounded-xl border border-amber-200 bg-amber-50/80 px-2.5 py-1.5 text-xs font-bold text-amber-800 transition hover:bg-amber-100 disabled:opacity-40 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300"
                          >
                            <Rocket className={`h-3.5 w-3.5 ${actionLoadingId === item.id ? "animate-spin" : ""}`} />
                            <span>Đẩy tin</span>
                          </button>

                          {/* Chỉnh sửa */}
                          <Link
                            href={`/properties/${item.id}/edit`}
                            title="Chỉnh sửa nội dung & hình ảnh tin"
                            className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                            <span>Sửa</span>
                          </Link>

                          {/* Ẩn / Bật lại */}
                          {!isSold && (
                            <button
                              type="button"
                              disabled={actionLoadingId === item.id}
                              onClick={() => handleToggleVisibility(item)}
                              title={item.is_visible ? "Tạm ẩn tin khỏi tìm kiếm" : "Bật hiển thị lại tin đăng"}
                              className={`inline-flex items-center gap-1 rounded-xl border px-2.5 py-1.5 text-xs font-semibold transition ${
                                item.is_visible
                                  ? "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300"
                                  : "border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 dark:border-blue-900/60 dark:bg-blue-950/60 dark:text-blue-300"
                              }`}
                            >
                              {item.is_visible ? (
                                <>
                                  <EyeOff className="h-3.5 w-3.5" />
                                  <span>Ẩn tin</span>
                                </>
                              ) : (
                                <>
                                  <Eye className="h-3.5 w-3.5" />
                                  <span>Hiện tin</span>
                                </>
                              )}
                            </button>
                          )}

                          {/* Đánh dấu đã bán */}
                          {!isSold && (
                            <button
                              type="button"
                              disabled={actionLoadingId === item.id}
                              onClick={() => handleMarkSold(item)}
                              title="Đánh dấu tin đã hoàn thành giao dịch"
                              className="inline-flex items-center gap-1 rounded-xl border border-purple-200 bg-purple-50/80 px-2.5 py-1.5 text-xs font-bold text-purple-700 transition hover:bg-purple-100 dark:border-purple-900/50 dark:bg-purple-950/40 dark:text-purple-300"
                            >
                              <Tag className="h-3.5 w-3.5" />
                              <span>{item.listing_type === "rent" ? "Đã cho thuê" : "Đã bán"}</span>
                            </button>
                          )}

                          {/* Xóa tin */}
                          <button
                            type="button"
                            onClick={() => {
                              setItemToDelete(item);
                              setDeleteModalOpen(true);
                            }}
                            title="Xóa vĩnh viễn tin đăng"
                            className="inline-flex items-center gap-1 rounded-xl border border-rose-200 bg-rose-50/80 px-2 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-400"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-6">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-40 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((num) => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setPage(num)}
                      className={`flex h-9 min-w-9 items-center justify-center rounded-xl px-2 text-xs font-bold transition ${
                        page === num
                          ? "bg-blue-600 text-white shadow-xs"
                          : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                      }`}
                    >
                      {num}
                    </button>
                  ))}
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-40 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal xác nhận xóa tin đăng an toàn */}
      {deleteModalOpen && itemToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 text-rose-600 dark:bg-rose-950 dark:text-rose-400">
              <AlertTriangle className="h-6 w-6" />
            </div>

            <h3 className="mt-4 text-base font-extrabold text-slate-900 dark:text-white">
              Xác nhận xóa tin đăng?
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Bạn có chắc chắn muốn xóa tin: <strong>"{itemToDelete.title}"</strong>?
              Thao tác này sẽ xóa vĩnh viễn tin đăng cùng toàn bộ hình ảnh và không thể hoàn tác.
            </p>

            <div className="mt-6 flex items-center justify-end gap-2.5">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => {
                  setDeleteModalOpen(false);
                  setItemToDelete(null);
                }}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleConfirmDelete}
                className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-rose-700 disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <RotateCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Đang xóa...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Xác nhận xóa</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MyListingsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        </div>
      }
    >
      <MyListingsContent />
    </Suspense>
  );
}
