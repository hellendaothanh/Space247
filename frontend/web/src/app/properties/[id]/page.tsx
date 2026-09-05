import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  MapPin,
  Bed,
  Bath,
  Maximize2,
  Calendar,
  Phone,
  Mail,
  ShieldCheck,
  Building,
  Building2,
  ChevronRight,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PropertyDetailResponse } from "@shared/types";
import { apiClient } from "@/lib/api";
import { formatPrice, formatPropertyType } from "@/lib/utils";
import PropertyFavoriteButton from "@/components/PropertyFavoriteButton";
import PropertyDetailMap from "@/components/PropertyDetailMap";
import MortgageCalculator from "@/components/MortgageCalculator";
import PropertyGallery from "@/components/PropertyGallery";
import PropertyShareButton from "@/components/PropertyShareButton";

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
  let property: PropertyDetailResponse;

  try {
    property = await apiClient.getProperty(id);
  } catch (error) {
    console.error(`Error fetching property ${id}:`, error);
    notFound();
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-xs text-slate-500">
        <Link href="/" className="hover:text-blue-600 transition">
          Trang chủ
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
        {property.project ? (
          <>
            <Link href="/projects" className="hover:text-blue-600 transition">
              Dự án
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
            <Link
              href={`/projects/${property.project.slug}`}
              className="hover:text-blue-600 transition font-medium text-slate-700 max-w-[150px] truncate"
            >
              {property.project.name}
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
          </>
        ) : (
          <>
            <Link href="/" className="hover:text-blue-600 transition">
              Bất động sản
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
          </>
        )}
        <span className="font-semibold text-slate-900 truncate max-w-xs">{property.title}</span>
      </nav>

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
          <PropertyShareButton title={property.title} />
          <PropertyFavoriteButton propertyId={property.id} />
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Gallery & Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Photo Gallery Carousel with Thumbnail Selector and Fallback */}
          <PropertyGallery
            images={property.images}
            propertyType={property.property_type}
            title={property.title}
            listingType={property.listing_type}
          />

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
            <div className="prose max-w-none text-slate-700 text-sm sm:text-base leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {property.description}
              </ReactMarkdown>
            </div>
          </div>

          {/* Map / Coordinates Info */}
          {property.latitude && property.longitude && (
            <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Vị trí trên bản đồ tương tác</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Kinh độ: <span className="font-semibold text-slate-700">{property.longitude}</span>, Vĩ độ:{" "}
                    <span className="font-semibold text-slate-700">{property.latitude}</span>
                  </p>
                </div>
                <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1 rounded-xl">
                  Bán kính khám phá tiện ích: 1.0 km
                </div>
              </div>
              <PropertyDetailMap
                latitude={property.latitude}
                longitude={property.longitude}
                title={property.title}
                address={[property.address, property.ward, property.district, property.city]
                  .filter(Boolean)
                  .join(", ")}
                price={property.price}
                currency={property.currency}
                propertyType={property.property_type}
              />
            </div>
          )}

          {/* Mortgage & Financial Affordability Calculator (Chỉ hiển thị cho tin Bán, ẩn với tin Cho thuê) */}
          {property.listing_type !== "rent" && (
            <MortgageCalculator
              propertyPrice={property.price}
              propertyTitle={property.title}
              currency={property.currency}
            />
          )}
        </div>

        {/* Right 1 Col: Contact & Safety Sidebar */}
        <div className="space-y-6">
          {/* Linked Project Banner */}
          {property.project && (
            <div className="rounded-3xl border border-blue-100 bg-linear-to-br from-blue-50/80 to-indigo-50/80 p-5 shadow-xs">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-xs">
                    <Building2 className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                      Thuộc dự án
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 line-clamp-1">
                      {property.project.name}
                    </h4>
                    {property.project.developer && (
                      <p className="text-xs text-slate-500 line-clamp-1">
                        CĐT: {property.project.developer}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-blue-200/50 flex items-center justify-between">
                <span className="text-xs text-slate-600 font-medium">
                  {property.project.city}
                </span>
                <Link
                  href={`/projects/${property.project.slug}`}
                  className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-900 transition"
                >
                  <span>Khám phá dự án</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* Dynamic Agent Card */}
          {(() => {
            const agent = property.agent;
            const agentName = agent?.full_name || "Chuyên viên Space247";
            const agentPhone = agent?.phone_number || agent?.phone || "1900 247 247";
            const agentEmail = agent?.email || "support@space247.vn";
            const agentRoleLabel =
              agent?.role === "admin"
                ? "Quản trị viên Space247"
                : agent?.role === "agent"
                ? "Chuyên viên tư vấn Space247"
                : "Người đăng tin Space247";
            const initials = agentName
              .split(" ")
              .filter(Boolean)
              .map((w) => w[0])
              .slice(-2)
              .join("")
              .toUpperCase() || "SP";

            return (
              <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-6">
                <div className="flex items-center gap-4">
                  {agent?.avatar_url ? (
                    <img
                      src={agent.avatar_url}
                      alt={agentName}
                      className="h-14 w-14 rounded-full object-cover shadow-md"
                    />
                  ) : (
                    <div className="h-14 w-14 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
                      {initials}
                    </div>
                  )}
                  <div>
                    <h3 className="font-bold text-slate-900">{agentName}</h3>
                    <p className="text-xs text-slate-500">{agentRoleLabel}</p>
                    <div className="flex items-center gap-1 mt-1 text-xs text-emerald-600 font-semibold">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      <span>Đã xác minh</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <a
                    href={`tel:${agentPhone.replace(/\s+/g, "")}`}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition"
                  >
                    <Phone className="h-4 w-4" />
                    <span>Gọi {agentPhone}</span>
                  </a>

                  <a
                    href={`mailto:${agentEmail}`}
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
            );
          })()}

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
