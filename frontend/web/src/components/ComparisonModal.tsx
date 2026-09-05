"use client";

import { useEffect, useRef, useState } from "react";
import { useComparison } from "@/lib/comparison";
import { apiClient } from "@/lib/api";
import { ComparePropertiesResponse } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import { X, Scale, MapPin, Bed, Bath, Maximize2, LineChart, Printer, Share2, Check, ArrowUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ComparisonModal({ onClose }: { onClose: () => void }) {
  const { selectedProperties } = useComparison();
  const [data, setData] = useState<ComparePropertiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const contentRef = useRef<HTMLDivElement | null>(null);

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

  const handlePrint = () => {
    window.print();
  };

  const handleScroll = () => {
    if (contentRef.current) {
      setShowScrollTop(contentRef.current.scrollTop > 240);
    }
  };

  const scrollToTop = () => {
    if (contentRef.current) {
      contentRef.current.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  };

  const handleShare = async () => {
    const shareUrl = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Báo cáo So sánh Bất động sản Space247",
          text: `Báo cáo so sánh đối chiếu ${selectedProperties.length} bất động sản trên Space247`,
          url: shareUrl,
        });
        return;
      } catch {
        // Fallback to clipboard if share was cancelled or failed
      }
    }
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in">
      <div
        id="comparison-printable-area"
        className="relative w-full max-w-5xl max-h-[92vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200"
      >
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
          <div className="flex items-center gap-2 no-print">
            <button
              onClick={handlePrint}
              disabled={loading || !data}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg shadow-2xs transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              title="In hoặc Lưu thành file PDF"
            >
              <Printer className="w-4 h-4 text-slate-600" />
              <span className="hidden sm:inline">In / Xuất PDF</span>
            </button>

            <button
              onClick={handleShare}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg shadow-2xs transition cursor-pointer"
              title="Chia sẻ hoặc Sao chép liên kết"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-600" />
                  <span className="text-emerald-700">Đã chép link!</span>
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4 text-blue-600" />
                  <span className="hidden sm:inline">Chia sẻ</span>
                </>
              )}
            </button>

            <div className="h-5 w-px bg-slate-200 mx-1" />

            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-200/60 rounded-full text-slate-400 hover:text-slate-600 transition cursor-pointer"
              title="Đóng cửa sổ"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div
          ref={contentRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6 scroll-smooth relative"
        >
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
              <div className="text-slate-800 text-sm leading-relaxed space-y-3">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-lg font-extrabold text-slate-900 border-b border-slate-200 pb-2 mt-4 mb-3 tracking-tight">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-base font-bold text-slate-900 mt-5 mb-2 flex items-center gap-2">
                        <span className="w-1.5 h-4 bg-blue-600 rounded-full inline-block" />
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-sm font-bold text-slate-900 mt-4 mb-2 uppercase tracking-wider text-blue-900">
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-sm font-semibold text-slate-900 mt-3 mb-1.5">
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className="text-slate-700 leading-relaxed mb-2.5">{children}</p>
                    ),
                    ul: ({ children }) => (
                      <ul className="space-y-1.5 my-2.5 list-none pl-1">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="space-y-1.5 my-2.5 list-decimal pl-5 text-slate-700">{children}</ol>
                    ),
                    li: ({ children }) => (
                      <li className="flex items-start gap-2 text-slate-700">
                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 shrink-0" />
                        <span className="flex-1">{children}</span>
                      </li>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-slate-900">{children}</strong>
                    ),
                    table: ({ children }) => (
                      <div className="my-4 overflow-x-auto rounded-xl border border-slate-200 shadow-xs bg-white">
                        <table className="w-full text-left text-xs border-collapse min-w-[500px]">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-slate-100/90 text-slate-900 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                        {children}
                      </thead>
                    ),
                    tbody: ({ children }) => (
                      <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>
                    ),
                    tr: ({ children }) => (
                      <tr className="hover:bg-blue-50/40 transition-colors">{children}</tr>
                    ),
                    th: ({ children }) => (
                      <th className="py-3 px-4 font-semibold text-slate-900 border-r border-slate-200/60 last:border-r-0">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="py-2.5 px-4 text-slate-700 border-r border-slate-100 last:border-r-0 align-top">
                        {children}
                      </td>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-500 bg-blue-50/50 pl-4 py-2 my-3 rounded-r-lg text-slate-700 italic">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {data.analysis_markdown}
                </ReactMarkdown>
              </div>
            ) : null}
          </div>
        </div>

        {/* Up To Top Floating Button */}
        {showScrollTop && (
          <button
            onClick={scrollToTop}
            className="no-print absolute bottom-6 right-6 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer flex items-center justify-center group focus:outline-hidden focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 z-20 animate-fade-in"
            title="Cuộn lên đầu trang"
            aria-label="Cuộn lên đầu trang"
          >
            <ArrowUp className="w-5 h-5 transition-transform duration-200 group-hover:-translate-y-0.5" />
          </button>
        )}
      </div>
    </div>
  );
}
