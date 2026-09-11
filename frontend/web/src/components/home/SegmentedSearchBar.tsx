"use client";

import { useState } from "react";
import { MapPin, Building2, Wallet, Search, SlidersHorizontal, Sparkles, Loader2 } from "lucide-react";
import type { PropertyType } from "@shared/types";

export type SearchMode = "sale" | "rent" | "projects";

export interface HomeSearchPayload {
  mode: SearchMode;
  location: string;
  propertyType?: PropertyType;
  rentalType?: "room" | "serviced_apartment" | "house_share" | "entire_house";
  projectKeyword?: string;
  minPrice?: number;
  maxPrice?: number;
  city?: string;
  minBedrooms?: number;
  minAreaSqm?: number;
  aiEnabled: boolean;
}

interface Props {
  onSearch: (payload: HomeSearchPayload) => void;
  isLoading?: boolean;
  initialMode?: SearchMode;
}

const MODE_TABS: { key: SearchMode; label: string }[] = [
  { key: "sale", label: "Mua Bán Nhà Đất" },
  { key: "rent", label: "Thuê Nhà & Phòng Trọ" },
  { key: "projects", label: "Dự Án Mới" },
];

const TYPE_OPTIONS: Record<SearchMode, { label: string; value: string }[]> = {
  sale: [
    { label: "Tất cả loại hình", value: "" },
    { label: "Nhà phố", value: "house" },
    { label: "Căn hộ", value: "apartment" },
    { label: "Đất nền", value: "land" },
    { label: "Biệt thự", value: "villa" },
    { label: "Mặt bằng / Shophouse", value: "commercial" },
  ],
  rent: [
    { label: "Tất cả loại hình", value: "" },
    { label: "Phòng trọ", value: "room" },
    { label: "Căn hộ dịch vụ", value: "serviced_apartment" },
    { label: "Ở ghép", value: "house_share" },
    { label: "Nhà nguyên căn", value: "entire_house" },
    { label: "Mặt bằng kinh doanh", value: "commercial" },
  ],
  projects: [
    { label: "Tất cả dự án", value: "" },
    { label: "Căn hộ cao cấp", value: "căn hộ" },
    { label: "Khu đô thị", value: "khu đô thị" },
    { label: "Nghỉ dưỡng", value: "nghỉ dưỡng" },
  ],
};

type PriceOption = { label: string; min?: number; max?: number };

const PRICE_OPTIONS: Record<SearchMode, PriceOption[]> = {
  sale: [
    { label: "Mức giá (tỷ)" },
    { label: "Dưới 1,5 tỷ", max: 1_500_000_000 },
    { label: "1,5 - 3 tỷ", min: 1_500_000_000, max: 3_000_000_000 },
    { label: "3 - 5 tỷ", min: 3_000_000_000, max: 5_000_000_000 },
    { label: "5 - 10 tỷ", min: 5_000_000_000, max: 10_000_000_000 },
    { label: "Trên 10 tỷ", min: 10_000_000_000 },
  ],
  rent: [
    { label: "Mức giá (triệu/tháng)" },
    { label: "Dưới 2 triệu", max: 2_000_000 },
    { label: "2 - 3,5 triệu", min: 2_000_000, max: 3_500_000 },
    { label: "3,5 - 5 triệu", min: 3_500_000, max: 5_000_000 },
    { label: "5 - 8 triệu", min: 5_000_000, max: 8_000_000 },
    { label: "Trên 8 triệu", min: 8_000_000 },
  ],
  projects: [
    { label: "Mức giá (tỷ)" },
    { label: "Dưới 1,5 tỷ", max: 1_500_000_000 },
    { label: "1,5 - 3 tỷ", min: 1_500_000_000, max: 3_000_000_000 },
    { label: "3 - 5 tỷ", min: 3_000_000_000, max: 5_000_000_000 },
    { label: "5 - 10 tỷ", min: 5_000_000_000, max: 10_000_000_000 },
    { label: "Trên 10 tỷ", min: 10_000_000_000 },
  ],
};

const CITY_OPTIONS = ["", "Thành phố Hà Nội", "Thành phố Hồ Chí Minh", "Thành phố Đà Nẵng", "Thành phố Cần Thơ", "Tỉnh Bình Dương"];

const LOCATION_PLACEHOLDER: Record<SearchMode, string> = {
  sale: "Địa bàn, quận huyện cần mua...",
  rent: "Khu vực hoặc tên khu trọ...",
  projects: "Tên dự án hoặc thành phố...",
};

