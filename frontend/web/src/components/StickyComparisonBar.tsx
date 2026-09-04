"use client";

import { useComparison } from "@/lib/comparison";
import { useState } from "react";
import ComparisonModal from "./ComparisonModal";
import { getPlaceholderImage, formatPrice } from "@/lib/utils";
import { X, Sparkles } from "lucide-react";

export default function StickyComparisonBar() {
  const { selectedProperties, toggleComparison, clearComparison } = useComparison();
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (selectedProperties.length === 0) return null;

  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200 shadow-[0_-8px_20px_-4px_rgba(0,0,0,0.1)] py-3 px-4 transition-all">
        <div className="max-w-7xl mx-auto flex flex-wrap sm:flex-nowrap items-center justify-between gap-4">
          {/* Thumbnails & Status */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="hidden sm:block shrink-0">
              <span className="font-semibold text-slate-800 text-sm">
                So sánh ({selectedProperties.length}/3):
              </span>
            </div>

            {/* List of thumbnails */}
            <div className="flex items-center gap-2 overflow-x-auto py-1">
              {selectedProperties.map((p, idx) => (
                <div
                  key={p.id}
                  className="relative group flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl p-1.5 pr-2 shadow-xs shrink-0"
                >
                  <img
                    src={getPlaceholderImage(p.property_type, idx)}
                    alt={p.title}
                    className="w-10 h-10 object-cover rounded-lg shrink-0"
                  />
                  <div className="max-w-[120px] text-xs">
                    <p className="font-medium text-slate-800 truncate" title={p.title}>
                      {p.title}
                    </p>
                    <p className="text-blue-600 font-semibold">
                      {formatPrice(p.price, p.currency, p.listing_type)}
                    </p>
                  </div>
                  <button
                    onClick={() => toggleComparison(p)}
                    title="Xóa khỏi so sánh"
                    className="p-1 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-full transition cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={clearComparison}
              className="text-xs text-rose-500 hover:text-rose-600 font-medium shrink-0 ml-1 cursor-pointer"
            >
              Xóa tất cả
            </button>
          </div>

          {/* Action CTA */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setIsModalOpen(true)}
              disabled={selectedProperties.length < 2}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition shadow-sm ${
                selectedProperties.length >= 2
                  ? "bg-blue-600 text-white hover:bg-blue-700 cursor-pointer shadow-blue-500/20 hover:shadow-md"
                  : "bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>So sánh bằng AI {selectedProperties.length < 2 && "(chọn ít nhất 2 căn)"}</span>
            </button>
          </div>
        </div>
      </div>
      
      {isModalOpen && (
        <ComparisonModal onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
