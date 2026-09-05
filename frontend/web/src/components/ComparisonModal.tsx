"use client";

import { useEffect, useState } from "react";
import { useComparison } from "@/lib/comparison";
import { apiClient } from "@/lib/api";
import { ComparePropertiesResponse } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import { X, Scale, MapPin, Bed, Bath, Maximize2, LineChart } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ComparisonModal({ onClose }: { onClose: () => void }) {
  const { selectedProperties } = useComparison();
  const [data, setData] = useState<ComparePropertiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        setLoading(true);
        setError("");
        const res = await apiClient.compareProperties({
          property_ids: selectedProperties.map((p) => p.id),
        });
        setData(res);
      } catch (err: any) {
        setError(err.message || "Có lỗi xảy ra khi so sánh bất động sản.");
      } finally {
        setLoading(false);
      }
    };
    if (selectedProperties.length >= 2) {
      fetchComparison();
    }
  }, [selectedProperties]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-5xl max-h-[92vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 sm:p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-xl">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                So sánh Bất động sản trực tiếp
              </h2>
              <p className="text-xs text-slate-500">
                Đối chiếu thông số kỹ thuật và báo cáo phân tích đối soát từ hệ thống Space247
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200/60 rounded-full text-slate-400 hover:text-slate-600 transition cursor-pointer"
            title="Đóng cửa sổ"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
          {error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
              <p className="font-semibold">Không thể tải phân tích so sánh:</p>
              <p className="mt-1">{error}</p>
            </div>
          ) : null}

          {/* Side-by-side Technical Comparison Table */}
          <div className="rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px] text-sm text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="p-4 font-semibold text-slate-700 w-1/4">Tiêu chí</th>
                    {selectedProperties.map((p, idx) => (
                      <th key={p.id} className="p-4 font-semibold text-slate-900 w-1/4 align-top">
                        <div className="space-y-2">
                          <img
                            src={getPlaceholderImage(p.property_type, idx)}
                            alt={p.title}
                            className="w-full h-24 object-cover rounded-lg"
                          />
                          <div className="line-clamp-2 font-bold text-slate-800" title={p.title}>
                            {p.title}
                          </div>
                          <span className="inline-block text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-200/80 text-slate-700">
                            {formatPropertyType(p.property_type)}
                          </span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="p-4 font-medium text-slate-600 bg-slate-50/50">Giá tổng</td>
                    {selectedProperties.map((p) => (
                      <td key={p.id} className="p-4 font-bold text-base text-blue-700">
                        {formatPrice(p.price, p.currency, p.listing_type)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-4 font-medium text-slate-600 bg-slate-50/50">Diện tích</td>
                    {selectedProperties.map((p) => (
                      <td key={p.id} className="p-4 text-slate-800">
                        <span className="font-semibold">{p.area_sqm}</span> m²
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-4 font-medium text-slate-600 bg-slate-50/50">Đơn giá / m²</td>
                    {selectedProperties.map((p) => {
                      const calculatedPricePerSqm =
                        p.area_sqm > 0 ? Math.round(p.price / p.area_sqm) : 0;
                      return (
                        <td key={p.id} className="p-4 font-semibold text-emerald-600">
                          {formatPrice(calculatedPricePerSqm, p.currency)}/m²
                        </td>
                      );
                    })}
                  </tr>
                  <tr>
                    <td className="p-4 font-medium text-slate-600 bg-slate-50/50">Địa chỉ / Vị trí</td>
                    {selectedProperties.map((p) => (
                      <td key={p.id} className="p-4 text-slate-600 text-xs leading-relaxed">
                        <div className="flex items-start gap-1">
                          <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400 mt-0.5" />
                          <span>
                            {[p.address, p.ward, p.district, p.city].filter(Boolean).join(", ")}
                          </span>
                        </div>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-4 font-medium text-slate-600 bg-slate-50/50">Phòng ngủ & WC</td>
                    {selectedProperties.map((p) => (
                      <td key={p.id} className="p-4 text-slate-700 text-xs">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1 font-medium">
                            <Bed className="w-3.5 h-3.5 text-slate-400" />
                            {p.num_bedrooms ?? "--"} PN
                          </span>
                          <span className="flex items-center gap-1 font-medium">
                            <Bath className="w-3.5 h-3.5 text-slate-400" />
                            {p.num_bathrooms ?? "--"} WC
                          </span>
                        </div>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Analysis Section */}
          <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50/70 via-white to-blue-50/30 p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2.5 text-slate-900 font-bold text-base">
              <div className="p-1.5 bg-blue-100 text-blue-700 rounded-lg">
                <LineChart className="w-4 h-4" />
              </div>
              <h3>Phân tích Chuyên sâu & Khuyến nghị từ AI</h3>
            </div>

            {loading ? (
              <div className="space-y-4 animate-pulse py-4">
                <div className="flex items-center gap-3 text-slate-600 text-sm">
                  <div className="w-4 h-4 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
                  <span>Gemini AI đang tổng hợp dữ liệu và phân tích theo 4 tiêu chí cốt lõi...</span>
                </div>
                <div className="h-4 bg-indigo-200/50 rounded w-3/4" />
                <div className="h-4 bg-indigo-100 rounded w-full" />
                <div className="h-4 bg-indigo-100 rounded w-5/6" />
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="h-20 bg-indigo-50/80 rounded-xl border border-indigo-100" />
                  <div className="h-20 bg-indigo-50/80 rounded-xl border border-indigo-100" />
                </div>
              </div>
            ) : data ? (
              <div className="prose prose-slate max-w-none text-slate-700 text-sm leading-relaxed prose-headings:text-slate-900 prose-headings:font-bold prose-h3:text-base prose-h4:text-sm prose-table:border prose-table:border-slate-200 prose-th:bg-slate-100 prose-th:p-2 prose-td:p-2">
                <ReactMarkdown>{data.analysis_markdown}</ReactMarkdown>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