export default function SegmentedSearchBar({ onSearch, isLoading = false, initialMode = "sale" }: Props) {
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [location, setLocation] = useState("");
  const [typeValue, setTypeValue] = useState("");
  const [priceIndex, setPriceIndex] = useState(0);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [city, setCity] = useState("");
  const [bedrooms, setBedrooms] = useState("");
  const [area, setArea] = useState("");

  const selectMode = (next: SearchMode) => {
    setMode(next);
    setTypeValue("");
    setPriceIndex(0);
  };

  const submit = () => {
    const price = PRICE_OPTIONS[mode][priceIndex];
    const type = TYPE_OPTIONS[mode].find((option) => option.value === typeValue);
    onSearch({
      mode,
      location: location.trim(),
      propertyType: mode === "rent" ? (typeValue === "commercial" ? "commercial" : undefined) : (typeValue as PropertyType | undefined) || undefined,
      rentalType: mode === "rent" && typeValue !== "commercial" ? (typeValue as HomeSearchPayload["rentalType"]) : undefined,
      projectKeyword: mode === "projects" ? type?.value || undefined : undefined,
      minPrice: price.min,
      maxPrice: price.max,
      city: city || undefined,
      minBedrooms: bedrooms ? Number(bedrooms) : undefined,
      minAreaSqm: area ? Number(area) : undefined,
      aiEnabled,
    });
  };

  return (
    <div className="mx-auto w-full max-w-4xl space-y-3">
      {/* Transaction Mode Tabs */}
      <div className="flex justify-center">
        <div className="inline-flex rounded-full border border-white/60 bg-white/80 p-1 shadow-md backdrop-blur-md">
          {MODE_TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => selectMode(tab.key)}
              className={`rounded-full px-4 py-2 text-xs font-bold transition sm:text-sm ${
                mode === tab.key
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/30"
                  : "text-slate-600 hover:text-blue-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Unified Floating Pill Bar */}
      <div className="grid grid-cols-1 items-center gap-2 rounded-3xl border border-slate-200/60 bg-white p-2 shadow-xl shadow-slate-900/10 md:grid-cols-12 md:rounded-full">
        {/* Compartment 1: Location / Project */}
        <label className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-2.5 transition focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500/40 md:col-span-4 md:rounded-full">
          <MapPin className="h-4 w-4 shrink-0 text-blue-600" />
          <input
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && submit()}
            placeholder={LOCATION_PLACEHOLDER[mode]}
            className="w-full bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
        </label>

        {/* Compartment 2: Property type (context-aware) */}
        <label className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-2.5 transition focus-within:ring-2 focus-within:ring-blue-500/40 md:col-span-3 md:rounded-full">
          <Building2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <select
            value={typeValue}
            onChange={(event) => setTypeValue(event.target.value)}
            className="w-full cursor-pointer bg-transparent text-sm text-slate-800 focus:outline-none"
          >
            {TYPE_OPTIONS[mode].map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {/* Compartment 3: Price range (context-aware) */}
        <label className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-2.5 transition focus-within:ring-2 focus-within:ring-blue-500/40 md:col-span-3 md:rounded-full">
          <Wallet className="h-4 w-4 shrink-0 text-amber-600" />
          <select
            value={priceIndex}
            onChange={(event) => setPriceIndex(Number(event.target.value))}
            className="w-full cursor-pointer bg-transparent text-sm text-slate-800 focus:outline-none"
          >
            {PRICE_OPTIONS[mode].map((option, index) => (
              <option key={option.label} value={index}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {/* Compartment 4: Actions */}
        <div className="flex items-center gap-2 md:col-span-2">
          <button
            type="button"
            onClick={() => setFiltersOpen((prev) => !prev)}
            className={`inline-flex flex-1 items-center justify-center gap-1 rounded-full border px-3 py-2.5 text-xs font-bold transition ${
              filtersOpen
                ? "border-blue-200 bg-blue-50 text-blue-700"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Bộ lọc</span>
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={isLoading}
            aria-label="Tìm kiếm"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-500/30 transition hover:bg-blue-700 active:scale-95 disabled:opacity-60"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4.5 w-4.5" />}
          </button>
        </div>
      </div>

      {/* Extended Filter Drawer */}
      {filtersOpen && (
        <div className="animate-in fade-in slide-in-from-top-2 grid grid-cols-1 gap-2 rounded-2xl border border-slate-200/60 bg-white p-3 shadow-lg sm:grid-cols-3">
          <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs">
            <span className="font-semibold text-slate-500">Thành phố</span>
            <select value={city} onChange={(event) => setCity(event.target.value)} className="w-full cursor-pointer bg-transparent text-slate-800 focus:outline-none">
              {CITY_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "Tất cả"}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs">
            <span className="font-semibold text-slate-500">Phòng ngủ</span>
            <select value={bedrooms} onChange={(event) => setBedrooms(event.target.value)} className="w-full cursor-pointer bg-transparent text-slate-800 focus:outline-none">
              <option value="">Tất cả</option>
              {[1, 2, 3].map((value) => (
                <option key={value} value={value}>{`${value}+ PN`}</option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs">
            <span className="font-semibold text-slate-500">Diện tích</span>
            <select value={area} onChange={(event) => setArea(event.target.value)} className="w-full cursor-pointer bg-transparent text-slate-800 focus:outline-none">
              <option value="">Tất cả</option>
              <option value="30">30+ m²</option>
              <option value="50">50+ m²</option>
              <option value="80">80+ m²</option>
            </select>
          </label>
        </div>
      )}

      {/* AI Semantic Search Toggle */}
      <div className="flex justify-center">
        <button
          type="button"
          onClick={() => setAiEnabled((prev) => !prev)}
          className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
            aiEnabled ? "border-purple-200 bg-purple-50 text-purple-700" : "border-slate-200 bg-white/80 text-slate-500 hover:text-slate-700"
          }`}
        >
          <span
            className={`relative inline-flex h-4 w-7 items-center rounded-full transition ${aiEnabled ? "bg-purple-600" : "bg-slate-300"}`}
          >
            <span className={`absolute h-3 w-3 rounded-full bg-white shadow transition-all ${aiEnabled ? "left-3.5" : "left-0.5"}`} />
          </span>
          <Sparkles className={`h-3.5 w-3.5 ${aiEnabled ? "text-purple-600" : "text-slate-400"}`} />
          <span>Tìm kiếm thông minh bằng AI</span>
        </button>
      </div>
    </div>
  );
}
