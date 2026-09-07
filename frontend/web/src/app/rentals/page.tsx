"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Search,
  SlidersHorizontal,
  Home,
  Building2,
  Sparkles,
  MapPin,
  CheckCircle,
  Clock,
  PawPrint,
  Layers,
  X,
  BedDouble,
  DollarSign,
  ChevronRight,
  ShieldCheck,
  DoorOpen,
} from "lucide-react";
import type {
  RentalProperty,
  RentalPropertyModel,
  RentalSearchFilterQuery,
  RentalUnitFurnishing,
} from "@shared/types";
import { apiClient } from "@/lib/api";

const propertyModelOptions: { id: RentalPropertyModel | ""; label: string; icon: any; hint: string }[] = [
  { id: "", label: "Tất cả", icon: Home, hint: "Tất cả loại hình" },
  { id: "boarding_house", label: "Phòng trọ", icon: DoorOpen, hint: "Thuê tháng giá rẻ" },
  { id: "serviced_apartment", label: "Căn hộ dịch vụ", icon: Building2, hint: "Full nội thất cao cấp" },
  { id: "homestay", label: "Homestay", icon: Sparkles, hint: "Thuê theo ngày / trải nghiệm" },
];

export default function RentalsDiscoveryPage() {
  const [items, setItems] = useState<RentalProperty[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  
  // Search query state
  const [keyword, setKeyword] = useState("");
  const [selectedModel, setSelectedModel] = useState<RentalPropertyModel | "">("");
  
  // Advanced Filter Drawer State
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [furnishing, setFurnishing] = useState<RentalUnitFurnishing | "">("");
  const [hasMezzanine, setHasMezzanine] = useState<boolean | null>(null);
  const [hasPrivateBathroom, setHasPrivateBathroom] = useState<boolean | null>(null);
  const [allowPets, setAllowPets] = useState<boolean | null>(null);
  const [fingerprintLock, setFingerprintLock] = useState<boolean | null>(null);
  const [curfewFree, setCurfewFree] = useState<boolean | null>(null);
  const [onlyAvailable, setOnlyAvailable] = useState<boolean>(true);

  async function fetchRentals() {
    setBusy(true);
    setError("");
    try {
      const params: RentalSearchFilterQuery = {
        limit: 50,
        query: keyword.trim() || undefined,
        property_model: selectedModel ? selectedModel : undefined,
        min_price: minPrice ? Number(minPrice) : undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
        furnishing: furnishing ? furnishing : undefined,
        has_mezzanine: hasMezzanine !== null ? hasMezzanine : undefined,
        has_private_bathroom: hasPrivateBathroom !== null ? hasPrivateBathroom : undefined,
        allow_pets: allowPets !== null ? allowPets : undefined,
        fingerprint_lock: fingerprintLock !== null ? fingerprintLock : undefined,
        curfew: curfewFree !== null ? !curfewFree : undefined, // curfewFree means curfew == false
        only_available: onlyAvailable,
      };
      const results = await apiClient.listRentals(params);
      setItems(results);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tải danh sách cho thuê");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    fetchRentals();
  }, [selectedModel]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRentals();
  };

  const activeFiltersCount = [
    minPrice,
    maxPrice,
    furnishing,
    hasMezzanine !== null,
    hasPrivateBathroom !== null,
    allowPets !== null,
    fingerprintLock !== null,
    curfewFree !== null,
    onlyAvailable,
  ].filter(Boolean).length;

  const resetFilters = () => {
    setMinPrice("");
    setMaxPrice("");
    setFurnishing("");
    setHasMezzanine(null);
    setHasPrivateBathroom(null);
    setAllowPets(null);
    setFingerprintLock(null);
    setCurfewFree(null);
    setOnlyAvailable(true);
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header & Channel Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="rounded-full bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1">
              Phân hệ cho thuê thông minh
            </span>
            <span className="text-slate-400 text-xs">•</span>
            <span className="text-slate-500 text-xs">Mô hình Host & Tenant</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Khám phá Phòng trọ, Căn hộ dịch vụ & Homestay
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Minh bạch chi phí điện nước, xem trước phòng còn trống thực tế, đặt lịch hẹn trực tiếp với Chủ nhà
          </p>
        </div>

        {/* Host Channel CTA */}
        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/host/rentals"
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition"
          >
            <DoorOpen className="h-4 w-4 text-emerald-400" />
            <span>Kênh Chủ Nhà (Host)</span>
          </Link>
          <Link
            href="/rentals/my-inquiries"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
          >
            <Clock className="h-4 w-4 text-blue-600" />
            <span>Lịch hẹn xem phòng</span>
          </Link>
        </div>
      </div>

      {/* Clean Modern Search Bar */}
      <section className="space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Nhập khu vực, quận huyện, trường ĐH hoặc tên khu trọ (VD: Bách Khoa, Cầu Giấy, Q7)..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-4 py-3.5 text-sm font-medium text-slate-800 placeholder-slate-400 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-100 transition"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              className={`inline-flex items-center gap-2 rounded-2xl border px-5 py-3.5 text-sm font-semibold transition ${
                activeFiltersCount > 0
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              <SlidersHorizontal className="h-4 w-4" />
              <span>Bộ lọc nâng cao</span>
              {activeFiltersCount > 0 && (
                <span className="rounded-full bg-blue-600 text-white text-[10px] w-5 h-5 flex items-center justify-center font-bold">
                  {activeFiltersCount}
                </span>
              )}
            </button>

            <button
              type="submit"
              disabled={busy}
              className="rounded-2xl bg-blue-600 px-6 py-3.5 text-sm font-bold text-white shadow-xs hover:bg-blue-700 transition disabled:opacity-50"
            >
              {busy ? "Đang tìm..." : "Tìm kiếm"}
            </button>
          </div>
        </form>

        {/* Quick Model Tabs (Pills) */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {propertyModelOptions.map((opt) => {
            const Icon = opt.icon;
            const active = selectedModel === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => setSelectedModel(opt.id)}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold whitespace-nowrap transition ${
                  active
                    ? "bg-blue-600 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{opt.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Results Header */}
      <div className="flex items-center justify-between text-sm text-slate-600">
        <p>
          Tìm thấy <strong className="text-slate-900 font-bold">{items.length}</strong> khu chỗ ở phù hợp
        </p>
        {busy && <span className="text-blue-600 font-medium animate-pulse">Đang cập nhật kết quả...</span>}
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 p-4 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Property Cards Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((property) => {
          const isHomestay = property.property_model === "homestay";
          const priceUnit = isHomestay ? "/đêm" : "/tháng";
          const coverImage =
            property.images?.[0] ||
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80";

          return (
            <div
              key={property.id}
              className="group relative flex flex-col overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-xs transition duration-300 hover:-translate-y-1 hover:shadow-xl"
            >
              {/* Image & Badge Header */}
              <div className="relative aspect-16/10 w-full overflow-hidden bg-slate-100">
                <img
                  src={coverImage}
                  alt={property.name}
                  className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-slate-900/80 px-2.5 py-1 text-xs font-bold text-white backdrop-blur-xs">
                    {property.property_model === "homestay"
                      ? "Homestay"
                      : property.property_model === "serviced_apartment"
                      ? "Căn hộ dịch vụ"
                      : "Nhà trọ"}
                  </span>
                  {property.available_units_count > 0 ? (
                    <span className="rounded-full bg-emerald-600 px-2.5 py-1 text-xs font-bold text-white">
                      Còn {property.available_units_count} phòng trống
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-500 px-2.5 py-1 text-xs font-medium text-white">
                      Tạm hết phòng
                    </span>
                  )}
                </div>
              </div>

              {/* Card Body */}
              <div className="flex flex-1 flex-col p-5 space-y-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900 line-clamp-1 group-hover:text-blue-600 transition">
                    <Link href={`/rentals/${property.id}`}>{property.name}</Link>
                  </h3>
                  <p className="flex items-center gap-1 text-xs text-slate-500 mt-1 line-clamp-1">
                    <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                    <span>
                      {[property.address, property.ward, property.district, property.city]
                        .filter(Boolean)
                        .join(", ")}
                    </span>
                  </p>
                </div>

                {/* Shared Highlights Badges */}
                <div className="flex flex-wrap gap-1.5 text-[11px] font-medium text-slate-600">
                  {property.shared_rules?.curfew === false && (
                    <span className="rounded-md bg-blue-50 text-blue-700 px-2 py-0.5">Giờ giấc tự do</span>
                  )}
                  {property.shared_rules?.fingerprint_lock && (
                    <span className="rounded-md bg-emerald-50 text-emerald-700 px-2 py-0.5">Khóa vân tay</span>
                  )}
                  {property.shared_rules?.allow_pets && (
                    <span className="rounded-md bg-amber-50 text-amber-700 px-2 py-0.5">Nuôi thú cưng</span>
                  )}
                </div>

                {/* Price Range & CTA */}
                <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Giá phòng từ</span>
                    <div className="text-base font-extrabold text-blue-600">
                      {property.min_price != null
                        ? `${property.min_price.toLocaleString("vi-VN")} đ`
                        : "Liên hệ"}
                      <span className="text-xs font-normal text-slate-500">{priceUnit}</span>
                    </div>
                  </div>

                  <Link
                    href={`/rentals/${property.id}`}
                    className="inline-flex items-center gap-1 rounded-xl bg-blue-50 px-3.5 py-2 text-xs font-bold text-blue-700 hover:bg-blue-600 hover:text-white transition"
                  >
                    <span>Xem phòng</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Advanced Filter Drawer / Modal */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/50 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white p-6 shadow-2xl overflow-y-auto flex flex-col justify-between animate-in slide-in-from-right duration-200">
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="h-5 w-5 text-blue-600" />
                  <h2 className="text-lg font-bold text-slate-900">Bộ lọc nâng cao</h2>
                </div>
                <button
                  onClick={() => setDrawerOpen(false)}
                  className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Price Range */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Khoảng giá (VND)</label>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="number"
                    placeholder="Giá từ"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    className="rounded-xl border border-slate-200 p-2.5 text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Giá đến"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="rounded-xl border border-slate-200 p-2.5 text-sm"
                  />
                </div>
              </div>

              {/* Furnishing */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Mức độ nội thất</label>
                <select
                  value={furnishing}
                  onChange={(e) => setFurnishing(e.target.value as RentalUnitFurnishing)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-sm bg-white"
                >
                  <option value="">Tất cả</option>
                  <option value="empty">Phòng trống</option>
                  <option value="basic">Nội thất cơ bản</option>
                  <option value="full">Full nội thất cao cấp</option>
                </select>
              </div>

              {/* Room Amenities */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Tiện nghi phòng & tòa nhà</label>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasMezzanine === true}
                    onChange={(e) => setHasMezzanine(e.target.checked ? true : null)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm text-slate-700">Có gác lửng / gác xép</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasPrivateBathroom === true}
                    onChange={(e) => setHasPrivateBathroom(e.target.checked ? true : null)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm text-slate-700">Vệ sinh khép kín</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowPets === true}
                    onChange={(e) => setAllowPets(e.target.checked ? true : null)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm text-slate-700">Cho nuôi thú cưng</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={curfewFree === true}
                    onChange={(e) => setCurfewFree(e.target.checked ? true : null)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm text-slate-700">Giờ giấc tự do (không giới nghiêm)</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={fingerprintLock === true}
                    onChange={(e) => setFingerprintLock(e.target.checked ? true : null)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm text-slate-700">Cửa khóa vân tay an ninh</span>
                </label>
              </div>

              {/* Only Available toggle */}
              <div className="pt-3 border-t border-slate-100">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onlyAvailable}
                    onChange={(e) => setOnlyAvailable(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span className="text-sm font-semibold text-slate-900">Chỉ hiển thị khu còn phòng trống</span>
                </label>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="pt-6 border-t border-slate-100 flex items-center gap-3">
              <button
                type="button"
                onClick={resetFilters}
                className="flex-1 rounded-xl border border-slate-200 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition"
              >
                Đặt lại
              </button>
              <button
                type="button"
                onClick={() => {
                  setDrawerOpen(false);
                  fetchRentals();
                }}
                className="flex-1 rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 transition"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
