"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  MapPin,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Sparkles,
  PawPrint,
  Layers,
  Bath,
  Maximize2,
  ShieldCheck,
  DoorOpen,
  ArrowLeft,
  X,
  Phone,
  Send,
} from "lucide-react";
import type { RentalProperty, RentalUnit } from "@shared/types";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function RentalPropertyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const propertyId = resolvedParams.id;
  const { user } = useAuth();

  const [property, setProperty] = useState<RentalProperty | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Inquiry Modal State
  const [selectedUnit, setSelectedUnit] = useState<RentalUnit | null>(null);
  const [inquiryType, setInquiryType] = useState<"view_appointment" | "booking_request">("view_appointment");
  const [scheduledDate, setScheduledDate] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [tenantPhone, setTenantPhone] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [inquirySuccess, setInquirySuccess] = useState(false);

  useEffect(() => {
    async function fetchDetails() {
      setLoading(true);
      try {
        const res = await apiClient.getRentalProperty(propertyId);
        setProperty(res);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Không thể tải thông tin khu trọ");
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
  }, [propertyId]);

  useEffect(() => {
    if (user) {
      setTenantName(user.full_name || "");
      setTenantPhone(user.phone || "");
    }
  }, [user]);

  const handleInquireSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUnit) return;
    setSubmitting(true);
    try {
      await apiClient.inquireRentalUnit(selectedUnit.id, {
        inquiry_type: inquiryType,
        scheduled_time: scheduledDate ? new Date(scheduledDate).toISOString() : undefined,
        tenant_name: tenantName,
        tenant_phone: tenantPhone,
        message: message,
      });
      setInquirySuccess(true);
      setTimeout(() => {
        setInquirySuccess(false);
        setSelectedUnit(null);
      }, 2500);
    } catch (cause) {
      alert(cause instanceof Error ? cause.message : "Không thể gửi yêu cầu");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center text-slate-500">
        <p className="animate-pulse">Đang tải chi tiết khu trọ & danh sách phòng...</p>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center space-y-4">
        <p className="text-red-600 font-semibold">{error || "Không tìm thấy khu trọ"}</p>
        <Link href="/rentals" className="inline-flex items-center gap-2 text-blue-600 font-bold hover:underline">
          <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
        </Link>
      </div>
    );
  }

  const isHomestay = property.property_model === "homestay";
  const priceUnit = isHomestay ? "/đêm" : "/tháng";
  const costs = property.shared_costs || {};
  const rules = property.shared_rules || {};

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-xs text-slate-500">
        <Link href="/rentals" className="hover:text-blue-600 transition">
          Cho thuê
        </Link>
        <span>/</span>
        <span className="text-slate-800 font-medium truncate max-w-[200px]">{property.name}</span>
      </nav>

      {/* Main Header Banner */}
      <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1">
                {property.property_model === "homestay"
                  ? "Homestay"
                  : property.property_model === "serviced_apartment"
                  ? "Căn hộ dịch vụ"
                  : "Khu nhà trọ"}
              </span>
              {property.available_units_count > 0 ? (
                <span className="rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1">
                  Còn {property.available_units_count} phòng trống
                </span>
              ) : (
                <span className="rounded-full bg-slate-100 text-slate-600 text-xs font-medium px-3 py-1">
                  Đã hết phòng
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">{property.name}</h1>
            <p className="flex items-center gap-1.5 text-sm text-slate-600">
              <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
              <span>{[property.address, property.ward, property.district, property.city].filter(Boolean).join(", ")}</span>
            </p>
          </div>

          {/* Host Card Preview */}
          {property.host && (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-lg">
                {property.host.full_name?.slice(0, 1) || "H"}
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Chủ nhà (Host)</span>
                <h4 className="text-sm font-bold text-slate-900">{property.host.full_name}</h4>
                <p className="text-xs text-slate-500">{property.host.phone || "Liên hệ qua Space247"}</p>
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {property.description && (
          <div className="pt-4 border-t border-slate-100 text-sm text-slate-700 leading-relaxed">
            {property.description}
          </div>
        )}
      </div>

      {/* Grid: Shared Fees & Shared Rules */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Transparent Utility Costs */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            <span>Biểu phí sinh hoạt minh bạch</span>
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-2xl bg-slate-50 p-3.5">
              <span className="text-xs text-slate-500 block">Tiền điện</span>
              <strong className="text-slate-900 font-bold">
                {costs.electricity_per_kwh != null
                  ? `${costs.electricity_per_kwh.toLocaleString("vi-VN")} đ/kWh`
                  : costs.electricity_billing === "state_rate"
                  ? "Giá nhà nước"
                  : "Chưa cung cấp"}
              </strong>
            </div>

            <div className="rounded-2xl bg-slate-50 p-3.5">
              <span className="text-xs text-slate-500 block">Tiền nước</span>
              <strong className="text-slate-900 font-bold">
                {costs.water_cost != null
                  ? `${costs.water_cost.toLocaleString("vi-VN")} đ/${costs.water_unit === "per_person" ? "người" : "m³"}`
                  : "Chưa cung cấp"}
              </strong>
            </div>

            <div className="rounded-2xl bg-slate-50 p-3.5">
              <span className="text-xs text-slate-500 block">Phí gửi xe</span>
              <strong className="text-slate-900 font-bold">
                {costs.parking_fee_monthly != null
                  ? `${costs.parking_fee_monthly.toLocaleString("vi-VN")} đ/tháng`
                  : "Miễn phí / Chưa có"}
              </strong>
            </div>

            <div className="rounded-2xl bg-slate-50 p-3.5">
              <span className="text-xs text-slate-500 block">Wifi & Dịch vụ</span>
              <strong className="text-slate-900 font-bold">
                {costs.wifi_fee != null
                  ? `${costs.wifi_fee.toLocaleString("vi-VN")} đ/tháng`
                  : "Miễn phí"}
              </strong>
            </div>
          </div>
        </section>

        {/* Shared Rules */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            <span>Nội quy & Tiện ích tòa nhà</span>
          </h2>
          <div className="grid grid-cols-2 gap-3 text-xs font-semibold">
            <div className="flex items-center gap-2 rounded-xl border border-slate-100 p-3 text-slate-700">
              <Clock className="h-4 w-4 text-blue-600" />
              <span>{rules.curfew === false ? "Giờ giấc tự do 24/7" : rules.curfew_time ? `Giới nghiêm ${rules.curfew_time}` : "Có giờ đóng cửa"}</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-100 p-3 text-slate-700">
              <PawPrint className="h-4 w-4 text-amber-600" />
              <span>{rules.allow_pets ? "Cho phép nuôi thú cưng" : "Không nuôi thú cưng"}</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-100 p-3 text-slate-700">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>{rules.fingerprint_lock ? "Khóa cổng vân tay" : "Khóa cổng chìa cơ"}</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-100 p-3 text-slate-700">
              <DoorOpen className="h-4 w-4 text-indigo-600" />
              <span>{rules.live_with_owner === false ? "Không chung chủ" : "Chung chủ"}</span>
            </div>
          </div>
        </section>
      </div>

      {/* Available Units Section */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900">
            Danh sách phòng & căn hộ ({(property.units || []).length} phòng)
          </h2>
          <p className="text-slate-500 text-xs">
            Xem thực tế trạng thái phòng còn trống để đặt lịch hẹn hoặc giữ chỗ
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(property.units || []).map((unit) => {
            const isAvailable = unit.status === "available";

            return (
              <div
                key={unit.id}
                className={`rounded-3xl border p-5 space-y-4 transition ${
                  isAvailable
                    ? "border-slate-200 bg-white shadow-xs hover:border-blue-400 hover:shadow-md"
                    : "border-slate-100 bg-slate-50 opacity-70"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-400">Phòng</span>
                    <h3 className="text-lg font-extrabold text-slate-900">{unit.unit_number}</h3>
                    {unit.floor != null && <p className="text-xs text-slate-500">Tầng {unit.floor}</p>}
                  </div>

                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                      unit.status === "available"
                        ? "bg-emerald-100 text-emerald-800"
                        : unit.status === "occupied"
                        ? "bg-slate-200 text-slate-600"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {unit.status === "available"
                      ? "Còn trống"
                      : unit.status === "occupied"
                      ? "Đã thuê"
                      : "Đang giữ chỗ"}
                  </span>
                </div>

                {/* Unit Amenities */}
                <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                  <span className="flex items-center gap-1">
                    <Maximize2 className="h-3.5 w-3.5 text-slate-400" />
                    {unit.area_sqm} m²
                  </span>
                  {unit.has_mezzanine && (
                    <span className="flex items-center gap-1 text-blue-700 font-medium">
                      <Layers className="h-3.5 w-3.5" /> Có gác lửng
                    </span>
                  )}
                  {unit.has_private_bathroom && (
                    <span className="flex items-center gap-1 text-slate-600">
                      <Bath className="h-3.5 w-3.5" /> WC khép kín
                    </span>
                  )}
                  <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px]">
                    {unit.furnishing === "full"
                      ? "Full nội thất"
                      : unit.furnishing === "basic"
                      ? "Nội thất cơ bản"
                      : "Phòng trống"}
                  </span>
                </div>

                {/* Unit Price & CTA */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Giá thuê</span>
                    <div className="text-base font-extrabold text-blue-600">
                      {unit.price.toLocaleString("vi-VN")} đ
                      <span className="text-xs font-normal text-slate-500">{priceUnit}</span>
                    </div>
                  </div>

                  {isAvailable ? (
                    <button
                      onClick={() => setSelectedUnit(unit)}
                      className="rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition"
                    >
                      Đặt lịch xem
                    </button>
                  ) : (
                    <span className="text-xs text-slate-400 font-medium">Không khả dụng</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Booking / Appointment Modal */}
      {selectedUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Đặt lịch hẹn / Giữ chỗ</h3>
                <p className="text-xs text-slate-500">
                  Phòng <strong>{selectedUnit.unit_number}</strong> • {property.name}
                </p>
              </div>
              <button
                onClick={() => setSelectedUnit(null)}
                className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {inquirySuccess ? (
              <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-6 text-center space-y-2">
                <CheckCircle2 className="h-10 w-10 text-emerald-600 mx-auto" />
                <h4 className="text-base font-bold text-emerald-900">Gửi yêu cầu thành công!</h4>
                <p className="text-xs text-emerald-700">
                  Chủ nhà đã nhận được thông tin hẹn và sẽ liên hệ xác nhận sớm nhất.
                </p>
              </div>
            ) : (
              <form onSubmit={handleInquireSubmit} className="space-y-4 text-sm">
                {/* Inquiry Type Radio */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700 uppercase">Hình thức yêu cầu</label>
                  <div className="grid grid-cols-2 gap-2">
                    <label
                      className={`flex items-center gap-2 rounded-xl border p-3 cursor-pointer ${
                        inquiryType === "view_appointment"
                          ? "border-blue-600 bg-blue-50 text-blue-900 font-semibold"
                          : "border-slate-200 text-slate-700"
                      }`}
                    >
                      <input
                        type="radio"
                        name="inquiry_type"
                        value="view_appointment"
                        checked={inquiryType === "view_appointment"}
                        onChange={() => setInquiryType("view_appointment")}
                        className="hidden"
                      />
                      <Clock className="h-4 w-4 text-blue-600" />
                      <span>Hẹn xem phòng</span>
                    </label>

                    <label
                      className={`flex items-center gap-2 rounded-xl border p-3 cursor-pointer ${
                        inquiryType === "booking_request"
                          ? "border-blue-600 bg-blue-50 text-blue-900 font-semibold"
                          : "border-slate-200 text-slate-700"
                      }`}
                    >
                      <input
                        type="radio"
                        name="inquiry_type"
                        value="booking_request"
                        checked={inquiryType === "booking_request"}
                        onChange={() => setInquiryType("booking_request")}
                        className="hidden"
                      />
                      <Calendar className="h-4 w-4 text-emerald-600" />
                      <span>Yêu cầu giữ chỗ</span>
                    </label>
                  </div>
                </div>

                {/* Scheduled Time */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">Thời gian mong muốn</label>
                  <input
                    type="datetime-local"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-sm"
                  />
                </div>

                {/* Tenant Contact */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-700">Họ và tên</label>
                    <input
                      type="text"
                      required
                      placeholder="Nguyễn Văn A"
                      value={tenantName}
                      onChange={(e) => setTenantName(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 p-2.5 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-slate-700">Số điện thoại</label>
                    <input
                      type="tel"
                      required
                      placeholder="0912345678"
                      value={tenantPhone}
                      onChange={(e) => setTenantPhone(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 p-2.5 text-sm"
                    />
                  </div>
                </div>

                {/* Message */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">Ghi chú gửi chủ nhà</label>
                  <textarea
                    rows={3}
                    placeholder="Ví dụ: Em muốn xem phòng vào buổi tối sau 18h hoặc cuối tuần..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-sm"
                  />
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedUnit(null)}
                    className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>{submitting ? "Đang gửi..." : "Gửi yêu cầu"}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
