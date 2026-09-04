import Link from "next/link";
import { Bed, Bath, Maximize2, MapPin, Sparkles, ArrowUpRight, Heart } from "lucide-react";
import { PropertyResponse, SearchResultItem } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import { useFavorites } from "@/lib/favorites";

interface PropertyCardProps {
  item: SearchResultItem | PropertyResponse;
  index?: number;
}

export default function PropertyCard({ item, index = 0 }: PropertyCardProps) {
  const { isFavorite, toggleFavorite } = useFavorites();

  // Support both SearchResultItem and raw PropertyResponse
  const isSearchResult = "property" in item;
  const property: PropertyResponse = isSearchResult ? (item as SearchResultItem).property : (item as PropertyResponse);
  const similarityScore = isSearchResult ? (item as SearchResultItem).similarity_score : null;
  const rrfScore = isSearchResult ? (item as SearchResultItem).rrf_score : null;

  const favorited = isFavorite(property.id);
  const imageUrl = getPlaceholderImage(property.property_type, index);

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
      {/* Image Container */}
      <div className="relative aspect-16/10 w-full overflow-hidden bg-slate-100">
        <img
          src={imageUrl}
          alt={property.title}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />

        {/* Listing Type Tag */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5">
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-semibold shadow-xs backdrop-blur-md ${
              property.listing_type === "sale"
                ? "bg-blue-600/90 text-white"
                : "bg-emerald-600/90 text-white"
            }`}
          >
            {property.listing_type === "sale" ? "Bán" : "Cho thuê"}
          </span>
          <span className="rounded-full bg-slate-900/70 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-md">
            {formatPropertyType(property.property_type)}
          </span>
        </div>

        {/* Top Right Badges: Favorite Button & Semantic Match Badge */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5">
          {typeof similarityScore === "number" && !Number.isNaN(similarityScore) && (
            <div className="flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-indigo-700 shadow-md backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5 text-indigo-500 fill-indigo-500" />
              <span>{Math.max(0, Math.min(100, similarityScore * 100)).toFixed(1)}% phù hợp</span>
            </div>
          )}

          <button
            type="button"
            onClick={handleToggleFavorite}
            title={favorited ? "Xóa khỏi danh sách yêu thích" : "Lưu vào danh sách yêu thích"}
            className={`flex h-8 w-8 items-center justify-center rounded-full shadow-md backdrop-blur-md transition cursor-pointer ${
              favorited
                ? "bg-rose-500 text-white hover:bg-rose-600"
                : "bg-white/90 text-slate-600 hover:bg-white hover:text-rose-500"
            }`}
          >
            <Heart className={`h-4 w-4 transition ${favorited ? "fill-current" : ""}`} />
          </button>
        </div>
      </div>

      {/* Content Container */}
      <div className="flex flex-1 flex-col p-5">
        {/* Price & Area */}
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-xl font-bold text-blue-700">
            {formatPrice(property.price, property.currency, property.listing_type)}
          </span>
          <span className="text-xs font-semibold text-slate-500">
            {property.area_sqm} m²
          </span>
        </div>

        {/* Title */}
        <Link href={`/properties/${property.id}`} className="mt-2.5 block group-hover:text-blue-600 transition">
          <h3 className="line-clamp-2 text-base font-semibold text-slate-900 leading-snug">
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

        {/* Features: Bedrooms, Bathrooms, Area */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
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
      </div>
    </div>
  );
}
