import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  MapPin,
  Bed,
  Bath,
  Maximize2,
  Calendar,
  Share2,
  Heart,
  Phone,
  Mail,
  ShieldCheck,
  Building,
} from "lucide-react";
import { PropertyResponse } from "@shared/types";
import { apiClient } from "@/lib/api";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";

interface PropertyDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PropertyDetailPageProps) {
  const { id } = await params;
  try {
    const property = await apiClient.getProperty(id);
    return {
      title: `${property.title} | Space247`,
      description: property.description.slice(0, 160),
    };
  } catch {
    return {
      title: "Bất động sản | Space247",
    };
  }
}

export default async function PropertyDetailPage({ params }: PropertyDetailPageProps) {
  const { id } = await params;
  let property: PropertyResponse;

  try {
    property = await apiClient.getProperty(id);
  } catch (error) {
    console.error(`Error fetching property ${id}:`, error);
    notFound();
  }

  const imageUrl = getPlaceholderImage(property.property_type, 0);

  return (
    <div className="space-y-8 pb-16">
      {/* Back Button & Actions */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Quay lại danh sách</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 shadow-xs hover:bg-slate-50"
          >
            <Share2 className="h-4 w-4 text-slate-500" />
            <span>Chia sẻ</span>
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 shadow-xs hover:bg-slate-50"
          >
            <Heart className="h-4 w-4 text-slate-500" />
            <span>Lưu tin</span>
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Gallery & Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Main Photo Hero */}
          <div className="relative aspect-16/9 w-full overflow-hidden rounded-3xl bg-slate-100 shadow-lg">
            <img
              src={imageUrl}
              alt={property.title}
              className="h-full w-full object-cover"
            />
            <div className="absolute top-4 left-4 flex gap-2">
              <span
                className={`rounded-full px-3 py-1 text-xs font-bold shadow-md backdrop-blur-md ${
                  property.listing_type === "sale"
                    ? "bg-blue-600/90 text-white"
                    : "bg-emerald-600/90 text-white"
                }`}
              >
                {property.listing_type === "sale" ? "Bán" : "Cho thuê"}
              </span>
              <span className="rounded-full bg-slate-900/80 px-3 py-1 text-xs font-medium text-white backdrop-blur-md">
                {formatPropertyType(property.property_type)}
              </span>
            </div>
          </div>

          {/* Title & Location Header */}
          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-snug">
                  {property.title}
                </h1>
                <div className="mt-3 flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
                  <span>
                    {property.address}
                    {property.ward && `, ${property.ward}`}
                    {property.district && `, ${property.district}`}
                    {property.city && `, ${property.city}`}
                  </span>
                </div>
              </div>

              <div className="shrink-0 text-left sm:text-right">
                <div className="text-3xl font-extrabold text-blue-700">
                  {formatPrice(property.price, property.currency || "VND", property.listing_type)}
                </div>
                {property.area_sqm > 0 && (
                  <div className="text-xs text-slate-500 mt-1">
                    Đơn giá: ~{Math.round(property.price / property.area_sqm).toLocaleString("vi-VN")} {property.currency || "VND"}/m²
                  </div>
                )}
              </div>
            </div>

            {/* Quick Specs Highlight Box */}
            <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4 rounded-2xl bg-slate-50 p-4 text-center">
              <div className="p-2">
                <div className="flex justify-center text-blue-600 mb-1">
                  <Maximize2 className="h-5 w-5" />
                </div>
                <div className="text-xs text-slate-500 font-medium">Diện tích</div>
                <div className="text-base font-bold text-slate-900">{property.area_sqm} m²</div>
              </div>

              <div className="p-2">
                <div className="flex justify-center text-blue-600 mb-1">
                  <Bed className="h-5 w-5" />
                </div>
                <div className="text-xs text-slate-500 font-medium">Phòng ngủ</div>
                <div className="text-base font-bold text-slate-900">
                  {property.num_bedrooms ?? "--"}
                </div>
              </div>

              <div className="p-2">
                <div className="flex justify-center text-blue-600 mb-1">
                  <Bath className="h-5 w-5" />
                </div>
                <div className="text-xs text-slate-500 font-medium">Phòng vệ sinh</div>
                <div className="text-base font-bold text-slate-900">
                  {property.num_bathrooms ?? "--"}
                </div>
              </div>

              <div className="p-2">
                <div className="flex justify-center text-blue-600 mb-1">
                  <Building className="h-5 w-5" />
                </div>
                <div className="text-xs text-slate-500 font-medium">Trạng thái</div>
                <div className="text-base font-bold text-emerald-600 uppercase">
                  {property.status}
                </div>
              </div>
            </div>
          </div>

          {/* Description Section */}
          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Thông tin chi tiết</h2>
            <div className="prose max-w-none text-slate-700 text-sm sm:text-base leading-relaxed whitespace-pre-line">
              {property.description}
            </div>
          </div>

          {/* Map / Coordinates Info */}
          {(property.latitude || property.longitude) && (
            <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-3">
              <h2 className="text-lg font-bold text-slate-900">Tọa độ vị trí địa lý</h2>
              <p className="text-xs text-slate-500">
                Kinh độ: {property.longitude}, Vĩ độ: {property.latitude}
              </p>
              <div className="rounded-2xl bg-slate-100 p-8 text-center text-slate-400 text-xs">
                Bản đồ tương tác OpenStreetMap / Mapbox được tích hợp tại tọa độ này.
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Col: Contact & Safety Sidebar */}
        <div className="space-y-6">
          {/* Agent Card */}
          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
                SP
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Chuyên viên Space247</h3>
                <p className="text-xs text-slate-500">Tư vấn bất động sản chuyên nghiệp</p>
                <div className="flex items-center gap-1 mt-1 text-xs text-emerald-600 font-semibold">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Đã xác minh</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <a
                href="tel:1900247247"
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition"
              >
                <Phone className="h-4 w-4" />
                <span>Gọi 1900 247 247</span>
              </a>

              <a
                href="mailto:support@space247.vn"
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
              >
                <Mail className="h-4 w-4 text-slate-500" />
                <span>Gửi email liên hệ</span>
              </a>
            </div>

            <div className="border-t border-slate-100 pt-4 text-xs text-slate-400 flex items-center justify-between">
              <div className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                <span>Ngày đăng:</span>
              </div>
              <span>{new Date(property.created_at).toLocaleDateString("vi-VN")}</span>
            </div>
          </div>

          {/* Safety Box */}
          <div className="rounded-3xl border border-amber-200/80 bg-amber-50/50 p-6 text-xs text-amber-900 space-y-2">
            <h4 className="font-bold flex items-center gap-1.5 text-amber-800">
              <ShieldCheck className="h-4 w-4 text-amber-600" />
              Lưu ý an toàn giao dịch
            </h4>
            <p className="leading-relaxed text-amber-800/80">
              Không đặt cọc hoặc chuyển tiền trước khi xem trực tiếp bất động sản và kiểm tra giấy tờ pháp lý (Sổ đỏ / Sổ hồng) bản gốc.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
