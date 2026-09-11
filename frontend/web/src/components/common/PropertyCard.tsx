import { RentalBadges } from "./RentalDetails";
import Link from "next/link";
import { Bed, Bath, Maximize2, MapPin, BadgeCheck, ArrowUpRight, Heart, FileCheck2 } from "lucide-react";
import { PropertyResponse, SearchResultItem } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import { useFavorites } from "@/lib/favorites";
import { useComparison } from "@/lib/comparison";

interface PropertyCardProps {
  item: SearchResultItem | PropertyResponse;
  index?: number;
}

const LEGAL_PATTERNS = ["sổ hồng", "sổ đỏ", "sổ hồng riêng", "sổ đỏ chính chủ"];

export default function PropertyCard({ item, index = 0 }: PropertyCardProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const { isSelected, toggleComparison, selectedProperties } = useComparison();

  // Support both SearchResultItem and raw PropertyResponse
  const isSearchResult = "property" in item;
  const property: PropertyResponse = isSearchResult ? (item as SearchResultItem).property : (item as PropertyResponse);
  const similarityScore = isSearchResult ? (item as SearchResultItem).similarity_score : null;

  const isRent = property.listing_type === "rent";
  const favorited = isFavorite(property.id);
  const imageUrl = property.images?.length
    ? property.images[0]
    : getPlaceholderImage(property.property_type, index);
  const pricePerSqm = property.area_sqm > 0 ? Math.round(property.price / property.area_sqm) : null;
  const hasLegalDocs = LEGAL_PATTERNS.some((pattern) => property.description?.toLowerCase().includes(pattern));
  const costs = property.rental_costs;
  const rules = property.rental_rules;

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await toggleFavorite(property.id);
    } catch {
      // Handled in context
    }
  };

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
      {/* Image Container (16:10) */}
      <div className="relative aspect-16/10 w-full overflow-hidden bg-slate-100">
        <img
          src={imageUrl}
          alt={property.title}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />

        {/* Listing Type Tag (Mở bán / Cho thuê) */}
        <div className="absolute left-3 top-3 flex items-center gap-1.5">
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-semibold shadow-xs backdrop-blur-md ${
              isRent ? "bg-emerald-600/90 text-white" : "bg-blue-600/90 text-white"
            }`}
          >
            {isRent ? "Cho thuê" : "Mở bán"}
          </span>
          <span className="rounded-full bg-slate-900/70 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-md">
            {formatPropertyType(property.property_type)}
          </span>
        </div>

        {/* Top Right Badges: Semantic Match + Favorite */}
        <div className="absolute right-3 top-3 flex items-center gap-1.5">
          {typeof similarityScore === "number" && !Number.isNaN(similarityScore) && (
            <div className="flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-blue-700 shadow-md backdrop-blur-md">
              <BadgeCheck className="h-3.5 w-3.5 text-blue-600" />
              <span>{Math.max(0, Math.min(100, similarityScore * 100)).toFixed(1)}% phù hợp</span>
            </div>
          )}

          <button
            type="button"
            onClick={handleToggleFavorite}
            title={favorited ? "Xóa khỏi tin yêu thích" : "Lưu vào tin yêu thích"}
            aria-pressed={favorited}
            className={`flex h-8 w-8 items-center justify-center rounded-full shadow-md backdrop-blur-md transition-transform duration-200 hover:scale-110 active:scale-95 cursor-pointer ${
              favorited ? "bg-rose-500 text-white hover:bg-rose-600" : "bg-white/90 text-slate-600 hover:text-rose-500"
            }`}
          >
            <Heart className={`h-4 w-4 transition-all ${favorited ? "scale-110 fill-current" : ""}`} />
          </button>
        </div>
      </div>

      {/* Content Container */}
      <div className="flex flex-1 flex-col p-5">
        {/* Price Block: per listing type */}
        <div className="flex items-baseline justify-between gap-2">
          <span className={`text-xl font-extrabold ${isRent ? "text-emerald-600" : "text-blue-700"}`}>
            {isRent
              ? formatPrice(property.price, property.currency, "rent")
              : formatPrice(property.price, property.currency)}
          </span>
          {!isRent && pricePerSqm != null && (
            <span className="text-xs font-semibold text-slate-500">
              {(pricePerSqm / 1_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} tr/m²
            </span>
          )}
          {isRent && <span className="text-xs font-semibold text-slate-500">{property.area_sqm} m²</span>}
        </div>

        {/* Title */}
        <Link href={`/properties/${property.id}`} className="mt-2.5 block transition group-hover:text-blue-600">
          <RentalBadges property={property} />
          <h3 className="line-clamp-2 text-base font-semibold leading-snug text-slate-900">
            {property.title}
          </h3>
        </Link>

        {/* Address */}
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
          <MapPin className="h-3.5 w-3.5 shrink-0 text-slate-400" />
          <span className="line-clamp-1">
            {[property.ward, property.district, property.city].filter(Boolean).join(", ")}
          </span>
        </div>

        {/* Rental Highlight Badges */}
        {isRent && (costs?.electricity_billing === "state_rate" || rules?.live_with_owner === false || rules?.has_mezzanine) && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {costs?.electricity_billing === "state_rate" && (
              <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700 ring-1 ring-amber-200/60">
                ⚡ Điện giá dân
              </span>
            )}
            {rules?.live_with_owner === false && (
              <span className="rounded-md bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-700 ring-1 ring-sky-200/60">
                🗝️ Không chung chủ
              </span>
            )}
            {rules?.has_mezzanine && (
              <span className="rounded-md bg-violet-50 px-2 py-0.5 text-[11px] font-semibold text-violet-700 ring-1 ring-violet-200/60">
                🪜 Gác lửng
              </span>
            )}
          </div>
        )}

        {/* Sale Trust Badge */}
        {!isRent && hasLegalDocs && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-emerald-200/60">
              <FileCheck2 className="h-3 w-3" /> Sổ hồng riêng
            </span>
          </div>
        )}

        {/* Features: Bedrooms, Bathrooms, Area */}
        <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-600">
          <div className="flex items-center gap-4">
            {property.num_bedrooms !== null && property.num_bedrooms !== undefined && (
              <div className="flex items-center gap-1" title="Số phòng ngủ">
                <Bed className="h-4 w-4 text-slate-400" />
                <span className="font-medium">{property.num_bedrooms} PN</span>
              </div>
            )}
            {property.num_bathrooms !== null && property.num_bathrooms !== undefined && (
              <div className="flex items-center gap-1" title="Số phòng tắm / vệ sinh">
                <Bath className="h-4 w-4 text-slate-400" />
                <span className="font-medium">{property.num_bathrooms} WC</span>
              </div>
            )}
            <div className="flex items-center gap-1" title="Diện tích sử dụng">
              <Maximize2 className="h-3.5 w-3.5 text-slate-400" />
              <span className="font-medium">{property.area_sqm} m²</span>
            </div>
          </div>

          <Link
            href={`/properties/${property.id}`}
            className="flex items-center gap-0.5 text-xs font-medium text-blue-600 hover:text-blue-800"
          >
            <span>Chi tiết</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Comparison */}
        <div className="mt-3 flex items-center gap-2 border-t border-slate-100 pt-3">
          <input
            type="checkbox"
            id={`compare-${property.id}`}
            checked={isSelected(property.id)}
            onChange={() => toggleComparison(property)}
            disabled={!isSelected(property.id) && selectedProperties.length >= 3}
            className="h-4 w-4 cursor-pointer rounded border-slate-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
          />
          <label
            htmlFor={`compare-${property.id}`}
            className={`cursor-pointer select-none text-xs font-medium ${isSelected(property.id) ? "text-blue-600" : "text-slate-600"} ${
              !isSelected(property.id) && selectedProperties.length >= 3 ? "opacity-50" : ""
            }`}
          >
            {isSelected(property.id) ? "Đang chọn so sánh" : "So sánh"}
          </label>
        </div>
      </div>
    </div>
  );
}
