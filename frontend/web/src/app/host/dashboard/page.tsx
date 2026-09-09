"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  DoorOpen,
  TrendingUp,
  AlertCircle,
  Calendar,
  Zap,
  Droplet,
  Bell,
  Send,
  FileText,
  CheckCircle2,
  Clock,
  Plus,
  RefreshCw,
  Users,
  Wallet,
  AlertTriangle,
} from "lucide-react";
import type {
  HostDashboardStats,
  RentalContract,
  MonthlyInvoice,
  MeterReadingInput,
  RentalInquiry,
  ViewingScheduleWindow,
} from "@shared/types";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/utils";

export default function HostDashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<HostDashboardStats | null>(null);
  const [contracts, setContracts] = useState<RentalContract[]>([]);
  const [invoices, setInvoices] = useState<MonthlyInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [viewingSchedule, setViewingSchedule] = useState<ViewingScheduleWindow[]>([]);
  const [viewingInquiries, setViewingInquiries] = useState<RentalInquiry[]>([]);

  // Invoice filtering
  const [invoiceFilter, setInvoiceFilter] = useState<"all" | "pending" | "paid" | "overdue">("all");
  const [remindingId, setRemindingId] = useState<string | null>(null);

  // Meter Reading Form State
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState("");
  const currentMonthStr = new Date().toISOString().slice(0, 7); // YYYY-MM
  const [billingMonth, setBillingMonth] = useState(currentMonthStr);
  const [elecPrev, setElecPrev] = useState<number>(0);
  const [elecCurr, setElecCurr] = useState<number>(0);
  const [waterPrev, setWaterPrev] = useState<number>(0);
  const [waterCurr, setWaterCurr] = useState<number>(0);
  const [readingNotes, setReadingNotes] = useState("");
  const [generatingInvoices, setGeneratingInvoices] = useState(false);
  const [invoiceFormError, setInvoiceFormError] = useState("");

  async function loadDashboardData() {
    setLoading(true);
    setError("");
    try {
      const [statsData, contractsData, invoicesData, scheduleData, inquiriesData] = await Promise.all([
        apiClient.getHostDashboardStats(),
        apiClient.getHostContracts(),
        apiClient.getHostInvoices(),
        apiClient.getViewingSchedule(),
        apiClient.getHostInquiries(),
      ]);
      setStats(statsData);
      setContracts(contractsData);
      setInvoices(invoicesData);
      setViewingSchedule(scheduleData);
      setViewingInquiries(inquiriesData.filter((item) => item.inquiry_type === "view_appointment"));
      if (contractsData.length > 0 && !selectedContractId) {
        setSelectedContractId(contractsData[0].id);
      }
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

  // Selected contract details for meter reading calculations
  const selectedContract = contracts.find((c) => c.id === selectedContractId);
  const elecUnits = Math.max(0, elecCurr - elecPrev);
  const elecRate = selectedContract?.electricity_rate || 3500;
  const elecCost = elecUnits * elecRate;

  const waterUnits = Math.max(0, waterCurr - waterPrev);
  const waterRate = selectedContract?.water_rate || 20000;
  const occupants = selectedContract?.unit?.max_occupants || 1;
  const waterCost = selectedContract?.water_billing_type === "per_person"
    ? waterRate * occupants
    : waterUnits * waterRate;

  const roomRent = selectedContract?.rental_price || 0;
  const serviceFee = selectedContract?.service_fee || 0;
  const estimatedTotal = roomRent + elecCost + waterCost + serviceFee;

  const handleGenerateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedContractId) {
      setInvoiceFormError("Vui lòng chọn hợp đồng cho thuê");
      return;
    }
    if (elecCurr < elecPrev) {
      setInvoiceFormError("Chỉ số điện mới phải lớn hơn hoặc bằng chỉ số cũ");
      return;
    }
    if (waterCurr < waterPrev) {
      setInvoiceFormError("Chỉ số nước mới phải lớn hơn hoặc bằng chỉ số cũ");
      return;
    }

    setGeneratingInvoices(true);
    setInvoiceFormError("");
    try {
      const reading: MeterReadingInput = {
        contract_id: selectedContractId,
        electricity_previous: Number(elecPrev),
        electricity_current: Number(elecCurr),
        water_previous: Number(waterPrev),
        water_current: Number(waterCurr),
        notes: readingNotes || undefined,
      };

      await apiClient.generateMonthlyInvoices({
        billing_month: billingMonth,
        readings: [reading],
        due_days: 5,
      });

      setSuccessMessage(`Đã lập hóa đơn tháng ${billingMonth} thành công!`);
      setShowInvoiceModal(false);
      // Reset form
      setElecPrev(elecCurr);
      setWaterPrev(waterCurr);
      setReadingNotes("");
      await loadDashboardData();
      setTimeout(() => setSuccessMessage(""), 5000);
    } catch (err) {
      setInvoiceFormError(err instanceof Error ? err.message : "Lỗi lập hóa đơn");
    } finally {
      setGeneratingInvoices(false);
    }
  };

  const updateViewingSchedule = async (windows: ViewingScheduleWindow[]) => {
    try {
      setViewingSchedule(await apiClient.replaceViewingSchedule(windows));
      setSuccessMessage("Đã lưu lịch nhận khách xem phòng");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể lưu lịch xem phòng");
    }
  };

  const confirmViewing = async (inquiryId: string) => {
    try {
      await apiClient.confirmViewing(inquiryId);
      await loadDashboardData();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể xác nhận lịch hẹn");
    }
  };

  const handleSendReminder = async (invoiceId: string) => {
    setRemindingId(invoiceId);
    try {
      const res = await apiClient.sendInvoiceReminder(invoiceId);
      setSuccessMessage(res.message || "Đã gửi thông báo nhắc nợ thành công tới khách thuê!");
      await loadDashboardData();
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Không thể gửi nhắc nhở");
    } finally {
      setRemindingId(null);
    }
  };

  const filteredInvoices = invoices.filter((inv) => {
    if (invoiceFilter === "all") return true;
    return inv.status === invoiceFilter;
  });

  if (loading && !stats) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-3" />
        <p className="text-slate-600 font-medium">Đang tải dữ liệu Bảng điều khiển Chủ nhà...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Building2 className="w-8 h-8 text-blue-600" />
            Bảng điều khiển Chủ nhà & Quản lý Thu phí
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Theo dõi phòng trọ, chốt chỉ số điện nước hàng tháng, phát hành hóa đơn và nhắc nợ tự động qua VietQR.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadDashboardData()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 transition"
          >
            <RefreshCw className="w-4 h-4 text-slate-500" />
            Làm mới
          </button>
          <button
            onClick={() => setShowInvoiceModal(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition"
          >
            <Plus className="w-4 h-4" />
            Lập Hóa đơn Điện Nước
          </button>
        </div>
      </div>

      {/* Success Notification Alert */}
      {successMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 flex items-center gap-3 text-emerald-800 shadow-xs animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span className="text-sm font-medium">{successMessage}</span>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 flex items-center gap-3 text-rose-800 shadow-xs">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {/* Total Properties & Units */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Tổng BĐS & Phòng</span>
            <Building2 className="w-5 h-5 text-blue-600" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-slate-900">
              {stats?.total_properties ?? 0} <span className="text-sm font-normal text-slate-500">khu trọ</span>
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {stats?.total_units ?? 0} phòng quản lý
            </div>
          </div>
        </div>

        {/* Occupancy Rate */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Tỷ lệ lấp đầy</span>
            <DoorOpen className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-emerald-700">
              {stats?.occupancy_rate ?? 0}%
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className="bg-emerald-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, stats?.occupancy_rate ?? 0))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Estimated Monthly Revenue */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Doanh thu dự kiến</span>
            <Wallet className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-indigo-900">
              {formatPrice(stats?.estimated_monthly_revenue ?? 0, "VND", "rent")}
            </div>
            <div className="text-xs text-slate-500 mt-1">Từ các phòng đang thuê</div>
          </div>
        </div>

        {/* Unpaid Invoices */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Hóa đơn chưa thu</span>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <div className="mt-4">
            <div className={`text-2xl font-bold ${
              (stats?.unpaid_invoices_count ?? 0) > 0 ? "text-amber-700" : "text-slate-900"
            }`}>
              {stats?.unpaid_invoices_count ?? 0}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {(stats?.unpaid_invoices_count ?? 0) > 0 ? "Cần đôn đốc nhắc nợ" : "Tất cả đã thanh toán"}
            </div>
          </div>
        </div>

        {/* Pending Inquiries */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Yêu cầu thuê chờ duyệt</span>
            <Clock className="w-5 h-5 text-violet-600" />
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold text-violet-700">
              {stats?.pending_inquiries_count ?? 0}
            </div>
            <Link
              href="/host/rentals"
              className="text-xs font-semibold text-blue-600 hover:underline mt-1 inline-block"
            >
              Xem danh sách phòng &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content Layout: Invoices & Active Contracts */}
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
          <h2 className="text-lg font-bold text-slate-900">Lịch nhận khách xem phòng</h2>
          <p className="mt-1 text-xs text-slate-500">Thứ Hai là 0. Khung giờ chỉ hiển thị khi bật.</p>
          <div className="mt-4 space-y-2">{[0, 1, 2, 3, 4, 5, 6].map((weekday) => {
            const window = viewingSchedule.find((item) => item.weekday === weekday);
            return <div key={weekday} className="flex items-center gap-3 text-sm"><span className="w-16 text-slate-600">Thứ {weekday + 2}</span><input type="time" defaultValue={window?.start_time?.slice(0, 5) ?? "09:00"} onBlur={(e) => updateViewingSchedule([...viewingSchedule.filter((item) => item.weekday !== weekday), { weekday, start_time: e.currentTarget.value, end_time: window?.end_time?.slice(0, 5) ?? "17:00", slot_duration_minutes: window?.slot_duration_minutes ?? 30, is_active: window?.is_active ?? false }])} className="rounded border p-1" /><input type="time" defaultValue={window?.end_time?.slice(0, 5) ?? "17:00"} onBlur={(e) => updateViewingSchedule([...viewingSchedule.filter((item) => item.weekday !== weekday), { weekday, start_time: window?.start_time?.slice(0, 5) ?? "09:00", end_time: e.currentTarget.value, slot_duration_minutes: window?.slot_duration_minutes ?? 30, is_active: window?.is_active ?? false }])} className="rounded border p-1" /><label className="text-xs"><input type="checkbox" checked={window?.is_active ?? false} onChange={(e) => updateViewingSchedule([...viewingSchedule.filter((item) => item.weekday !== weekday), { weekday, start_time: window?.start_time?.slice(0, 5) ?? "09:00", end_time: window?.end_time?.slice(0, 5) ?? "17:00", slot_duration_minutes: window?.slot_duration_minutes ?? 30, is_active: e.target.checked }])} /> Mở lịch</label></div>;
          })}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs"><h2 className="text-lg font-bold text-slate-900">Lịch hẹn xem phòng</h2><div className="mt-4 space-y-3">{viewingInquiries.length === 0 ? <p className="text-sm text-slate-500">Chưa có lịch hẹn.</p> : viewingInquiries.map((item) => <div key={item.id} className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-sm"><span>{item.tenant_name || "Khách thuê"} · {item.appointment_date} {item.start_time?.slice(0, 5)}</span>{item.status === "pending" ? <button onClick={() => confirmViewing(item.id)} className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white">Xác nhận</button> : <span className="text-xs font-semibold text-emerald-700">Đã xác nhận</span>}</div>)}</div></div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Monthly Invoices & Debt Reminders */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  Hóa đơn Điện Nước & Thu Phí Hàng Tháng
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Danh sách hóa đơn được tạo theo chỉ số đồng hồ điện nước của từng hợp đồng
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium">
                {(["all", "pending", "overdue", "paid"] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setInvoiceFilter(filter)}
                    className={`px-3 py-1.5 rounded-lg capitalize transition ${
                      invoiceFilter === filter
                        ? "bg-white text-blue-600 shadow-2xs font-semibold"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {filter === "all" && "Tất cả"}
                    {filter === "pending" && "Chờ thanh toán"}
                    {filter === "overdue" && "Quá hạn"}
                    {filter === "paid" && "Đã thu"}
                  </button>
                ))}
              </div>
            </div>

            {/* Invoices List */}
            {filteredInvoices.length === 0 ? (
              <div className="py-12 text-center text-slate-500">
                <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" />
                <p className="font-medium text-sm">Chưa có hóa đơn nào phù hợp với bộ lọc</p>
                <p className="text-xs text-slate-400 mt-1">
                  Nhấn &quot;Lập Hóa đơn Điện Nước&quot; ở trên để ghi chỉ số và xuất hóa đơn mới.
                </p>
              </div>
            ) : (
              <div className="mt-4 divide-y divide-slate-100">
                {filteredInvoices.map((inv) => (
                  <div key={inv.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900">
                          Tháng {inv.billing_month}
                        </span>
                        <span
                          className={`px-2 py-0.5 text-[11px] font-semibold rounded-md ${
                            inv.status === "paid"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : inv.status === "overdue"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {inv.status === "paid" && "Đã thanh toán"}
                          {inv.status === "overdue" && "Quá hạn nộp"}
                          {inv.status === "pending" && "Chờ thanh toán"}
                        </span>
                      </div>

                      <div className="text-xs text-slate-600 flex flex-wrap items-center gap-x-4 gap-y-1">
                        <span>Tiền phòng: {formatPrice(inv.room_amount, "VND", "rent")}</span>
                        <span className="flex items-center gap-1">
                          <Zap className="w-3.5 h-3.5 text-amber-500" />
                          Điện ({inv.electricity_current_index - inv.electricity_previous_index} kWh):{" "}
                          {formatPrice(inv.electricity_amount, "VND", "rent")}
                        </span>
                        <span className="flex items-center gap-1">
                          <Droplet className="w-3.5 h-3.5 text-blue-500" />
                          Nước: {formatPrice(inv.water_amount, "VND", "rent")}
                        </span>
                        {inv.service_amount > 0 && (
                          <span>Dịch vụ: {formatPrice(inv.service_amount, "VND", "rent")}</span>
                        )}
                      </div>

                      <div className="text-[11px] text-slate-400 flex items-center gap-3 mt-1">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" /> Hạn nộp: {inv.due_date}
                        </span>
                        {inv.last_reminded_at && (
                          <span className="flex items-center gap-1 text-slate-500">
                            <Clock className="w-3 h-3" /> Đã nhắc lúc:{" "}
                            {new Date(inv.last_reminded_at).toLocaleTimeString("vi-VN", {
                              hour: "2-digit",
                              minute: "2-digit",
                              day: "2-digit",
                              month: "2-digit",
                            })}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 shrink-0">
                      <div className="text-right">
                        <span className="text-xs text-slate-500 block">Tổng thanh toán</span>
                        <span className="text-base font-bold text-blue-700">
                          {formatPrice(inv.total_amount, "VND", "rent")}
                        </span>
                      </div>

                      {inv.status !== "paid" && (
                        <button
                          type="button"
                          onClick={() => handleSendReminder(inv.id)}
                          disabled={remindingId === inv.id}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition cursor-pointer disabled:opacity-50"
                        >
                          {remindingId === inv.id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Bell className="w-3.5 h-3.5" />
                          )}
                          Gửi nhắc nợ
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Col: Active Contracts & Tenants */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Users className="w-5 h-5 text-indigo-600" />
                Hợp đồng Thuê ({contracts.length})
              </h2>
            </div>

            {contracts.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                <p>Chưa có hợp đồng thuê nào đang kích hoạt.</p>
              </div>
            ) : (
              <div className="mt-4 space-y-3.5">
                {contracts.map((c) => (
                  <div
                    key={c.id}
                    className="p-3.5 rounded-xl border border-slate-200/90 bg-slate-50/50 hover:bg-white hover:border-blue-300 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-slate-900">
                        {c.tenant_name}
                      </span>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                        {c.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      SĐT: <span className="font-medium text-slate-700">{c.tenant_phone}</span>
                    </div>
                    <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs">
                      <span className="text-slate-600">Giá thuê:</span>
                      <span className="font-bold text-blue-700">
                        {formatPrice(c.rental_price, "VND", "rent")}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                      <span>Điện: {c.electricity_rate.toLocaleString("vi-VN")} đ/kWh</span>
                      <span>Nước: {c.water_rate.toLocaleString("vi-VN")} đ</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Meter Reading & Generate Invoice Modal */}
      {showInvoiceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" />
                Ghi Chỉ Số & Lập Hóa Đơn Tháng
              </h3>
              <button
                type="button"
                onClick={() => setShowInvoiceModal(false)}
                className="text-slate-400 hover:text-slate-600 rounded-lg p-1"
              >
                ✕
              </button>
            </div>

            {invoiceFormError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
                {invoiceFormError}
              </div>
            )}

            <form onSubmit={handleGenerateInvoice} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Chọn Hợp đồng Thuê / Khách thuê
                </label>
                <select
                  value={selectedContractId}
                  onChange={(e) => setSelectedContractId(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {contracts.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.tenant_name} ({c.tenant_phone}) - Giá phòng: {formatPrice(c.rental_price, "VND", "rent")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kỳ thanh toán (Tháng/Năm)
                </label>
                <input
                  type="month"
                  value={billingMonth}
                  onChange={(e) => setBillingMonth(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Electricity Readings */}
              <div className="p-3.5 bg-amber-50/50 rounded-xl border border-amber-200/70 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-amber-900">
                  <span className="flex items-center gap-1.5">
                    <Zap className="w-4 h-4 text-amber-600" /> Chỉ số Điện (kWh)
                  </span>
                  <span className="text-[11px] font-medium text-amber-700">
                    Đơn giá: {elecRate.toLocaleString("vi-VN")} đ/kWh
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-0.5">Chỉ số cũ</label>
                    <input
                      type="number"
                      min={0}
                      value={elecPrev}
                      onChange={(e) => setElecPrev(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-0.5">Chỉ số mới</label>
                    <input
                      type="number"
                      min={elecPrev}
                      value={elecCurr}
                      onChange={(e) => setElecCurr(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                      required
                    />
                  </div>
                </div>
                <div className="text-[11px] text-amber-800 font-medium pt-1 flex justify-between">
                  <span>Tiêu thụ: {elecUnits} kWh</span>
                  <span>Thành tiền: {elecCost.toLocaleString("vi-VN")} đ</span>
                </div>
              </div>

              {/* Water Readings */}
              <div className="p-3.5 bg-blue-50/50 rounded-xl border border-blue-200/70 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-blue-900">
                  <span className="flex items-center gap-1.5">
                    <Droplet className="w-4 h-4 text-blue-600" /> Chỉ số Nước (m³)
                  </span>
                  <span className="text-[11px] font-medium text-blue-700">
                    Đơn giá: {waterRate.toLocaleString("vi-VN")} đ
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-0.5">Chỉ số cũ</label>
                    <input
                      type="number"
                      min={0}
                      value={waterPrev}
                      onChange={(e) => setWaterPrev(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-0.5">Chỉ số mới</label>
                    <input
                      type="number"
                      min={waterPrev}
                      value={waterCurr}
                      onChange={(e) => setWaterCurr(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs"
                    />
                  </div>
                </div>
                <div className="text-[11px] text-blue-800 font-medium pt-1 flex justify-between">
                  <span>Tiêu thụ: {waterUnits} m³</span>
                  <span>Thành tiền: {waterCost.toLocaleString("vi-VN")} đ</span>
                </div>
              </div>

              {/* Estimated Total Bar */}
              <div className="bg-slate-100 rounded-xl p-3 flex items-center justify-between text-sm">
                <span className="font-semibold text-slate-700">Tổng cộng hóa đơn:</span>
                <span className="font-bold text-base text-blue-700">
                  {estimatedTotal.toLocaleString("vi-VN")} đ
                </span>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInvoiceModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={generatingInvoices}
                  className="px-5 py-2 rounded-xl text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 transition flex items-center gap-2 disabled:opacity-50"
                >
                  {generatingInvoices && <RefreshCw className="w-4 h-4 animate-spin" />}
                  Xuất Hóa Đơn & Gửi Khách
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
