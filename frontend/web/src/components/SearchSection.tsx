"use client";

import { useState } from "react";
import { Search, Compass, Filter, SlidersHorizontal, Loader2 } from "lucide-react";
import { ListingType, PropertyType } from "@shared/types";

export interface FilterState {
  query: string;
  listing_type?: ListingType;
  property_type?: PropertyType;
  min_price?: number;
  max_price?: number;
  city?: string;
  enable_hybrid: boolean;
}

interface SearchSectionProps {
  onSearch: (filters: FilterState) => void;
  isLoading: boolean;
  totalResults?: number;
}

export default function SearchSection({ onSearch, isLoading, totalResults }: SearchSectionProps) {
  const [query, setQuery] = useState("");
  const [listingType, setListingType] = useState<ListingType | undefined>(undefined);
  const [propertyType, setPropertyType] = useState<PropertyType | undefined>(undefined);
  const [city, setCity] = useState<string | undefined>(undefined);
  const [priceRange, setPriceRange] = useState<string>("all");
  const [enableHybrid, setEnableHybrid] = useState(true);

  const handlePriceChange = (val: string) => {
    setPriceRange(val);
  };

  const getPriceBounds = (val: string): { min?: number; max?: number } => {
    switch (val) {
      case "under_2b":
        return { max: 2_000_000_000 };
      case "2b_5b":
        return { min: 2_000_000_000, max: 5_000_000_000 };
      case "5b_10b":
        return { min: 5_000_000_000, max: 10_000_000_000 };
      case "above_10b":
        return { min: 10_000_000_000 };
      default:
        return {};
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const bounds = getPriceBounds(priceRange);
    onSearch({
      query: query.trim(),
      listing_type: listingType,
      property_type: propertyType,
      city: city || undefined,
      min_price: bounds.min,
      max_price: bounds.max,
      enable_hybrid: enableHybrid,
    });
  };

  const sampleQueries = [
    "Căn hộ 2 phòng ngủ view sông Sài Gòn",
    "Nhà phố mặt tiền kinh doanh Cầu Giấy Hà Nội",
    "Biệt thự sân vườn hồ bơi Thảo Điền",
    "Chung cư cao cấp 3PN cạnh Metro",
  ];

  return (
    <div className="relative overflow-hidden rounded-3xl bg-linear-to-b from-blue-900 via-indigo-950 to-slate-900 px-6 py-12 sm:px-12 sm:py-20 text-white shadow-2xl">
      {/* Decorative gradient blur balls */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-purple-500/20 blur-3xl" />

      <div className="relative mx-auto max-w-4xl text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-blue-300 backdrop-blur-md">
          <Compass className="h-3.5 w-3.5 text-blue-400" />
          <span>Tìm kiếm thông minh với Vector Embedding 768 chiều & PostGIS</span>
        </div>

        <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-5xl text-white">
          Tìm ngôi nhà mơ ước bằng ngôn ngữ tự nhiên
        </h1>
        <p className="mt-3 text-sm sm:text-base text-slate-300 max-w-2xl mx-auto">
          Mô tả không gian sống lý tưởng của bạn như cách bạn trao đổi với một chuyên viên bất động sản am hiểu thị trường.
        </p>

        {/* Search Box Form */}
        <form onSubmit={handleSubmit} className="mt-8">
          <div className="flex flex-col gap-3 sm:flex-row items-center rounded-2xl bg-white/10 p-2 backdrop-blur-xl border border-white/20 shadow-2xl">
            <div className="relative flex-1 w-full flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Tìm kiếm bất động sản"
                placeholder="Nhập yêu cầu: 'Căn hộ 2PN ban công view sông Bình Thạnh'..."
                className="w-full rounded-xl bg-transparent py-3.5 pl-12 pr-4 text-sm sm:text-base text-white placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-400"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/40 hover:bg-blue-500 active:scale-[0.98] transition disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Đang phân tích...</span>
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 text-blue-200" />
                  <span>Tìm kiếm</span>
                </>
              )}
            </button>
          </div>

          {/* Sample Prompts */}
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-300">
            <span className="text-slate-400">Gợi ý:</span>
            {sampleQueries.map((sample, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setQuery(sample);
                  const bounds = getPriceBounds(priceRange);
                  onSearch({
                    query: sample,
                    listing_type: listingType,
                    property_type: propertyType,
                    city: city || undefined,
                    min_price: bounds.min,
                    max_price: bounds.max,
                    enable_hybrid: enableHybrid,
                  });
                }}
                className="rounded-full bg-white/10 px-3 py-1 text-slate-200 hover:bg-white/20 hover:text-white transition"
              >
                {sample}
              </button>
            ))}
          </div>

          {/* Quick Filters Bar */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3 rounded-2xl bg-white/5 p-4 border border-white/10 backdrop-blur-md">
            {/* Listing Type Filter */}
            <div className="flex rounded-lg bg-black/20 p-1 text-xs">
              <button
                type="button"
                onClick={() => setListingType(undefined)}
                className={`rounded-md px-3 py-1.5 transition ${
                  listingType === undefined ? "bg-blue-600 text-white font-semibold" : "text-slate-300 hover:text-white"
                }`}
              >
                Tất cả
              </button>
              <button
                type="button"
                onClick={() => setListingType("sale")}
                className={`rounded-md px-3 py-1.5 transition ${
                  listingType === "sale" ? "bg-blue-600 text-white font-semibold" : "text-slate-300 hover:text-white"
                }`}
              >
                Mua bán
              </button>
              <button
                type="button"
                onClick={() => setListingType("rent")}
                className={`rounded-md px-3 py-1.5 transition ${
                  listingType === "rent" ? "bg-emerald-600 text-white font-semibold" : "text-slate-300 hover:text-white"
                }`}
              >
                Cho thuê
              </button>
            </div>

            {/* Property Type Dropdown */}
            <select
              value={propertyType || ""}
              onChange={(e) => setPropertyType(e.target.value ? (e.target.value as PropertyType) : undefined)}
              aria-label="Loại bất động sản"
              className="rounded-lg bg-slate-800/80 px-3 py-1.5 text-xs text-white border border-white/15 focus:outline-hidden"
            >
              <option value="">Tất cả loại hình</option>
              <option value="apartment">Căn hộ chung cư</option>
              <option value="house">Nhà phố</option>
              <option value="villa">Biệt thự</option>
              <option value="land">Đất nền</option>
              <option value="commercial">Mặt bằng kinh doanh</option>
            </select>

            {/* City Dropdown */}
            <select
              value={city || ""}
              onChange={(e) => setCity(e.target.value || undefined)}
              aria-label="Khu vực thành phố"
              className="rounded-lg bg-slate-800/80 px-3 py-1.5 text-xs text-white border border-white/15 focus:outline-hidden"
            >
              <option value="">Toàn quốc</option>
              <option value="Thành phố Hồ Chí Minh">TP. Hồ Chí Minh</option>
              <option value="Thành phố Hà Nội">Hà Nội</option>
            </select>

            {/* Price Range Dropdown */}
            <select
              value={priceRange}
              onChange={(e) => handlePriceChange(e.target.value)}
              aria-label="Khoảng giá"
              className="rounded-lg bg-slate-800/80 px-3 py-1.5 text-xs text-white border border-white/15 focus:outline-hidden"
            >
              <option value="all">Mọi mức giá</option>
              <option value="under_2b">Dưới 2 tỷ</option>
              <option value="2b_5b">2 tỷ - 5 tỷ</option>
              <option value="5b_10b">5 tỷ - 10 tỷ</option>
              <option value="above_10b">Trên 10 tỷ</option>
            </select>

            {/* Hybrid Search Toggle */}
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer ml-1">
              <input
                type="checkbox"
                checked={enableHybrid}
                onChange={(e) => setEnableHybrid(e.target.checked)}
                className="h-3.5 w-3.5 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500"
              />
              <span>Hybrid Search (Vector + FTS)</span>
            </label>
          </div>
        </form>
      </div>
    </div>
  );
}
