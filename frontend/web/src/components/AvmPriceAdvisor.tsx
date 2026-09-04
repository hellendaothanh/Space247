"use client";

import { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Scale,
  Compass,
  Building,
  Sparkles,
  Info,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { ValuationResponse, ComparableProperty } from "@shared/types";
import { formatPrice } from "@/lib/utils";

interface AvmPriceAdvisorProps {
  propertyType: string;
  areaSqm: number;
  numBedrooms?: number | null;
  numBathrooms?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  proposedPrice?: number | null;
  onApplyPrice?: (price: number) => void;
}

export default function AvmPriceAdvisor({
  propertyType,
  areaSqm,
  numBedrooms,
  numBathrooms,
  latitude,
  longitude,
  proposedPrice,
  onApplyPrice,
}: AvmPriceAdvisorProps) {
  const [data, setData] = useState<ValuationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showComps, setShowComps] = useState(false);

  const fetchValuation = useCallback(async () => {
    if (!areaSqm || areaSqm <= 0) {
      setError("Vui lòng nhập diện tích hợp lệ để định giá AVM.");
      return;
    }
    if (!latitude || !longitude) {
      setError("Vui lòng nhập tọa độ vị trí (vĩ độ, kinh độ) để tìm kiếm các BĐS tương đồng xung quanh.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const res = await apiClient.estimatePropertyValuation({
        property_type: propertyType,
        area_sqm: areaSqm,
        num_bedrooms: numBedrooms ?? undefined,
        num_bathrooms: numBathrooms ?? undefined,
        latitude: latitude,
        longitude: longitude,
        radius_km: 2.5,
        user_proposed_price: proposedPrice && proposedPrice > 0 ? proposedPrice : undefined,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || "Không thể tính toán định giá AVM.");
    } finally {
      setIsLoading(false);
    }
  }, [propertyType, areaSqm, numBedrooms, numBathrooms, latitude, longitude, proposedPrice]);

  const getGaugePosition = () => {
    if (!data || !proposedPrice || proposedPrice <= 0) return 50; // Default centered
    const dev = data.deviation_percentage ?? 0;
    // Map deviation: -25% -> 10%, 0% -> 50%, +25% -> 90%
    const pos = 50 + dev * 1.6;
    return Math.max(5, Math.min(95, pos));
  };

  const getConfidenceBadge = (score: number) => {
    if (score >= 0.8) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" /> Độ tin cậy cao ({Math.round(score * 100)}%)
        </span>
      );
    }
    if (score >= 0.6) {
      return (
        <span className="px-2 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800 rounded-full flex items-center gap-1">
          <Info className="w-3 h-3" /> Độ tin cậy khá ({Math.round(score * 100)}%)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-semibold bg-orange-100 text-orange-800 rounded-full flex items-center gap-1">
        <AlertTriangle className="w-3 h-3" /> Tham khảo ({Math.round(score * 100)}%)
      </span>
    );
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 rounded-2xl border border-blue-100/80 p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-600 text-white rounded-lg shadow-sm">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              Smart AVM Pricing Advisor
              <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                AI Agent
              </span>
            </h3>
            <p className="text-xs text-slate-500">
              Định giá tự động dựa trên giao dịch thực tế & thuật toán Weighted KNN lân cận
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchValuation}
          disabled={isLoading}
          className="px-3 py-1.5 bg-white hover:bg-blue-50 text-blue-600 border border-blue-200 text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5 disabled:opacity-50"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>{isLoading ? "Đang định giá..." : data ? "Cập nhật định giá" : "Định giá AVM"}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-center gap-2">
          <Info className="w-4 h-4 shrink-0 text-amber-600" />
          <span>{error}</span>
        </div>
      )}

      {data && (
        <div className="space-y-4 pt-1 animate-fade-in">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-0.5">
                Đơn giá đề xuất
              </span>
              <span className="text-base font-bold text-slate-900">
                {(data.estimated_price_per_sqm / 1_000_000).toFixed(1)} tr/m²
              </span>
              <span className="text-[11px] text-slate-400 block">
                {data.estimated_price_per_sqm.toLocaleString("vi-VN")} đ/m²
              </span>
            </div>

            <div className="p-3 bg-white rounded-xl border border-blue-200 bg-blue-50/20 shadow-xs">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[11px] font-semibold text-blue-700 uppercase">
                  Tổng giá thị trường
                </span>
                {getConfidenceBadge(data.confidence_score)}
              </div>
              <span className="text-lg font-extrabold text-blue-600">
                {formatPrice(data.estimated_total_price)}
              </span>
              <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                <span>Khoảng giá: {formatPrice(data.price_range_low)} – {formatPrice(data.price_range_high)}</span>
              </div>
            </div>

            <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-0.5">
                  Bán kính tham chiếu
                </span>
                <span className="text-sm font-bold text-slate-800">
                  {data.radius_used_km} km
                </span>
                <span className="text-[11px] text-slate-400 block">
                  Tìm thấy {data.comparable_properties.length} căn tương đồng
                </span>
              </div>
              {onApplyPrice && (
                <button
                  type="button"
                  onClick={() => onApplyPrice(data.estimated_total_price)}
                  className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 hover:underline"
                >
                  <span>Áp dụng giá này</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Pricing Gauge Bar (Rẻ - Hợp lý - Đắt) */}
          <div className="p-3 bg-white rounded-xl border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-slate-600">
              <span className="text-emerald-700 font-semibold">Thấp hơn thị trường</span>
              <span className="text-blue-700 font-semibold">Định giá hợp lý</span>
              <span className="text-rose-700 font-semibold">Cao hơn thị trường</span>
            </div>

            {/* Gauge Track */}
            <div className="relative h-2.5 rounded-full bg-gradient-to-r from-emerald-400 via-blue-400 to-rose-400 overflow-visible">
              <div
                className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-slate-900 rounded-full shadow-md transition-all duration-300 -ml-2"
                style={{ left: `${getGaugePosition()}%` }}
                title={`Vị trí giá hiện tại: ${data.deviation_percentage ? `${data.deviation_percentage}%` : "Mặt bằng chuẩn"}`}
              />
            </div>

            {/* Pricing Advice Banner */}
            {data.pricing_advice && (
              <p className="text-xs text-slate-700 pt-1 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                {data.pricing_advice}
              </p>
            )}
          </div>

          {/* Comparable Properties Accordion */}
          {data.comparable_properties.length > 0 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              <button
                type="button"
                onClick={() => setShowComps(!showComps)}
                className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                <span>
                  Danh sách BĐS tham chiếu lân cận ({data.comparable_properties.length} căn)
                </span>
                {showComps ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </button>

              {showComps && (
                <div className="p-3 border-t border-slate-100 space-y-2 max-h-60 overflow-y-auto">
                  {data.comparable_properties.map((comp) => (
                    <div
                      key={comp.id}
                      className="p-2.5 bg-slate-50 hover:bg-blue-50/40 rounded-lg border border-slate-100 flex items-center justify-between text-xs transition"
                    >
                      <div className="space-y-0.5">
                        <p className="font-semibold text-slate-800 line-clamp-1">
                          {comp.title}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {comp.address} • Cách {comp.distance_km} km
                        </p>
                      </div>
                      <div className="text-right shrink-0 ml-3">
                        <span className="font-bold text-slate-900 block">
                          {formatPrice(comp.price)}
                        </span>
                        <span className="text-[11px] text-slate-500 block">
                          {(comp.price_per_sqm / 1_000_000).toFixed(1)} tr/m² ({comp.area_sqm} m²)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
