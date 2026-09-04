"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { z } from "zod";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  AlertCircle,
  Upload,
  Sparkles,
  MapPin,
  Home,
  Tag,
  DollarSign,
  Layers,
  FileText,
  X,
  Plus,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ListingType, PropertyType } from "@shared/types";
import AiListingGeneratorModal from "@/components/AiListingGeneratorModal";
import AvmPriceAdvisor from "@/components/AvmPriceAdvisor";

// Client-side Zod validation schema matching backend constraints
const propertyFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(3, "Tiêu đề phải có ít nhất 3 ký tự")
    .max(255, "Tiêu đề không được vượt quá 255 ký tự"),
  description: z
    .string()
    .trim()
    .min(10, "Mô tả chi tiết phải có ít nhất 10 ký tự"),
  property_type: z.enum(
    ["apartment", "house", "villa", "land", "commercial"] as const
  ),
  listing_type: z.enum(["sale", "rent"] as const),
  price: z
    .number()
    .positive("Giá tiền phải lớn hơn 0"),
  currency: z.string().default("VND"),
  area_sqm: z
    .number()
    .positive("Diện tích phải lớn hơn 0 m²"),
  num_bedrooms: z
    .number()
    .int("Số phòng phải là số nguyên")
    .min(0, "Số phòng ngủ không thể âm")
    .nullable()
    .optional(),
  num_bathrooms: z
    .number()
    .int("Số phòng phải là số nguyên")
    .min(0, "Số phòng tắm không thể âm")
    .nullable()
    .optional(),
  address: z
    .string()
    .trim()
    .min(3, "Địa chỉ đường phố phải có ít nhất 3 ký tự")
    .max(500, "Địa chỉ không vượt quá 500 ký tự"),
  ward: z.string().trim().max(100).optional(),
  district: z.string().trim().max(100).optional(),
  city: z
    .string()
    .trim()
    .min(2, "Vui lòng chọn hoặc nhập Tỉnh / Thành phố")
    .max(100),
  latitude: z
    .number()
    .min(-90, "Vĩ độ từ -90 đến 90")
    .max(90, "Vĩ độ từ -90 đến 90")
    .nullable()
    .optional(),
  longitude: z
    .number()
    .min(-180, "Kinh độ từ -180 đến 180")
    .max(180, "Kinh độ từ -180 đến 180")
    .nullable()
    .optional(),
});

type PropertyFormValues = z.infer<typeof propertyFormSchema>;

const POPULAR_AMENITIES = [
  "Hồ bơi",
  "Phòng Gym & Yoga",
  "Chỗ để ô tô",
  "Bảo vệ 24/7",
  "Sổ hồng riêng",
  "Full nội thất cao cấp",
  "Thang máy",
  "Ban công thoáng mát",
  "Công viên cây xanh",
  "Gần trường học & bệnh viện",
  "View sông/hồ",
  "Sân chơi trẻ em",
];

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

