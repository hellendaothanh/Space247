"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Calculator,
  Landmark,
  Percent,
  Calendar,
  DollarSign,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  PiggyBank,
  CheckCircle2,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import type { MortgageCalcResponse, AmortizationScheduleItem } from "@shared/types";

interface MortgageCalculatorProps {
  propertyPrice: number;
  propertyTitle?: string;
  currency?: string;
}

export default function MortgageCalculator({
  propertyPrice,
  propertyTitle,
  currency = "VND",
}: MortgageCalculatorProps) {
  const [price, setPrice] = useState<number>(propertyPrice || 3_000_000_000);
  const [downPaymentPercent, setDownPaymentPercent] = useState<number>(30);
  const [loanTermYears, setLoanTermYears] = useState<number>(20);
  const [preferentialRate, setPreferentialRate] = useState<number>(7.5);
  const [preferentialMonths, setPreferentialMonths] = useState<number>(12);
  const [postPreferentialRate, setPostPreferentialRate] = useState<number>(10.5);
  const [calculationMethod, setCalculationMethod] = useState<"declining_balance" | "fixed_payment">("declining_balance");

  const [loading, setLoading] = useState<boolean>(false);
  const [calcResult, setCalcResult] = useState<MortgageCalcResponse | null>(null);
  const [showSchedule, setShowSchedule] = useState<boolean>(false);
  const [schedulePage, setSchedulePage] = useState<number>(1);
  const pageSize = 12;

  // Sync prop changes
  useEffect(() => {
    if (propertyPrice && propertyPrice > 0) {
      setPrice(propertyPrice);
    }
  }, [propertyPrice]);

  // Recalculate whenever inputs change
  useEffect(() => {
    let isCancelled = false;
    async function doCalculate() {
      setLoading(true);
      try {
        const res = await apiClient.calculateMortgage({
          property_price: price,
          down_payment_percent: downPaymentPercent,
          loan_term_years: loanTermYears,
          annual_interest_rate: preferentialRate,
          preferential_period_months: preferentialMonths,
          post_preferential_rate: postPreferentialRate,
          calculation_method: calculationMethod,
        });
        if (!isCancelled) {
          setCalcResult(res);
        }
      } catch (err) {
        console.error("Mortgage calculation failed:", err);
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    const timer = setTimeout(() => {
      doCalculate();
    }, 150);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [
    price,
    downPaymentPercent,
    loanTermYears,
    preferentialRate,
    preferentialMonths,
    postPreferentialRate,
    calculationMethod,
  ]);

  const downPaymentAmount = useMemo(() => {
    return Math.round((price * downPaymentPercent) / 100);
  }, [price, downPaymentPercent]);

  const loanAmount = useMemo(() => {
    return Math.max(0, price - downPaymentAmount);
  }, [price, downPaymentAmount]);

  const displayedSchedule = useMemo(() => {
    if (!calcResult || !calcResult.schedule) return [];
    return calcResult.schedule.slice(0, schedulePage * pageSize);
  }, [calcResult, schedulePage]);

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-xs">
            <Calculator className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900">Bảng tính vay mua nhà</h3>
            <p className="text-xs text-slate-500">
              Dự toán chi phí gốc & lãi vay ngân hàng theo dư nợ giảm dần hoặc niên kim
            </p>
          </div>
        </div>

        {/* Calculation Method Toggle */}
        <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setCalculationMethod("declining_balance")}
            className={`rounded-lg px-3 py-1.5 transition ${
              calculationMethod === "declining_balance"
                ? "bg-white text-blue-600 shadow-xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Dư nợ giảm dần
          </button>
          <button
            type="button"
            onClick={() => setCalculationMethod("fixed_payment")}
            className={`rounded-lg px-3 py-1.5 transition ${
              calculationMethod === "fixed_payment"
                ? "bg-white text-blue-600 shadow-xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Trả đều (Niên kim)
          </button>
        </div>
      </div>

      {/* Grid: Inputs on Left, Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Form Inputs (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Property Price */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
              <label htmlFor="propPrice">Giá trị bất động sản</label>
              <span className="text-blue-600 font-bold text-sm">
                {formatPrice(price, currency, "sale")}
              </span>
            </div>
            <input
              id="propPrice"
              type="number"
              min={100_000_000}
              step={50_000_000}
              value={price}
              onChange={(e) => setPrice(Math.max(0, Number(e.target.value)))}
              className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-900 focus:border-blue-500 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          {/* Down Payment % Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
              <label htmlFor="downPaymentRange">
                Vốn tự có (Trả trước): <span className="text-blue-600 font-bold">{downPaymentPercent}%</span>
              </label>
              <span className="text-slate-900 font-bold">
                {formatPrice(downPaymentAmount, currency, "sale")}
              </span>
            </div>
            <input
              id="downPaymentRange"
              type="range"
              min={0}
              max={90}
              step={5}
              value={downPaymentPercent}
              onChange={(e) => setDownPaymentPercent(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>0% (Vay 100%)</span>
              <span>30%</span>
              <span>50%</span>
              <span>70%</span>
              <span>90%</span>
            </div>
          </div>

          {/* Loan Term (Years) Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
              <label htmlFor="loanTermRange">
                Thời hạn vay: <span className="text-blue-600 font-bold">{loanTermYears} năm</span> ({loanTermYears * 12} tháng)
              </label>
              <span className="text-slate-500 text-xs font-medium">Tối đa 35 năm</span>
            </div>
            <input
              id="loanTermRange"
              type="range"
              min={1}
              max={35}
              step={1}
              value={loanTermYears}
              onChange={(e) => setLoanTermYears(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>5 năm</span>
              <span>10 năm</span>
              <span>20 năm</span>
              <span>25 năm</span>
              <span>35 năm</span>
            </div>
          </div>

          {/* Interest Rates & Preferential Period */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Lãi suất ưu đãi (%/năm)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step={0.1}
                  min={0}
                  max={30}
                  value={preferentialRate}
                  onChange={(e) => setPreferentialRate(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-200 pl-3 pr-7 py-2 text-xs font-medium text-slate-900 focus:border-blue-500 focus:outline-hidden"
                />
                <span className="absolute right-2.5 top-2 text-xs text-slate-400">%</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Kỳ ưu đãi (Tháng)
              </label>
              <select
                value={preferentialMonths}
                onChange={(e) => setPreferentialMonths(Number(e.target.value))}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-900 bg-white focus:border-blue-500 focus:outline-hidden"
              >
                <option value={0}>Không ưu đãi</option>
                <option value={6}>6 tháng</option>
                <option value={12}>12 tháng (1 năm)</option>
                <option value={18}>18 tháng</option>
                <option value={24}>24 tháng (2 năm)</option>
                <option value={36}>36 tháng (3 năm)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Lãi suất sau ưu đãi (%)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step={0.1}
                  min={0}
                  max={30}
                  value={postPreferentialRate}
                  onChange={(e) => setPostPreferentialRate(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-200 pl-3 pr-7 py-2 text-xs font-medium text-slate-900 focus:border-blue-500 focus:outline-hidden"
                />
                <span className="absolute right-2.5 top-2 text-xs text-slate-400">%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Summary Cards (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-2xl bg-linear-to-br from-slate-900 to-blue-950 p-6 text-white shadow-lg space-y-6">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/20 px-3 py-1 text-[11px] font-semibold text-blue-300 border border-blue-400/30 mb-4">
              <Landmark className="h-3.5 w-3.5" />
              {calculationMethod === "declining_balance"
                ? "Dư nợ giảm dần"
                : "Niên kim cố định"}
            </span>

            <p className="text-xs font-medium text-slate-300">Số tiền trả tháng đầu tiên</p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                {calcResult ? formatPrice(calcResult.monthly_payment_first_month, currency, "sale") : "--"}
              </span>
              <span className="text-xs text-slate-400">/ tháng</span>
            </div>

            {calculationMethod === "declining_balance" && calcResult && (
              <p className="text-[11px] text-blue-200/80 mt-1 flex items-center gap-1">
                <TrendingDown className="h-3.5 w-3.5 text-emerald-400" />
                Số tiền trả sẽ giảm dần xuống còn ~{formatPrice(calcResult.monthly_payment_min, currency, "sale")} vào tháng cuối.
              </p>
            )}
          </div>

          {/* Visual Distribution Bar */}
          {calcResult && (
            <div className="space-y-2">
              <div className="flex justify-between text-[11px] text-slate-300 font-medium">
                <span>Cơ cấu thanh toán toàn kỳ:</span>
                <span>{formatPrice(calcResult.total_payment, currency, "sale")}</span>
              </div>
              <div className="h-3 w-full rounded-full bg-slate-800 overflow-hidden flex">
                <div
                  style={{
                    width: `${(calcResult.loan_amount / calcResult.total_payment) * 100}%`,
                  }}
                  className="h-full bg-blue-500"
                  title="Gốc vay"
                />
                <div
                  style={{
                    width: `${(calcResult.total_interest / calcResult.total_payment) * 100}%`,
                  }}
                  className="h-full bg-amber-400"
                  title="Tổng lãi"
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-blue-500 inline-block" /> Gốc vay: {formatPrice(calcResult.loan_amount, currency, "sale")}
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-amber-400 inline-block" /> Lãi: {formatPrice(calcResult.total_interest, currency, "sale")}
                </span>
              </div>
            </div>
          )}

          {/* Breakdown Stats */}
          <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10 text-xs">
            <div>
              <p className="text-slate-400 text-[10px] uppercase font-semibold">Cần vay ngân hàng</p>
              <p className="font-bold text-white mt-0.5">
                {calcResult ? formatPrice(calcResult.loan_amount, currency, "sale") : "--"}
              </p>
            </div>
            <div>
              <p className="text-slate-400 text-[10px] uppercase font-semibold">Tổng tiền lãi cả kỳ</p>
              <p className="font-bold text-amber-300 mt-0.5">
                {calcResult ? formatPrice(calcResult.total_interest, currency, "sale") : "--"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Table Accordion */}
      {calcResult && calcResult.schedule && calcResult.schedule.length > 0 && (
        <div className="border-t border-slate-100 pt-6">
          <button
            type="button"
            onClick={() => setShowSchedule((prev) => !prev)}
            className="flex w-full items-center justify-between rounded-2xl bg-slate-50 hover:bg-slate-100/80 px-5 py-4 transition text-left cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <div>
                <span className="text-sm font-bold text-slate-800">
                  Xem chi tiết lịch trả nợ ({calcResult.loan_term_months} tháng)
                </span>
                <p className="text-xs text-slate-500">
                  Bảng chi tiết số tiền gốc, tiền lãi và dư nợ còn lại từng kỳ
                </p>
              </div>
            </div>
            {showSchedule ? (
              <ChevronUp className="h-5 w-5 text-slate-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-slate-400" />
            )}
          </button>

          {showSchedule && (
            <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50 text-slate-700 font-semibold">
                  <tr>
                    <th className="px-4 py-3 text-left">Kỳ (Tháng)</th>
                    <th className="px-4 py-3 text-right">Lãi suất (%/năm)</th>
                    <th className="px-4 py-3 text-right">Tiền gốc</th>
                    <th className="px-4 py-3 text-right">Tiền lãi</th>
                    <th className="px-4 py-3 text-right">Tổng phải trả</th>
                    <th className="px-4 py-3 text-right">Dư nợ còn lại</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white font-medium text-slate-600">
                  {displayedSchedule.map((row) => (
                    <tr key={row.month} className="hover:bg-blue-50/40 transition">
                      <td className="px-4 py-2.5 font-bold text-slate-900">Tháng {row.month}</td>
                      <td className="px-4 py-2.5 text-right font-medium text-blue-600">
                        {row.interest_rate}%
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {formatPrice(row.principal_payment, currency, "sale")}
                      </td>
                      <td className="px-4 py-2.5 text-right text-amber-600">
                        {formatPrice(row.interest_payment, currency, "sale")}
                      </td>
                      <td className="px-4 py-2.5 text-right font-bold text-slate-900">
                        {formatPrice(row.total_payment, currency, "sale")}
                      </td>
                      <td className="px-4 py-2.5 text-right font-semibold text-slate-500">
                        {formatPrice(row.remaining_balance, currency, "sale")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {displayedSchedule.length < calcResult.schedule.length && (
                <div className="p-4 bg-slate-50 text-center border-t border-slate-200">
                  <button
                    type="button"
                    onClick={() => setSchedulePage((prev) => prev + 2)}
                    className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-800 transition"
                  >
                    Xem thêm các tháng tiếp theo ({displayedSchedule.length} / {calcResult.schedule.length})
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
