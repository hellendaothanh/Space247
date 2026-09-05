"use client";

import { useState, useEffect, useTransition } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  AlertCircle,
  FileEdit,
  MapPin,
  Home,
  Tag,
  DollarSign,
  Layers,
  FileText,
  Save,
  Check,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ListingType, PropertyResponse, PropertyStatus, PropertyType } from "@shared/types";
import { formatPropertyType } from "@/lib/utils";
import AiListingGeneratorModal from "@/components/AiListingGeneratorModal";
import AvmPriceAdvisor from "@/components/AvmPriceAdvisor";

const editPropertyFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(3, "Tiêu đề phải có ít nhất 3 ký tự")
    .max(255, "Tiêu đề không được vượt quá 255 ký tự"),
  description: z
    .string()
    .trim()
    .min(10, "Mô tả chi tiết phải có ít nhất 10 ký tự"),
  property_type: z.enum(["apartment", "house", "villa", "land", "commercial"] as const),
  listing_type: z.enum(["sale", "rent"] as const),
  price: z.number().positive("Giá tiền phải lớn hơn 0"),
  currency: z.string().default("VND"),
  area_sqm: z.number().positive("Diện tích phải lớn hơn 0 m²"),
  num_bedrooms: z.number().int().min(0).nullable().optional(),
  num_bathrooms: z.number().int().min(0).nullable().optional(),
  address: z
    .string()
    .trim()
    .min(3, "Địa chỉ đường phố phải có ít nhất 3 ký tự")
    .max(500, "Địa chỉ không vượt quá 500 ký tự"),
  ward: z.string().trim().max(100).optional(),
  district: z.string().trim().max(100).optional(),
  city: z.string().trim().min(2, "Vui lòng nhập Tỉnh / Thành phố").max(100),
  status: z.enum(["active", "pending", "sold", "rented", "inactive"] as const),
  latitude: z.number().min(-90).max(90).nullable().optional(),
  longitude: z.number().min(-180).max(180).nullable().optional(),
});

const MAJOR_CITIES = [
  "Thành phố Hồ Chí Minh",
  "Hà Nội",
  "Đà Nẵng",
  "Bình Dương",
  "Đồng Nai",
  "Khánh Hòa",
  "Cần Thơ",
  "Hải Phòng",
];

