"use client";

import { Building2, Home, Layers, KeyRound, Trees, Map, Store, Building } from "lucide-react";

export interface HomeCategory {
  key: string;
  label: string;
  icon: typeof Building2;
  iconClass: string;
  /** Filter definition applied to the listing groups below */
  match: (p: { property_type: string; listing_type: string; rental_type?: string | null; title?: string; rental_rules?: any }) => boolean;
  count: number;
}

interface Props {
  categories: HomeCategory[];
  activeKey: string | null;
  onSelect: (key: string | null) => void;
}

export default function CategoryQuickNav({ categories, activeKey, onSelect }: Props) {
  return (
    <div className="-mx-4 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div className="flex w-max gap-3 sm:w-full sm:grid sm:grid-cols-4 lg:grid-cols-7">
        {categories.map((category) => {
          const Icon = category.icon;
          const isActive = activeKey === category.key;
          return (
            <button
              key={category.key}
              type="button"
              onClick={() => onSelect(isActive ? null : category.key)}
              className={`group flex w-[120px] shrink-0 flex-col items-center gap-2 rounded-2xl border p-3.5 text-center transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md sm:w-auto ${
                isActive
                  ? "border-blue-300 bg-blue-50 shadow-sm ring-1 ring-blue-400/40"
                  : "border-slate-200 bg-white hover:border-blue-200"
              }`}
            >
              <span
                className={`flex h-10 w-10 items-center justify-center rounded-xl transition ${category.iconClass} ${
                  isActive ? "ring-2 ring-blue-300" : ""
                }`}
              >
                <Icon className="h-5 w-5" />
              </span>
              <span className={`text-[11px] font-bold leading-tight ${isActive ? "text-blue-800" : "text-slate-800"}`}>
                {category.label}
              </span>
              <span className="text-[10px] font-medium text-slate-400">
                {category.count > 0 ? `${category.count}+ tin` : `${category.count} tin`}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export const HOME_CATEGORIES: Omit<HomeCategory, "count">[] = [
  { key: "apartment", label: "Căn hộ chung cư", icon: Building, iconClass: "bg-blue-100 text-blue-600", match: (p) => p.property_type === "apartment" },
  { key: "house", label: "Nhà phố mặt tiền", icon: Home, iconClass: "bg-emerald-100 text-emerald-600", match: (p) => p.property_type === "house" },
  {
    key: "room",
    label: "Phòng trọ & Gác lửng",
    icon: Layers,
    iconClass: "bg-amber-100 text-amber-600",
    match: (p) =>
      p.listing_type === "rent" &&
      (p.rental_type === "room" ||
        !!p.rental_rules?.has_mezzanine ||
        /phòng trọ|gác lửng|nhà trọ|phòng sinh viên/i.test(p.title || "")),
  },
  { key: "serviced", label: "Căn hộ dịch vụ Studio", icon: KeyRound, iconClass: "bg-purple-100 text-purple-600", match: (p) => p.listing_type === "rent" && p.rental_type === "serviced_apartment" },
  { key: "villa", label: "Biệt thự nghỉ dưỡng", icon: Trees, iconClass: "bg-teal-100 text-teal-600", match: (p) => p.property_type === "villa" },
  { key: "land", label: "Đất nền thổ cư", icon: Map, iconClass: "bg-orange-100 text-orange-600", match: (p) => p.property_type === "land" },
  { key: "commercial", label: "Shophouse & Văn phòng", icon: Store, iconClass: "bg-rose-100 text-rose-600", match: (p) => p.property_type === "commercial" },
];
