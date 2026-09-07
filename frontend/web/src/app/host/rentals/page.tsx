"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  DoorOpen,
  PlusCircle,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  Calendar,
  AlertCircle,
  Layers,
  MapPin,
  RefreshCw,
} from "lucide-react";
import type {
  LandlordDashboardStats,
  RentalInquiry,
  RentalProperty,
  RentalUnit,
} from "@shared/types";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LandlordDashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<LandlordDashboardStats | null>(null);
  const [properties, setProperties] = useState<RentalProperty[]>([]);
  const [inquiries, setInquiries] = useState<RentalInquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [togglingUnitId, setTogglingUnitId] = useState<string | null>(null);

  async function loadDashboardData() {
    setLoading(true);
    setError("");
    try {
      const [statsData, propsData, inqsData] = await Promise.all([
        apiClient.getLandlordStats(),
        apiClient.getHostProperties(),
        apiClient.getHostInquiries(),
      ]);
      setStats(statsData);
      setProperties(propsData);
      setInquiries(inqsData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể tải dữ liệu kênh chủ nhà");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const handleToggleUnitStatus = async (unit: RentalUnit) => {
    setTogglingUnitId(unit.id);
    const newStatus = unit.status === "available" ? "occupied" : "available";
    try {
      await apiClient.updateRentalUnitStatus(unit.id, newStatus);
      // Reload stats and properties to reflect occupancy update
      await loadDashboardData();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Lỗi khi cập nhật trạng thái phòng");
    } finally {
      setTogglingUnitId(null);
    }
  };

  const handleInquiryAction = async (inquiryId: string, status: "confirmed" | "rejected") => {
    try {
      await apiClient.updateInquiryStatus(inquiryId, status);
      await loadDashboardData();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Lỗi cập nhật yêu cầu");
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1">
              Host Management Portal
            </span>
            <span className="text-slate-400 text-xs">•</span>
            <span className="text-slate-500 text-xs">Không gian dành cho Chủ nhà</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900">Bảng điều khiển quản lý phòng trọ</h1>
          <p className="text-slate-500 text-sm mt-1">
            Bật/tắt trạng thái phòng 1-click, theo dõi công suất phòng và phản hồi lịch hẹn khách thuê
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadDashboardData}
            className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 hover:bg-slate-50 shadow-xs"
            title="Làm mới dữ liệu"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/host/rentals/new"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-xs hover:bg-blue-700 transition"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Thêm khu trọ mới</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase">
            <span>Tổng số phòng</span>
            <Building2 className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">
            {stats ? stats.total_units : "--"}
          </div>
          <p className="text-xs text-slate-400">
            {stats ? `${stats.total_properties} khu nhà đang vận hành` : ""}
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase">
            <span>Phòng còn trống</span>
            <DoorOpen className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-600">
            {stats ? stats.available_units : "--"}
          </div>
          <p className="text-xs text-slate-400">
            {stats ? `Đã thuê: ${stats.occupied_units} phòng` : ""}
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase">
            <span>Tỷ lệ lấp đầy</span>
            <TrendingUp className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-extrabold text-indigo-600">
            {stats ? `${stats.occupancy_rate}%` : "--"}
          </div>
          <p className="text-xs text-slate-400">Công suất khai thác thực tế</p>
        </div>

        <div className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase">
            <span>Doanh thu dự kiến</span>
            <Clock className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">
            {stats ? `${stats.estimated_monthly_revenue.toLocaleString("vi-VN")} đ` : "--"}
          </div>
          <p className="text-xs text-slate-400">Từ các phòng đang cho thuê</p>
        </div>
      </div>

      {/* Main Grid: Properties & Units Table + Inquiries Inbox */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left 2 Cols: Properties & Unit Quick-Toggle */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">Danh sách khu trọ & Trình quản lý phòng</h2>
            <span className="text-xs text-slate-500">{properties.length} khu nhà</span>
          </div>

          {properties.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 p-8 text-center bg-slate-50/50 space-y-3">
              <Building2 className="h-10 w-10 text-slate-400 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">Chưa có khu trọ nào</h3>
              <p className="text-xs text-slate-500">
                Hãy bắt đầu đăng ký tòa nhà, khu phòng trọ hoặc homestay đầu tiên của bạn.
              </p>
              <Link
                href="/host/rentals/new"
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-xs"
              >
                <PlusCircle className="h-4 w-4" /> Thêm khu trọ ngay
              </Link>
            </div>
          ) : (
            properties.map((prop) => (
              <div
                key={prop.id}
                className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="rounded-md bg-blue-50 text-blue-700 text-[10px] font-bold px-2 py-0.5 uppercase">
                      {prop.property_model === "boarding_house"
                        ? "Phòng trọ"
                        : prop.property_model === "serviced_apartment"
                        ? "Căn hộ dịch vụ"
                        : "Homestay"}
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 mt-1">{prop.name}</h3>
                    <p className="flex items-center gap-1 text-xs text-slate-500">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      <span>{[prop.address, prop.ward, prop.district, prop.city].filter(Boolean).join(", ")}</span>
                    </p>
                  </div>

                  <Link
                    href={`/rentals/${prop.id}`}
                    className="text-xs font-semibold text-blue-600 hover:underline"
                  >
                    Xem trang khách thuê
                  </Link>
                </div>

                {/* Units List with 1-Click Status Toggle */}
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Các phòng ({prop.units.length} phòng)
                  </h4>

                  <div className="grid gap-2 sm:grid-cols-2">
                    {prop.units.map((unit) => {
                      const isAvailable = unit.status === "available";
                      const isToggling = togglingUnitId === unit.id;

                      return (
                        <div
                          key={unit.id}
                          className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-xs"
                        >
                          <div>
                            <span className="font-extrabold text-slate-900 text-sm">
                              {unit.unit_number}
                            </span>
                            <span className="text-slate-400 text-[11px] block">
                              {unit.area_sqm} m² • {unit.price.toLocaleString("vi-VN")} đ
                            </span>
                          </div>

                          <button
                            onClick={() => handleToggleUnitStatus(unit)}
                            disabled={isToggling}
                            className={`rounded-xl px-3 py-1.5 font-bold transition flex items-center gap-1.5 ${
                              isAvailable
                                ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                                : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                            }`}
                            title="Bấm để đổi trạng thái Trống <-> Đã thuê"
                          >
                            <span
                              className={`h-2 w-2 rounded-full ${
                                isAvailable ? "bg-emerald-500" : "bg-slate-500"
                              }`}
                            />
                            <span>{isAvailable ? "Còn trống" : "Đã thuê"}</span>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right 1 Col: Inquiries & Appointments Inbox */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">Yêu cầu & Lịch hẹn</h2>
            {stats && (
              <span className="rounded-full bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-0.5">
                {stats.pending_inquiries_count} mới
              </span>
            )}
          </div>

          <div className="space-y-3">
            {inquiries.length === 0 ? (
              <div className="rounded-3xl border border-slate-200 bg-white p-6 text-center text-xs text-slate-400">
                Chưa có yêu cầu xem phòng nào từ khách thuê.
              </div>
            ) : (
              inquiries.map((inq) => (
                <div
                  key={inq.id}
                  className="rounded-3xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-3 text-xs"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-bold text-slate-900 text-sm">{inq.tenant_name}</span>
                      <p className="text-slate-500">{inq.tenant_phone}</p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 font-bold text-[10px] uppercase ${
                        inq.status === "confirmed"
                          ? "bg-emerald-100 text-emerald-800"
                          : inq.status === "rejected"
                          ? "bg-red-100 text-red-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {inq.status === "confirmed"
                        ? "Đã xác nhận"
                        : inq.status === "rejected"
                        ? "Từ chối"
                        : "Chờ duyệt"}
                    </span>
                  </div>

                  {inq.unit && (
                    <div className="rounded-xl bg-slate-50 p-2 text-slate-600">
                      Phòng: <strong>{inq.unit.unit_number}</strong> ({inq.unit.area_sqm} m²)
                    </div>
                  )}

                  {inq.scheduled_time && (
                    <p className="flex items-center gap-1.5 text-blue-700 font-medium">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{new Date(inq.scheduled_time).toLocaleString("vi-VN")}</span>
                    </p>
                  )}

                  {inq.message && <p className="text-slate-600 italic">"{inq.message}"</p>}

                  {inq.status === "pending" && (
                    <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => handleInquiryAction(inq.id, "confirmed")}
                        className="flex-1 rounded-xl bg-emerald-600 py-1.5 font-bold text-white hover:bg-emerald-700 transition"
                      >
                        Xác nhận
                      </button>
                      <button
                        onClick={() => handleInquiryAction(inq.id, "rejected")}
                        className="flex-1 rounded-xl border border-slate-200 py-1.5 font-semibold text-slate-600 hover:bg-slate-50 transition"
                      >
                        Từ chối
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