export default function CreatePropertyPage() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isPending, startTransition] = useTransition();

  // Form Fields State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [propertyType, setPropertyType] = useState<PropertyType>("apartment");
  const [listingType, setListingType] = useState<ListingType>("sale");
  const [priceStr, setPriceStr] = useState("");
  const [areaStr, setAreaStr] = useState("");
  const [bedroomsStr, setBedroomsStr] = useState("2");
  const [bathroomsStr, setBathroomsStr] = useState("2");
  const [address, setAddress] = useState("");
  const [ward, setWard] = useState("");
  const [district, setDistrict] = useState("");
  const [city, setCity] = useState("Thành phố Hồ Chí Minh");
  const [latitudeStr, setLatitudeStr] = useState("");
  const [longitudeStr, setLongitudeStr] = useState("");

  // Amenities & Photos UI state
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([
    "Bảo vệ 24/7",
    "Sổ hồng riêng",
  ]);
  const [customAmenity, setCustomAmenity] = useState("");
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // Validation errors & Server feedback
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{ id: string; title: string } | null>(null);
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
    if (data.specs.amenities && Array.isArray(data.specs.amenities)) {
      setSelectedAmenities((prev) => {
        const combined = new Set([...prev, ...data.specs.amenities]);
        return Array.from(combined);
      });
    }
  };

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) =>
      prev.includes(amenity)
        ? prev.filter((item) => item !== amenity)
        : [...prev, amenity]
    );
  };

  const addCustomAmenity = () => {
    if (!customAmenity.trim()) return;
    if (!selectedAmenities.includes(customAmenity.trim())) {
      setSelectedAmenities((prev) => [...prev, customAmenity.trim()]);
    }
    setCustomAmenity("");
  };

  const processImageFiles = (files: FileList | File[]) => {
    const validFiles: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file.type.startsWith("image/")) {
        alert(`File "${file.name}" không phải là định dạng ảnh hợp lệ.`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert(`File "${file.name}" vượt quá dung lượng cho phép (10MB).`);
        continue;
      }
      validFiles.push(file);
    }

    validFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result && typeof event.target.result === "string") {
          setUploadedImages((prev) => [...prev, event.target!.result as string]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const handleImageFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processImageFiles(e.target.files);
      e.target.value = ""; // Reset to allow re-upload of same file
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processImageFiles(e.dataTransfer.files);
    }
  };

  const removeImage = (index: number) => {
    setUploadedImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isPending || successInfo) return; // Prevent double submit
    setErrors({});
    setServerError(null);

    const priceNum = parseFloat(priceStr.replace(/,/g, ""));
    const areaNum = parseFloat(areaStr.replace(/,/g, ""));
    const bedroomsNum = bedroomsStr.trim() === "" ? null : parseInt(bedroomsStr, 10);
    const bathroomsNum = bathroomsStr.trim() === "" ? null : parseInt(bathroomsStr, 10);
    const latNum = latitudeStr.trim() === "" ? null : parseFloat(latitudeStr);
    const lngNum = longitudeStr.trim() === "" ? null : parseFloat(longitudeStr);

    // Combine user-selected amenities into description text so AI embedding and search captures them
    let enrichedDescription = description.trim();
    if (selectedAmenities.length > 0) {
      enrichedDescription += `\n\nTiện ích nổi bật: ${selectedAmenities.join(", ")}.`;
    }

    const payloadCandidate = {
      title,
      description: enrichedDescription,
      property_type: propertyType,
      listing_type: listingType,
      price: isNaN(priceNum) ? undefined : priceNum,
      currency: "VND",
      area_sqm: isNaN(areaNum) ? undefined : areaNum,
      num_bedrooms: isNaN(bedroomsNum as number) ? null : bedroomsNum,
      num_bathrooms: isNaN(bathroomsNum as number) ? null : bathroomsNum,
      address,
      ward: ward.trim() || undefined,
      district: district.trim() || undefined,
      city,
      latitude: isNaN(latNum as number) ? null : latNum,
      longitude: isNaN(lngNum as number) ? null : lngNum,
    };

    const validation = propertyFormSchema.safeParse(payloadCandidate);

    if (!validation.success) {
      const fieldErrors: Record<string, string> = {};
      validation.error.issues.forEach((err) => {
        if (err.path && err.path[0]) {
          fieldErrors[err.path[0].toString()] = err.message;
        }
      });
      setErrors(fieldErrors);
      // Scroll to top of form
      window.scrollTo({ top: 100, behavior: "smooth" });
      return;
    }

    startTransition(async () => {
      try {
        const createdProperty = await apiClient.createProperty(validation.data);
        setSuccessInfo({ id: createdProperty.id, title: createdProperty.title });

        // Smooth redirect to detail page
        setTimeout(() => {
          router.push(`/properties/${createdProperty.id}`);
        }, 1200);
      } catch (err: any) {
        console.error("Create property failed:", err);
        setServerError(
          err?.message || "Đã xảy ra lỗi khi tạo bài đăng. Vui lòng kiểm tra lại thông tin."
        );
      }
    });
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-20">
      {/* Header Breadcrumb & Title */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Quay lại trang chủ
          </Link>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Building2 className="h-7 w-7 text-blue-600" />
            Đăng tin Bất động sản Mới
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Hệ thống AI Space247 sẽ tự động vector hóa 768 chiều để tin đăng tiếp cận đúng khách hàng tiềm năng.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-blue-50/80 px-3.5 py-2 text-xs font-medium text-blue-700 border border-blue-100">
          <Sparkles className="h-4 w-4 shrink-0 text-blue-600" />
          <span>Tự động sinh AI Semantic Embedding</span>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successInfo && (
        <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/90 p-4 shadow-xs">
          <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-emerald-900">Đăng tin thành công!</h4>
            <p className="text-sm text-emerald-800 mt-0.5">
              Bất động sản &ldquo;{successInfo.title}&rdquo; đã được lưu và tạo vector tìm kiếm. Đang chuyển hướng đến trang chi tiết...
            </p>
          </div>
        </div>
      )}

      {/* Server Error Banner */}
      {serverError && (
        <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50/90 p-4 shadow-xs">
          <AlertCircle className="h-6 w-6 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-rose-900">Không thể đăng tin</h4>
            <p className="text-sm text-rose-800 mt-0.5">{serverError}</p>
          </div>
        </div>
      )}

      {/* Unauthenticated Banner Prompt */}
      {!isAuthLoading && !user && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-amber-200 bg-amber-50/90 p-4 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-amber-900">Yêu cầu đăng nhập</h4>
              <p className="text-xs text-amber-800 mt-0.5">
                Bạn cần đăng nhập tài khoản Space247 để đăng bài và quản lý bất động sản.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="inline-flex items-center rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-amber-700 transition"
            >
              Đăng nhập ngay
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center rounded-xl border border-amber-300 bg-white px-3.5 py-2 text-xs font-semibold text-amber-900 shadow-xs hover:bg-amber-50 transition"
            >
              Đăng ký
            </Link>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* SECTION 1: Category & Purpose */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <Tag className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">1. Hình thức & Loại hình bất động sản</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Listing Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Mục đích đăng tin <span className="text-rose-500">*</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setListingType("sale")}
                  className={`flex items-center justify-center gap-2 rounded-xl py-2.5 px-4 text-sm font-semibold transition border ${
                    listingType === "sale"
                      ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  Bán BĐS
                </button>
                <button
                  type="button"
                  onClick={() => setListingType("rent")}
                  className={`flex items-center justify-center gap-2 rounded-xl py-2.5 px-4 text-sm font-semibold transition border ${
                    listingType === "rent"
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  Cho thuê
                </button>
              </div>
            </div>

            {/* Property Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Loại hình bất động sản <span className="text-rose-500">*</span>
              </label>
              <select
                value={propertyType}
                onChange={(e) => setPropertyType(e.target.value as PropertyType)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="apartment">Căn hộ chung cư</option>
                <option value="house">Nhà phố / Nhà riêng</option>
                <option value="villa">Biệt thự / Liền kề</option>
                <option value="commercial">Mặt bằng kinh doanh / Shophouse</option>
                <option value="land">Đất nền / Thổ cư</option>
              </select>
            </div>
          </div>
        </div>

        {/* SECTION 2: Basic Content */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-semibold text-slate-900">2. Tiêu đề & Nội dung mô tả</h2>
            </div>
            <button
              type="button"
              onClick={() => setIsAiModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Soạn Tin (Agent Co-Pilot)</span>
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Tiêu đề bài đăng <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              placeholder="VD: Căn hộ Vinhomes 2PN view sông trực diện, full nội thất cao cấp..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:outline-hidden focus:ring-2 ${
                errors.title
                  ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/20"
                  : "border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
              }`}
            />
            {errors.title && <p className="mt-1 text-xs text-rose-500">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Mô tả chi tiết <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={5}
              placeholder="Mô tả kỹ về hiện trạng nhà, phong cách nội thất, hướng nhà, pháp lý, tiện ích xung quanh, lý do bán/cho thuê..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:outline-hidden focus:ring-2 ${
                errors.description
                  ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/20"
                  : "border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
              }`}
            />
            <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
              {errors.description ? (
                <span className="text-rose-500">{errors.description}</span>
              ) : (
                <span>Mô tả càng chi tiết giúp AI tìm kiếm khớp nhu cầu người mua hơn</span>
              )}
              <span>{description.length} ký tự</span>
            </div>
          </div>
        </div>

        {/* SECTION 3: Price & Dimensions */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <DollarSign className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">3. Giá bán & Thông số diện tích</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Price */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-slate-700">
                  Mức giá (VNĐ) <span className="text-rose-500">*</span>
                </label>
                {priceStr && !isNaN(parseFloat(priceStr.replace(/,/g, ""))) && (
                  <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">
                    {(() => {
                      const val = parseFloat(priceStr.replace(/,/g, ""));
                      if (val >= 1_000_000_000) return `${(val / 1_000_000_000).toFixed(2)} tỷ`;
                      if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)} triệu`;
                      return `${val.toLocaleString()} đ`;
                    })()}
                  </span>
                )}
              </div>
              <input
                type="number"
                placeholder={listingType === "sale" ? "6500000000" : "18000000"}
                value={priceStr}
                onChange={(e) => setPriceStr(e.target.value)}
                className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:outline-hidden focus:ring-2 ${
                  errors.price
                    ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/20"
                    : "border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
                }`}
              />
              {errors.price && <p className="mt-1 text-xs text-rose-500">{errors.price}</p>}
            </div>

            {/* Area */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Diện tích (m²) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="75.5"
                value={areaStr}
                onChange={(e) => setAreaStr(e.target.value)}
                className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:outline-hidden focus:ring-2 ${
                  errors.area_sqm
                    ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/20"
                    : "border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
                }`}
              />
              {errors.area_sqm && <p className="mt-1 text-xs text-rose-500">{errors.area_sqm}</p>}
            </div>

            {/* Bedrooms */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Số phòng ngủ
              </label>
              <input
                type="number"
                min="0"
                placeholder="2"
                value={bedroomsStr}
                onChange={(e) => setBedroomsStr(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.num_bedrooms && <p className="mt-1 text-xs text-rose-500">{errors.num_bedrooms}</p>}
            </div>

            {/* Bathrooms */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Số phòng tắm
              </label>
              <input
                type="number"
                min="0"
                placeholder="2"
                value={bathroomsStr}
                onChange={(e) => setBathroomsStr(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.num_bathrooms && <p className="mt-1 text-xs text-rose-500">{errors.num_bathrooms}</p>}
            </div>

            {/* Smart AVM Pricing Advisor */}
            <div className="sm:col-span-2 pt-2">
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

        {/* SECTION 4: Location */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <MapPin className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">4. Vị trí & Tọa độ bản đồ</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {/* City */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Tỉnh / Thành phố <span className="text-rose-500">*</span>
              </label>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              >
                {MAJOR_CITIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {errors.city && <p className="mt-1 text-xs text-rose-500">{errors.city}</p>}
            </div>

            {/* District */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Quận / Huyện
              </label>
              <input
                type="text"
                placeholder="VD: Quận Bình Thạnh, Cầu Giấy..."
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.district && <p className="mt-1 text-xs text-rose-500">{errors.district}</p>}
            </div>

            {/* Ward */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Phường / Xã
              </label>
              <input
                type="text"
                placeholder="VD: Phường 22, Dịch Vọng..."
                value={ward}
                onChange={(e) => setWard(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.ward && <p className="mt-1 text-xs text-rose-500">{errors.ward}</p>}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Địa chỉ số nhà / Tên đường <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              placeholder="VD: 208 Nguyễn Hữu Cảnh"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-slate-800 shadow-xs focus:outline-hidden focus:ring-2 ${
                errors.address
                  ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500/20"
                  : "border-slate-200 focus:border-blue-500 focus:ring-blue-500/20"
              }`}
            />
            {errors.address && <p className="mt-1 text-xs text-rose-500">{errors.address}</p>}
          </div>

          {/* Map Coordinates (Optional) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Tọa độ Latitude (Vĩ độ - Tùy chọn)
              </label>
              <input
                type="number"
                step="0.0001"
                placeholder="VD: 10.7954"
                value={latitudeStr}
                onChange={(e) => setLatitudeStr(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
              />
              {errors.latitude && <p className="mt-1 text-xs text-rose-500">{errors.latitude}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Tọa độ Longitude (Kinh độ - Tùy chọn)
              </label>
              <input
                type="number"
                step="0.0001"
                placeholder="VD: 106.7218"
                value={longitudeStr}
                onChange={(e) => setLongitudeStr(e.target.value)}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
              />
              {errors.longitude && <p className="mt-1 text-xs text-rose-500">{errors.longitude}</p>}
            </div>
          </div>
        </div>

        {/* SECTION 5: Amenities & Features */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <Layers className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">5. Tiện ích & Đặc điểm nổi bật</h2>
          </div>

          <div className="flex flex-wrap gap-2.5">
            {POPULAR_AMENITIES.map((amenity) => {
              const isSelected = selectedAmenities.includes(amenity);
              return (
                <button
                  type="button"
                  key={amenity}
                  onClick={() => toggleAmenity(amenity)}
                  className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-medium transition border ${
                    isSelected
                      ? "bg-blue-50 text-blue-700 border-blue-300 font-semibold"
                      : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />}
                  {amenity}
                </button>
              );
            })}
          </div>

          {/* Add custom amenity */}
          <div className="flex items-center gap-2 max-w-md pt-2">
            <input
              type="text"
              placeholder="Thêm tiện ích khác..."
              value={customAmenity}
              onChange={(e) => setCustomAmenity(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addCustomAmenity();
                }
              }}
              className="flex-1 rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-800 shadow-xs focus:border-blue-500 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={addCustomAmenity}
              className="inline-flex items-center gap-1 rounded-xl bg-slate-100 px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200 transition"
            >
              <Plus className="h-3.5 w-3.5" />
              Thêm
            </button>
          </div>
        </div>

        {/* SECTION 6: Images & Media */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
            <Upload className="h-5 w-5 text-blue-600" />
            <h2 className="text-base font-semibold text-slate-900">6. Hình ảnh bất động sản</h2>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`rounded-2xl border-2 border-dashed p-6 text-center transition ${
              isDragging
                ? "border-blue-500 bg-blue-50/60"
                : "border-slate-200 bg-slate-50/50 hover:border-blue-400"
            }`}
          >
            <Upload className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-700">
              {isDragging ? "Thả ảnh vào đây..." : "Chọn ảnh từ máy tính hoặc kéo thả ảnh vào đây"}
            </p>
            <p className="text-xs text-slate-500 mt-1">Hỗ trợ PNG, JPG, WebP tối đa 10MB</p>
            <label className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-semibold text-blue-600 border border-slate-200 shadow-xs hover:bg-blue-50 transition">
              <span>Tải ảnh lên</span>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageFileChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Uploaded Images Preview */}
          {uploadedImages.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              {uploadedImages.map((src, index) => (
                <div key={index} className="group relative aspect-4/3 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 shadow-xs">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={src} alt={`Preview ${index + 1}`} className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="absolute top-1.5 right-1.5 rounded-full bg-slate-900/70 p-1 text-white hover:bg-rose-600 transition"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-4 pt-4 border-t border-slate-200">
          <Link
            href="/"
            className="rounded-xl px-5 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
          >
            Hủy bỏ
          </Link>
          <button
            type="submit"
            disabled={isPending}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-7 py-3 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {isPending ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                <span>Đang xử lý & tạo Vector AI...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Hoàn tất & Đăng tin</span>
              </>
            )}
          </button>
        </div>
      </form>

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
