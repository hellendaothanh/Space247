"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Clock,
  Calendar,
  Building2,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  User,
  Phone,
  MessageSquare,
} from "lucide-react";
import type { RentalInquiry } from "@shared/types";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function MyRentalInquiriesPage() {
  const { user, token, isLoading: authLoading } = useAuth();
  const [inquiries, setInquiries] = useState<RentalInquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchInquiries() {
      if (!user) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError("");
      try {
        const res = await apiClient.getMyRentalInquiries();
        setInquiries(res || []);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Không thể tải danh sách lịch hẹn");
      } finally {
        setLoading(false);
      }
    }

    if (!authLoading) {
      fetchInquiries();
    }
  }, [user, authLoading]);

  if (authLoading || loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 text-center text-slate-500">
        <Clock className="h-8 w-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm">Đang tải danh sách lịch hẹn xem phòng...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16 text-center space-y-4">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <User className="h-7 w-7" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Vui lòng đăng nhập</h1>
        <p className="text-sm text-slate-500">
          Bạn cần đăng nhập để xem danh sách lịch hẹn xem phòng và yêu cầu giữ chỗ đã gửi đến các chủ nhà.
        </p>
        <div className="pt-2">
          <Link
            href="/login?redirect=/rentals/my-inquiries"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-bold text-white shadow-xs hover:bg-blue-700 transition"
          >
            Đăng nhập ngay
          </Link>
        </div>
      </main>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-800">
            <CheckCircle2 className="h-3.5 w-3.5" /> Đã xác nhận
          </span>
        );
      case "rejected":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-800">
            <XCircle className="h-3.5 w-3.5" /> Đã từ chối
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-200 px-2.5 py-1 text-xs font-bold text-slate-700">
            <CheckCircle2 className="h-3.5 w-3.5" /> Đã hoàn tất
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-800">
            <AlertCircle className="h-3.5 w-3.5" /> Chờ chủ nhà duyệt
          </span>
        );
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Navigation Breadcrumb & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <nav className="flex items-center gap-2 text-xs text-slate-500 mb-2">
            <Link href="/rentals" className="hover:text-blue-600 transition flex items-center gap-1">
              <ArrowLeft className="h-3 w-3" /> Quay lại Cho thuê
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">Lịch hẹn của tôi</span>
          </nav>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Lịch Hẹn Xem Phòng & Giữ Chỗ
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Theo dõi trạng thái các yêu cầu xem phòng và giữ chỗ bạn đã gửi cho Chủ nhà
          </p>
        </div>

        <Link
          href="/rentals"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100 transition self-start sm:self-auto"
        >
          <span>Tìm thêm phòng khác</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700">
          {error}
        </div>
      )}

      {/* Inquiries List */}
      {inquiries.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center bg-slate-50/50 space-y-3">
          <Clock className="h-10 w-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">Chưa có lịch hẹn nào</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Khi bạn xem thông tin chi tiết phòng trọ, căn hộ và nhấn &quot;Đặt lịch xem phòng&quot;, thông tin yêu cầu sẽ xuất hiện ở đây.
          </p>
          <div className="pt-2">
            <Link
              href="/rentals"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition"
            >
              Khám phá phòng trọ ngay
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {inquiries.map((inq) => {
            const scheduledStr = inq.scheduled_time
              ? new Date(inq.scheduled_time).toLocaleString("vi-VN", {
                  weekday: "short",
                  day: "2-digit",
                  month: "2-digit",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "Thỏa thuận trực tiếp";

            return (
              <div
                key={inq.id}
                className="rounded-3xl border border-slate-200/80 bg-white p-5 sm:p-6 shadow-xs hover:shadow-md transition space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="rounded-full bg-blue-100 text-blue-800 px-3 py-1 text-xs font-bold">
                      {inq.inquiry_type === "booking_request" ? "Giữ chỗ / Đặt cọc" : "Hẹn xem phòng"}
                    </span>
                    <span className="text-xs text-slate-400">
                      Gửi ngày {new Date(inq.created_at).toLocaleDateString("vi-VN")}
                    </span>
                  </div>

                  <div>{getStatusBadge(inq.status)}</div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                      <Building2 className="h-4 w-4 text-blue-600 shrink-0" />
                      <span>{inq.unit ? `Phòng ${inq.unit.unit_number}` : "Phòng đang chọn"}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-600">
                      <Calendar className="h-4 w-4 text-amber-600 shrink-0" />
                      <span>Thời gian hẹn: <strong className="text-slate-900">{scheduledStr}</strong></span>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/80 p-3 rounded-2xl border border-slate-100">
                    <div className="flex items-center gap-1.5 font-medium text-slate-700">
                      <User className="h-3.5 w-3.5 text-slate-400" />
                      <span>Người đặt: {inq.tenant_name || user.full_name}</span>
                    </div>
                    {inq.tenant_phone && (
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Phone className="h-3.5 w-3.5 text-slate-400" />
                        <span>SĐT liên hệ: {inq.tenant_phone}</span>
                      </div>
                    )}
                    {inq.message && (
                      <div className="flex items-start gap-1.5 text-slate-500 pt-1 border-t border-slate-200/60 mt-1">
                        <MessageSquare className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span className="italic line-clamp-2">&quot;{inq.message}&quot;</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}
