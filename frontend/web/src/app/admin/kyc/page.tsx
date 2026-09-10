"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Clock3, Loader2, ShieldCheck, XCircle } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { apiClient } from "@/lib/api";
import type { PendingKycUser } from "@shared/types";

export default function AdminKycPage() {
  const router = useRouter();
  const { user, token, isLoading } = useAuth();
  const [items, setItems] = useState<PendingKycUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      setItems(await apiClient.getPendingKYCList());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tải hồ sơ KYC.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!isLoading && (!user || user.role !== "superadmin")) router.replace("/profile");
  }, [isLoading, router, user]);

  const review = async (item: PendingKycUser, action: "approve" | "reject") => {
    const reason = action === "reject" ? window.prompt("Lý do từ chối hồ sơ:")?.trim() : undefined;
    if (action === "reject" && !reason) return;
    setReviewing(item.user_id);
    try {
      await apiClient.reviewKYC(item.user_id, { action, reason });
      setItems((current) => current.filter((candidate) => candidate.user_id !== item.user_id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể cập nhật hồ sơ KYC.");
    } finally {
      setReviewing(null);
    }
  };

  if (isLoading || !user || user.role !== "superadmin") return <div className="min-h-[55vh]" />;

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-purple-700"><ShieldCheck className="h-4 w-4" /> Quản trị hệ thống</p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Duyệt hồ sơ KYC</h1>
          <p className="mt-2 text-sm text-slate-600">Kiểm tra hồ sơ CCCD đang chờ xác thực và gửi kết quả trực tiếp tới người dùng.</p>
        </div>
        <span className="rounded-full bg-amber-100 px-4 py-2 text-sm font-bold text-amber-800">{items.length} hồ sơ chờ duyệt</span>
      </div>
      {error && <p className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {loading ? <div className="flex min-h-64 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-purple-600" /></div> : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center"><CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" /><h2 className="mt-4 text-lg font-bold text-slate-800">Không còn hồ sơ chờ duyệt</h2></div>
      ) : <div className="grid gap-5 md:grid-cols-2">
        {items.map((item) => <article key={item.user_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3"><div><h2 className="font-bold text-slate-900">{item.full_name}</h2><p className="mt-1 text-sm text-slate-500">{item.email} · {item.phone || "Chưa có số điện thoại"}</p></div><Clock3 className="h-5 w-5 text-amber-500" /></div>
          <div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-xl bg-slate-100 p-4 text-center text-xs font-semibold text-slate-500">Mặt trước CCCD<br /><span className="mt-1 block text-slate-800">Tài liệu riêng tư</span></div><div className="rounded-xl bg-slate-100 p-4 text-center text-xs font-semibold text-slate-500">Mặt sau CCCD<br /><span className="mt-1 block text-slate-800">Tài liệu riêng tư</span></div></div>
          <p className="mt-4 text-sm text-slate-600">CCCD: <strong>{item.masked_citizen_id}</strong></p>
          <div className="mt-5 flex gap-3"><button disabled={reviewing === item.user_id} onClick={() => review(item, "approve")} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-60"><CheckCircle2 className="h-4 w-4" />Duyệt hồ sơ</button><button disabled={reviewing === item.user_id} onClick={() => review(item, "reject")} className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-rose-200 px-4 py-2.5 text-sm font-bold text-rose-700 disabled:opacity-60"><XCircle className="h-4 w-4" />Từ chối</button></div>
        </article>)}
      </div>}
    </main>
  );
}
