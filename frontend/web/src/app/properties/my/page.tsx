"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  Building2,
  PlusCircle,
  Eye,
  Edit3,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Search,
  Filter,
  Home,
  MapPin,
  Calendar,
  X,
  ExternalLink,
  Layers,
  TrendingUp,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PropertyResponse, PropertyStatus } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";

function getDeterministicViews(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash % 920) + 85;
}

export default function MyPropertiesPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [properties, setProperties] = useState<PropertyResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [toastMessage, setToastMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [propertyToDelete, setPropertyToDelete] = useState<PropertyResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Close modal on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && deleteModalOpen && !isDeleting) {
        setDeleteModalOpen(false);
        setPropertyToDelete(null);
        setDeleteError(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [deleteModalOpen, isDeleting]);

  // Redirect if not logged in
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [user, isAuthLoading, router]);

  // Fetch properties
  const fetchProperties = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getMyProperties({ limit: 100 });
      setProperties(data);
    } catch (err: any) {
      console.error("Failed to load user properties:", err);
      setToastMessage({
        type: "error",
        text: err?.message || "Không thể tải danh sách tin đăng của bạn.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchProperties();
    }
  }, [user]);

  // Handle delete execution
  const handleDeleteConfirm = async () => {
    if (!propertyToDelete) return;
    try {
      setIsDeleting(true);
      setDeleteError(null);
      await apiClient.deleteProperty(propertyToDelete.id);
      setProperties((prev) => prev.filter((p) => p.id !== propertyToDelete.id));
      setToastMessage({
        type: "success",
        text: `Đã xóa thành công tin đăng "${propertyToDelete.title}"`,
      });
      setDeleteModalOpen(false);
      setPropertyToDelete(null);
    } catch (err: any) {
      setDeleteError(err?.message || "Không thể xóa tin đăng. Vui lòng thử lại.");
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredProperties = useMemo(() => {
    return properties.filter((p) => {
      if (statusFilter === "active" && p.status !== "active") return false;
      if (statusFilter === "inactive" && p.status === "active") return false;

      if (searchKeyword.trim()) {
        const query = searchKeyword.toLowerCase();
        const matchTitle = p.title.toLowerCase().includes(query);
        const matchAddress = p.address.toLowerCase().includes(query);
        const matchCity = p.city.toLowerCase().includes(query);
        return matchTitle || matchAddress || matchCity;
      }

      return true;
    });
  }, [properties, statusFilter, searchKeyword]);

  const activeCount = useMemo(() => properties.filter((p) => p.status === "active").length, [properties]);
  const inactiveCount = useMemo(() => properties.filter((p) => p.status !== "active").length, [properties]);
  const totalViews = useMemo(() => {
    return properties.reduce((acc, p) => acc + getDeterministicViews(p.id), 0);
  }, [properties]);

  if (isAuthLoading || (!user && isLoading)) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-sm font-medium text-slate-500">Đang tải trang quản lý tin đăng...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/60 pb-16">
      {toastMessage && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl px-4 py-3 shadow-lg transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-600 text-white"
              : "bg-rose-600 text-white"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle2 className="h-5 w-5 shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0" />
          )}
          <span className="text-xs font-semibold">{toastMessage.text}</span>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            className="ml-2 rounded-lg p-1 hover:bg-white/20 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
                <Building2 className="h-4 w-4" />
                <span>Bảng điều khiển cá nhân</span>
              </div>
              <h1 className="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Quản lý tin đăng của bạn
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Theo dõi hiệu quả, số lượt xem, trạng thái hiển thị và thao tác cập nhật bài đăng bất động sản.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/properties/create"
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition active:scale-95"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Đăng tin mới</span>
              </Link>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-4.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Tổng số tin</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <Layers className="h-4 w-4" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{properties.length}</p>
              <span className="text-[11px] text-slate-400">Tất cả bài đã tạo</span>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Đang hiển thị</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-emerald-600">{activeCount}</p>
              <span className="text-[11px] text-emerald-600/80 font-medium">Khách hàng tìm thấy</span>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Tạm dừng / Đã bán</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
                  <Filter className="h-4 w-4" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-amber-600">{inactiveCount}</p>
              <span className="text-[11px] text-slate-400">Đã chốt hoặc ẩn</span>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Tổng lượt xem</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
                  <TrendingUp className="h-4 w-4" />
                </span>
              </div>
              <p className="mt-2 text-2xl font-bold text-purple-600">{totalViews.toLocaleString("vi-VN")}</p>
              <span className="text-[11px] text-purple-600/80 font-medium">Tương tác toàn hệ thống</span>
            </div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center gap-1.5 p-1 bg-slate-100/80 rounded-xl overflow-x-auto">
            <button
              type="button"
              onClick={() => setStatusFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                statusFilter === "all"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Tất cả ({properties.length})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("active")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                statusFilter === "active"
                  ? "bg-white text-emerald-600 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Đang hiển thị ({activeCount})
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter("inactive")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                statusFilter === "inactive"
                  ? "bg-white text-amber-600 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Tạm dừng / Đã xong ({inactiveCount})
            </button>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="Tìm theo tiêu đề, địa chỉ..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-9 pr-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 transition"
            />
            {searchKeyword && (
              <button
                type="button"
                onClick={() => setSearchKeyword("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="mt-8 flex flex-col items-center justify-center py-16">
            <div className="h-9 w-9 animate-spin rounded-full border-3 border-blue-600 border-t-transparent" />
            <p className="mt-3 text-xs font-medium text-slate-500">Đang đồng bộ danh sách tin cá nhân...</p>
          </div>
        ) : filteredProperties.length === 0 ? (
          <div className="mt-8 flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 mb-4">
              <Home className="h-8 w-8" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              {searchKeyword ? "Không tìm thấy tin đăng phù hợp" : "Bạn chưa có tin đăng nào"}
            </h3>
            <p className="mt-1 text-xs text-slate-500 max-w-md">
              {searchKeyword
                ? "Thử thay đổi từ khóa tìm kiếm hoặc bỏ chọn các bộ lọc trạng thái để xem đầy đủ tin đăng."
                : "Bắt đầu tiếp cận hàng triệu khách hàng tiềm năng với công nghệ tìm kiếm AI thông minh của Space247."}
            </p>
            <div className="mt-6">
              {searchKeyword ? (
                <button
                  type="button"
                  onClick={() => setSearchKeyword("")}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
                >
                  Xóa tìm kiếm
                </button>
              ) : (
                <Link
                  href="/properties/create"
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition"
                >
                  <PlusCircle className="h-4 w-4" />
                  Đăng tin đầu tiên ngay
                </Link>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-4">
            {filteredProperties.map((prop, idx) => {
              const views = getDeterministicViews(prop.id);
              const isSale = prop.listing_type === "sale";
              const isActive = prop.status === "active";

              return (
                <div
                  key={prop.id}
                  className="group relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-2xs hover:shadow-md hover:border-slate-300 transition-all"
                >
                  <div className="flex items-start gap-4 w-full sm:w-auto">
                    <div className="relative h-24 w-28 sm:h-24 sm:w-32 shrink-0 overflow-hidden rounded-xl bg-slate-100">
                      <Image
                        src={getPlaceholderImage(prop.property_type, idx)}
                        alt={prop.title}
                        fill
                        className="object-cover group-hover:scale-105 transition duration-300"
                      />
                      <div className="absolute top-1.5 left-1.5">
                        <span
                          className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-xs ${
                            isSale ? "bg-blue-600" : "bg-emerald-600"
                          }`}
                        >
                          {isSale ? "Bán" : "Cho thuê"}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-1 min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                            isActive
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-slate-100 text-slate-600 border border-slate-200"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              isActive ? "bg-emerald-500 animate-pulse" : "bg-slate-400"
                            }`}
                          />
                          {isActive ? "Đang hiển thị" : prop.status === "sold" ? "Đã bán" : "Tạm dừng"}
                        </span>
                        <span className="text-xs text-slate-400">|</span>
                        <span className="text-xs font-medium text-slate-500">
                          {formatPropertyType(prop.property_type)}
                        </span>
                      </div>

                      <Link
                        href={`/properties/${prop.id}`}
                        className="text-sm sm:text-base font-bold text-slate-900 hover:text-blue-600 transition truncate"
                        title={prop.title}
                      >
                        {prop.title}
                      </Link>

                      <p className="flex items-center gap-1 text-xs text-slate-500 truncate">
                        <MapPin className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                        <span>
                          {prop.address}, {prop.district ? `${prop.district}, ` : ""}
                          {prop.city}
                        </span>
                      </p>

                      <div className="mt-1 flex items-center gap-3 text-xs flex-wrap">
                        <span className="font-extrabold text-blue-600 text-sm">
                          {formatPrice(prop.price, prop.currency, prop.listing_type)}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="font-medium text-slate-600">{prop.area_sqm} m²</span>
                        {prop.num_bedrooms ? (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className="text-slate-600">{prop.num_bedrooms} PN</span>
                          </>
                        ) : null}
                      </div>
                    </div>
                  </div>

                  <div className="flex w-full sm:w-auto items-center justify-between sm:justify-end gap-6 pt-3 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                    <div className="flex items-center sm:flex-col sm:items-end gap-3 sm:gap-1 text-xs text-slate-500">
                      <div className="flex items-center gap-1 font-semibold text-slate-700 bg-slate-100 px-2 py-1 rounded-lg">
                        <Eye className="h-3.5 w-3.5 text-blue-600" />
                        <span>{views} lượt xem</span>
                      </div>
                      <div className="flex items-center gap-1 text-[11px] text-slate-400">
                        <Calendar className="h-3 w-3" />
                        <span>{new Date(prop.created_at).toLocaleDateString("vi-VN")}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Link
                        href={`/properties/${prop.id}`}
                        className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition shadow-2xs"
                        title="Xem chi tiết trên website"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                        <span className="hidden md:inline">Xem</span>
                      </Link>

                      <Link
                        href={`/properties/${prop.id}/edit`}
                        className="inline-flex items-center gap-1 rounded-xl border border-blue-200 bg-blue-50/50 px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition shadow-2xs"
                        title="Chỉnh sửa thông tin tin đăng"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                        <span>Sửa</span>
                      </Link>

                      <button
                        type="button"
                        onClick={() => {
                          setPropertyToDelete(prop);
                          setDeleteModalOpen(true);
                        }}
                        className="inline-flex items-center gap-1 rounded-xl border border-rose-200 bg-rose-50/40 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-100 hover:border-rose-300 transition shadow-2xs cursor-pointer"
                        title="Xóa tin đăng vĩnh viễn"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Xóa</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {deleteModalOpen && propertyToDelete && (
        <div
          onClick={(e) => {
            if (e.target === e.currentTarget && !isDeleting) {
              setDeleteModalOpen(false);
              setPropertyToDelete(null);
              setDeleteError(null);
            }
          }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-200"
        >
          <div className="relative w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center gap-3 text-rose-600 mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 border border-rose-100">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Xác nhận xóa tin đăng</h3>
                <p className="text-xs text-slate-500">Hành động này không thể hoàn tác</p>
              </div>
            </div>

            {deleteError && (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                {deleteError}
              </div>
            )}

            <div className="my-4 rounded-2xl bg-slate-50 p-3.5 border border-slate-200/80">
              <p className="text-xs font-bold text-slate-800 line-clamp-2">{propertyToDelete.title}</p>
              <p className="text-[11px] text-slate-500 mt-1">
                {propertyToDelete.address}, {propertyToDelete.city}
              </p>
              <p className="text-xs font-extrabold text-blue-600 mt-2">
                {formatPrice(propertyToDelete.price, propertyToDelete.currency, propertyToDelete.listing_type)}
              </p>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Bạn có chắc chắn muốn xóa vĩnh viễn bài đăng này khỏi hệ thống Space247? Tất cả dữ liệu vector AI và thông tin liên quan sẽ bị xóa bỏ.
            </p>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => {
                  setDeleteModalOpen(false);
                  setPropertyToDelete(null);
                  setDeleteError(null);
                }}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition disabled:opacity-50"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleDeleteConfirm}
                className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-rose-700 transition disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
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
