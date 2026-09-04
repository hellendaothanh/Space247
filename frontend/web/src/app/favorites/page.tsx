"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Heart, Home, ArrowLeft, Loader2, RefreshCw } from "lucide-react";
import { PropertyResponse } from "@shared/types";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/favorites";
import PropertyCard from "@/components/PropertyCard";

export default function FavoritesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { isFavorite } = useFavorites();
  const [favorites, setFavorites] = useState<PropertyResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const displayFavorites = favorites.filter((p) => isFavorite(p.id));

  const fetchFavorites = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listFavorites({ limit: 100 });
      setFavorites(data);
    } catch (err: any) {
      setError(err?.message || "Không thể tải danh sách bất động sản đã lưu.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading) {
      if (user) {
        fetchFavorites();
      } else {
        setLoading(false);
      }
    }
  }, [user, authLoading, fetchFavorites]);

  if (authLoading) {
    return (
      <div className="flex min-h-[450px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md text-center py-16 px-4">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50 text-rose-500">
          <Heart className="h-8 w-8 fill-rose-500/20" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Đăng nhập để xem danh sách yêu thích</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vui lòng đăng nhập tài khoản để lưu trữ và theo dõi các tin bất động sản bạn quan tâm.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link
            href="/login?redirect=/favorites"
            className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition"
          >
            Đăng nhập ngay
          </Link>
          <Link
            href="/"
            className="inline-flex items-center rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100 transition"
          >
            Khám phá nhà đất
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/" className="hover:text-blue-600 transition flex items-center gap-1">
              <Home className="h-3 w-3" /> Trang chủ
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">Tin đã lưu</span>
          </div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-600">
              <Heart className="h-5 w-5 fill-rose-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Bất Động Sản Đã Lưu</h1>
              <p className="text-xs text-slate-500">
                {displayFavorites.length} bất động sản trong bộ sưu tập yêu thích của bạn
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchFavorites}
          disabled={loading}
          className="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition cursor-pointer shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Làm mới</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex min-h-[300px] flex-col items-center justify-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm text-slate-500">Đang tải các tin bất động sản đã lưu...</p>
        </div>
      ) : displayFavorites.length === 0 ? (
        /* Empty State */
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-16 px-6 text-center shadow-xs">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50 text-rose-400">
            <Heart className="h-8 w-8 stroke-1" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Bạn chưa lưu bất động sản nào</h3>
          <p className="mt-1.5 text-xs text-slate-500 max-w-md mx-auto">
            Nhấp vào biểu tượng trái tim trên bất kỳ tin đăng nào để lưu lại và dễ dàng xem lại bất kỳ lúc nào.
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Khám phá bất động sản ngay</span>
            </Link>
          </div>
        </div>
      ) : (
        /* Property Grid */
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {displayFavorites.map((property, idx) => (
            <PropertyCard key={property.id} item={property} index={idx} />
          ))}
        </div>
      )}
    </div>
  );
}
