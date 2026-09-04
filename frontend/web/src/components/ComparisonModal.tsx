"use client";

import { useEffect, useState } from "react";
import { useComparison } from "@/lib/comparison";
import { RealEstateApiClient } from "@shared/api-client";
import { ComparePropertiesResponse } from "@shared/types";
import { formatPrice } from "@/lib/utils";
import { X, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ComparisonModal({ onClose }: { onClose: () => void }) {
  const { selectedProperties } = useComparison();
  const [data, setData] = useState<ComparePropertiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const apiClient = new RealEstateApiClient({ baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" });
        const res = await apiClient.compareProperties({
          property_ids: selectedProperties.map(p => p.id)
        });
        setData(res);
      } catch (err: any) {
        setError(err.message || "Có lỗi xảy ra khi so sánh");
      } finally {
        setLoading(false);
      }
    };
    fetchComparison();
  }, [selectedProperties]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h2 className="text-2xl font-bold text-slate-800">So sánh Bất động sản bằng AI</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full transition">
            <X className="w-6 h-6 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
              <p className="text-slate-500 animate-pulse">AI đang phân tích các bất động sản...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 text-rose-600 rounded-xl">
              {error}
            </div>
          ) : data ? (
            <div className="space-y-8">
              {/* Matrix */}
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] border-collapse">
                  <thead>
                    <tr>
                      <th className="p-4 text-left border-b border-slate-200 bg-slate-50 w-1/4">Tiêu chí</th>
                      {data.properties.map((p, i) => (
                        <th key={p.property_id} className="p-4 text-left border-b border-slate-200 bg-slate-50 w-1/4">
                          <div className="font-semibold text-slate-800 line-clamp-2">{p.title}</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="p-4 border-b border-slate-100 font-medium text-slate-600">Giá tổng</td>
                      {data.properties.map((p) => (
                        <td key={p.property_id} className="p-4 border-b border-slate-100 font-bold text-blue-600">
                          {formatPrice(p.price)}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-4 border-b border-slate-100 font-medium text-slate-600">Diện tích</td>
                      {data.properties.map((p) => (
                        <td key={p.property_id} className="p-4 border-b border-slate-100">{p.area_sqm} m²</td>
                      ))}
                    </tr>
                    <tr>
                      <td className="p-4 border-b border-slate-100 font-medium text-slate-600">Đơn giá</td>
                      {data.properties.map((p) => (
                        <td key={p.property_id} className="p-4 border-b border-slate-100 font-medium text-emerald-600">
                          {formatPrice(p.price_per_sqm)}/m²
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* AI Markdown Analysis */}
              <div className="prose prose-slate max-w-none bg-blue-50/50 p-6 rounded-2xl border border-blue-100">
                <ReactMarkdown>{data.analysis_markdown}</ReactMarkdown>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
