"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  QrCode,
  Copy,
  Check,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import type { DepositTransaction } from "@shared/types";

interface DepositPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  transaction: DepositTransaction | null;
  onPaymentSuccess?: (tx: DepositTransaction) => void;
}

export default function DepositPaymentModal({
  isOpen,
  onClose,
  transaction,
  onPaymentSuccess,
}: DepositPaymentModalProps) {
  const [currentTx, setCurrentTx] = useState<DepositTransaction | null>(transaction);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(15 * 60); // in seconds
  const [isSuccess, setIsSuccess] = useState(false);
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    setCurrentTx(transaction);
    setIsSuccess(transaction?.status === "success");
    setIsExpired(transaction?.status === "expired");

    if (transaction?.expires_at) {
      const expiry = new Date(transaction.expires_at).getTime();
      const now = new Date().getTime();
      const diffSecs = Math.max(0, Math.floor((expiry - now) / 1000));
      setTimeLeft(diffSecs);
      if (diffSecs === 0 && transaction.status === "pending") {
        setIsExpired(true);
      }
    } else {
      setTimeLeft(15 * 60);
    }
  }, [transaction]);

  // 1-second interval countdown timer
  useEffect(() => {
    if (!isOpen || isSuccess || isExpired) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsExpired(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen, isSuccess, isExpired]);

  // 3-second real-time status polling
  useEffect(() => {
    if (!isOpen || !currentTx || isSuccess || isExpired) return;

    const interval = setInterval(async () => {
      try {
        const latest = await apiClient.getDepositTransactionStatus(currentTx.reference_code);
        setCurrentTx(latest);

        if (latest.status === "success") {
          setIsSuccess(true);
          clearInterval(interval);
          if (onPaymentSuccess) {
            onPaymentSuccess(latest);
          }
        } else if (latest.status === "expired") {
          setIsExpired(true);
          clearInterval(interval);
        }
      } catch (err) {
        // Silently catch temporary network hiccups during polling
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isOpen, currentTx, isSuccess, isExpired, onPaymentSuccess]);

  if (!isOpen || !currentTx) return null;

  const formatCountdown = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const isUrgent = timeLeft < 180; // less than 3 mins

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative bg-white rounded-3xl max-w-md w-full overflow-hidden shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-white/10 rounded-xl">
              <QrCode className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <h3 className="font-bold text-base leading-snug">Đặt cọc giữ chỗ phòng</h3>
              <p className="text-xs text-blue-100">Quét mã VietQR Napas 247 tức thì</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Success State */}
          {isSuccess ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto animate-bounce">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <div>
                <h4 className="text-xl font-bold text-slate-900">Thanh toán thành công!</h4>
                <p className="text-sm text-slate-600 mt-1">
                  Số tiền <span className="font-semibold text-emerald-600">{formatPrice(currentTx.amount, "VND")}</span> đã được xác nhận.
                </p>
                <p className="text-xs text-slate-500 mt-2 bg-emerald-50 text-emerald-800 p-2.5 rounded-xl border border-emerald-200">
                  🎉 Phòng của bạn đã được chuyển sang trạng thái <strong>Đã giữ chỗ</strong>. Chủ nhà đã nhận được thông báo để bàn giao phòng.
                </p>
              </div>
              <button
                onClick={onClose}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition-colors shadow-sm"
              >
                Hoàn tất & Đóng
              </button>
            </div>
          ) : isExpired ? (
            /* Expired State */
            <div className="text-center py-6 space-y-4">
              <div className="w-16 h-16 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto">
                <AlertTriangle className="w-10 h-10" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-slate-900">Mã thanh toán đã hết hạn</h4>
                <p className="text-xs text-slate-500 mt-1.5">
                  Thời hạn 15 phút đặt cọc giữ chỗ đã kết thúc. Vui lòng liên hệ lại chủ nhà hoặc tạo yêu cầu mới.
                </p>
              </div>
              <button
                onClick={onClose}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-xl transition-colors"
              >
                Đóng
              </button>
            </div>
          ) : (
            /* Pending Payment State */
            <>
              {/* Countdown Banner */}
              <div
                className={`flex items-center justify-between p-3 rounded-xl border text-xs font-semibold ${
                  isUrgent
                    ? "bg-rose-50 text-rose-700 border-rose-200 animate-pulse"
                    : "bg-blue-50 text-blue-800 border-blue-200"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
                  <span>Thời gian giữ phòng còn lại:</span>
                </div>
                <span className="text-sm font-bold font-mono tracking-wider">
                  {formatCountdown(timeLeft)}
                </span>
              </div>

              {/* VietQR Image Card */}
              <div className="flex flex-col items-center justify-center p-3 bg-slate-50 rounded-2xl border border-slate-200">
                <div className="bg-white p-2.5 rounded-xl shadow-xs border border-slate-200/80">
                  <img
                    src={currentTx.vietqr_url}
                    alt="VietQR Deposit Code"
                    className="w-56 h-auto object-contain rounded-lg"
                    loading="eager"
                  />
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Chuyển khoản liên ngân hàng 24/7 Napas</span>
                </div>
              </div>

              {/* Transfer Details Breakdown */}
              <div className="space-y-2 text-xs">
                {/* Amount */}
                <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-500">Số tiền đặt cọc:</span>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm text-blue-700">
                      {formatPrice(currentTx.amount, "VND")}
                    </span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(currentTx.amount.toString(), "amount")}
                      className="p-1 hover:bg-slate-200 rounded text-slate-500 transition-colors"
                      title="Sao chép số tiền"
                    >
                      {copiedField === "amount" ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Reference Code */}
                <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                  <div>
                    <span className="text-slate-500 block">Nội dung chuyển khoản (bắt buộc):</span>
                    <span className="font-mono font-bold text-slate-900">{currentTx.reference_code}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(currentTx.reference_code, "ref")}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg transition-colors"
                  >
                    {copiedField === "ref" ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Đã chép</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Sao chép</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Polling Indicator */}
              <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400 py-1">
                <RefreshCw className="w-3 h-3 animate-spin text-blue-600" />
                <span>Hệ thống đang tự động kiểm tra giao dịch...</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