export default function EditPropertyPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isPending, startTransition] = useTransition();

  const propertyId = params.id as string;

  const [isLoadingProperty, setIsLoadingProperty] = useState(true);
  const [property, setProperty] = useState<PropertyResponse | null>(null);

  // Form states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [propertyType, setPropertyType] = useState<PropertyType>("apartment");
  const [listingType, setListingType] = useState<ListingType>("sale");
  const [status, setStatus] = useState<PropertyStatus>("active");
  const [priceStr, setPriceStr] = useState("");
  const [areaStr, setAreaStr] = useState("");
  const [bedroomsStr, setBedroomsStr] = useState("");
  const [bathroomsStr, setBathroomsStr] = useState("");
  const [address, setAddress] = useState("");
  const [ward, setWard] = useState("");
  const [district, setDistrict] = useState("");
  const [city, setCity] = useState("Thành phố Hồ Chí Minh");
  const [latitudeStr, setLatitudeStr] = useState("");
  const [longitudeStr, setLongitudeStr] = useState("");

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);

  const handleAiApply = (data: {
    title: string;
    description: string;
    specs: any;
  }) => {
    if (data.title) setTitle(data.title);
    if (data.description) setDescription(data.description);
    if (data.specs.area_sqm) setAreaStr(data.specs.area_sqm.toString());
    if (data.specs.num_bedrooms) setBedroomsStr(data.specs.num_bedrooms.toString());
    if (data.specs.num_bathrooms) setBathroomsStr(data.specs.num_bathrooms.toString());
    if (data.specs.suggested_price) setPriceStr(data.specs.suggested_price.toString());
  };

  // Authentication check
  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [user, isAuthLoading, router]);

  // Load existing property
  useEffect(() => {
    async function loadData() {
      if (!propertyId) return;
      try {
        setIsLoadingProperty(true);
        const data = await apiClient.getProperty(propertyId);
        setProperty(data);

        // Populate fields
        setTitle(data.title);
        setDescription(data.description);
        setPropertyType(data.property_type);
        setListingType(data.listing_type);
        setStatus(data.status);
        setPriceStr(String(data.price));
        setAreaStr(String(data.area_sqm));
        setBedroomsStr(data.num_bedrooms !== null && data.num_bedrooms !== undefined ? String(data.num_bedrooms) : "");
        setBathroomsStr(data.num_bathrooms !== null && data.num_bathrooms !== undefined ? String(data.num_bathrooms) : "");
        setAddress(data.address);
        setWard(data.ward || "");
        setDistrict(data.district || "");
        setCity(data.city);
        setLatitudeStr(data.latitude !== null && data.latitude !== undefined ? String(data.latitude) : "");
        setLongitudeStr(data.longitude !== null && data.longitude !== undefined ? String(data.longitude) : "");
      } catch (err: any) {
        setServerError(err?.message || "Không thể tải thông tin bất động sản.");
      } finally {
        setIsLoadingProperty(false);
      }
    }

    if (user) {
      loadData();
    }
  }, [propertyId, user]);

  const isOwnerOrAdmin =
    user && property
      ? property.user_id === user.id || user.role === "admin" || !property.user_id
      : true;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);
    setSuccessMessage(null);
    setErrors({});

    if (!isOwnerOrAdmin) {
      setServerError("Bạn không có quyền chỉnh sửa tin đăng này.");
      return;
    }

    const rawValues = {
      title,
      description,
      property_type: propertyType,
      listing_type: listingType,
      status,
      price: parseFloat(priceStr),
      currency: property?.currency || "VND",
      area_sqm: parseFloat(areaStr),
      num_bedrooms: bedroomsStr ? parseInt(bedroomsStr, 10) : null,
      num_bathrooms: bathroomsStr ? parseInt(bathroomsStr, 10) : null,
      address,
      ward: ward.trim() ? ward.trim() : null,
      district: district.trim() ? district.trim() : null,
      city: city.trim(),
      latitude: latitudeStr ? parseFloat(latitudeStr) : null,
      longitude: longitudeStr ? parseFloat(longitudeStr) : null,
    };

    const parsed = editPropertyFormSchema.safeParse(rawValues);
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      parsed.error.issues.forEach((err: z.ZodIssue) => {
        if (err.path && err.path[0]) {
          fieldErrors[err.path[0].toString()] = err.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    startTransition(async () => {
      try {
        const updated = await apiClient.updateProperty(propertyId, parsed.data);
        setProperty(updated);
        setSuccessMessage("Cập nhật tin đăng và tái tạo vector embedding thành công!");
        setTimeout(() => {
          router.push("/properties/my");
        }, 1200);
      } catch (err: any) {
        setServerError(err?.message || "Lỗi khi cập nhật bất động sản. Vui lòng kiểm tra lại.");
      }
    });
  };

  if (isAuthLoading || isLoadingProperty) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-sm font-medium text-slate-500">Đang tải dữ liệu bài đăng...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50/50 pb-20">
      {/* Header Bar */}
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
          <Link
            href="/properties/my"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition mb-3"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Quay lại Quản lý tin đăng</span>
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight sm:text-3xl">
                Chỉnh sửa tin đăng
              </h1>
              <p className="mt-1 text-xs text-slate-500">
                Mã tin: <span className="font-mono text-slate-700 font-medium">{propertyId}</span>
              </p>
            </div>
            <Link
              href={`/properties/${propertyId}`}
              className="hidden sm:inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:underline"
            >
              Xem trang hiển thị
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        {/* Messages */}
        {serverError && (
          <div className="mb-6 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
            <AlertCircle className="h-5 w-5 shrink-0 text-rose-600 mt-0.5" />
            <div className="text-xs">
              <p className="font-bold">Không thể lưu thay đổi</p>
              <p className="mt-0.5">{serverError}</p>
            </div>
          </div>
        )}

        {successMessage && (
          <div className="mb-6 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 mt-0.5" />
            <div className="text-xs">
              <p className="font-bold">Thành công</p>
              <p className="mt-0.5">{successMessage}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Card 1: Trạng thái & Loại hình */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-6">
              <Tag className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-bold text-slate-900">Trạng thái & Hình thức giao dịch</h2>
            </div>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              {/* Status */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Trạng thái tin đăng
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as PropertyStatus)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="active">Đang hiển thị (Active)</option>
                  <option value="inactive">Tạm dừng (Inactive)</option>
                  <option value="sold">Đã bán (Sold)</option>
                  <option value="rented">Đã cho thuê (Rented)</option>
                  <option value="pending">Chờ cập nhật (Pending)</option>
                </select>
              </div>

              {/* Listing Type */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Mục đích
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setListingType("sale")}
                    className={`rounded-xl py-2.5 text-xs font-bold transition border ${
                      listingType === "sale"
                        ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    Bán
                  </button>
                  <button
                    type="button"
                    onClick={() => setListingType("rent")}
                    className={`rounded-xl py-2.5 text-xs font-bold transition border ${
                      listingType === "rent"
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    Cho thuê
                  </button>
                </div>
              </div>

              {/* Property Type */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Loại bất động sản
                </label>
                <select
                  value={propertyType}
                  onChange={(e) => setPropertyType(e.target.value as PropertyType)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="apartment">Căn hộ chung cư</option>
                  <option value="house">Nhà phố / Nhà riêng</option>
                  <option value="villa">Biệt thự / Villa</option>
                  <option value="land">Đất nền dự án / Thổ cư</option>
                  <option value="commercial">Mặt bằng kinh doanh</option>
                </select>
              </div>
            </div>
          </div>

          {/* Card 2: Nội dung & Mô tả */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h2 className="text-base font-bold text-slate-900">Thông tin bài đăng & Mô tả</h2>
              </div>
              <button
                type="button"
                onClick={() => setIsAiModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-xs transition cursor-pointer"
              >
                <FileEdit className="w-3.5 h-3.5" />
                <span>Hỗ trợ soạn tin</span>
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Tiêu đề tin đăng <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: Căn hộ 2PN Vinhomes Central Park view sông cực đẹp..."
                  className={`w-full rounded-xl border px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:outline-hidden focus:ring-2 transition ${
                    errors.title
                      ? "border-rose-300 bg-rose-50/30 focus:ring-rose-500/20"
                      : "border-slate-200 bg-slate-50/50 focus:border-blue-600 focus:ring-blue-500/20"
                  }`}
                />
                {errors.title && <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.title}</p>}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Mô tả chi tiết <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={5}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Mô tả cụ thể vị trí, thiết kế, tiện ích, pháp lý..."
                  className={`w-full rounded-xl border px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:outline-hidden focus:ring-2 transition ${
                    errors.description
                      ? "border-rose-300 bg-rose-50/30 focus:ring-rose-500/20"
                      : "border-slate-200 bg-slate-50/50 focus:border-blue-600 focus:ring-blue-500/20"
                  }`}
                />
                {errors.description && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.description}</p>
                )}
                <p className="mt-1 text-[11px] text-slate-400">
                  Hệ thống AI sẽ tự động tái tạo vector ngữ nghĩa 768 chiều khi bạn sửa tiêu đề hoặc mô tả.
                </p>
              </div>

              {/* Price & Area */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Mức giá (VND) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={priceStr}
                    onChange={(e) => setPriceStr(e.target.value)}
                    placeholder="3500000000"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.price && <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.price}</p>}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Diện tích (m²) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={areaStr}
                    onChange={(e) => setAreaStr(e.target.value)}
                    placeholder="75"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.area_sqm && (
                    <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.area_sqm}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Số phòng ngủ
                  </label>
                  <input
                    type="number"
                    value={bedroomsStr}
                    onChange={(e) => setBedroomsStr(e.target.value)}
                    placeholder="2"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.num_bedrooms && (
                    <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.num_bedrooms}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Số phòng tắm
                  </label>
                  <input
                    type="number"
                    value={bathroomsStr}
                    onChange={(e) => setBathroomsStr(e.target.value)}
                    placeholder="2"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.num_bathrooms && (
                    <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.num_bathrooms}</p>
                  )}
                </div>
              </div>

              {/* Smart AVM Pricing Advisor */}
              <div className="pt-2">
                <AvmPriceAdvisor
                  propertyType={propertyType}
                  areaSqm={parseFloat(areaStr.replace(/,/g, "")) || 0}
                  numBedrooms={parseInt(bedroomsStr, 10) || null}
                  numBathrooms={parseInt(bathroomsStr, 10) || null}
                  latitude={parseFloat(latitudeStr) || null}
                  longitude={parseFloat(longitudeStr) || null}
                  proposedPrice={parseFloat(priceStr.replace(/,/g, "")) || null}
                  onApplyPrice={(price) => setPriceStr(Math.round(price).toString())}
                />
              </div>
            </div>
          </div>

          {/* Card 3: Vị trí */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-6">
              <MapPin className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-bold text-slate-900">Địa chỉ & Tọa độ bản đồ</h2>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="sm:col-span-3">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Địa chỉ số nhà, tên đường <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="208 Nguyễn Hữu Cảnh"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                {errors.address && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.address}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Phường / Xã
                </label>
                <input
                  type="text"
                  value={ward}
                  onChange={(e) => setWard(e.target.value)}
                  placeholder="Phường 22"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                {errors.ward && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.ward}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Quận / Huyện
                </label>
                <input
                  type="text"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  placeholder="Bình Thạnh"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                {errors.district && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.district}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Tỉnh / Thành phố <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  list="city-options"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Chọn hoặc nhập Tỉnh / Thành phố"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                <datalist id="city-options">
                  {MAJOR_CITIES.map((c) => (
                    <option key={c} value={c} />
                  ))}
                </datalist>
                {errors.city && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.city}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Vĩ độ (Latitude)
                </label>
                <input
                  type="number"
                  step="any"
                  value={latitudeStr}
                  onChange={(e) => setLatitudeStr(e.target.value)}
                  placeholder="10.7915"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                {errors.latitude && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.latitude}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Kinh độ (Longitude)
                </label>
                <input
                  type="number"
                  step="any"
                  value={longitudeStr}
                  onChange={(e) => setLongitudeStr(e.target.value)}
                  placeholder="106.7215"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-xs text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20"
                />
                {errors.longitude && (
                  <p className="mt-1 text-[11px] text-rose-600 font-medium">{errors.longitude}</p>
                )}
              </div>
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <Link
              href="/properties/my"
              className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Hủy bỏ
            </Link>

            <button
              type="submit"
              disabled={isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition disabled:opacity-50"
            >
              {isPending ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Đang lưu thay đổi...</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>Lưu thay đổi</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* AI Listing Generator Modal */}
      <AiListingGeneratorModal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        initialPropertyType={propertyType}
        onApply={handleAiApply}
      />
    </div>
  );
}
