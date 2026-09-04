"use client";

import { useComparison } from "@/lib/comparison";
import { useState } from "react";
import ComparisonModal from "./ComparisonModal";

export default function StickyComparisonBar() {
  const { selectedProperties, clearComparison } = useComparison();
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (selectedProperties.length === 0) return null;

  return (
    <>
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgb(0,0,0,0.1)] p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-semibold text-slate-800">
              Đã chọn {selectedProperties.length}/3 bất động sản để so sánh
            </span>
            <button
              onClick={clearComparison}
              className="text-sm text-rose-500 hover:text-rose-600 font-medium"
            >
              Xóa tất cả
            </button>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            disabled={selectedProperties.length < 2}
            className={`px-6 py-2 rounded-lg font-semibold transition ${
              selectedProperties.length >= 2
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-slate-200 text-slate-400 cursor-not-allowed"
            }`}
          >
            So sánh ngay
          </button>
        </div>
      </div>
      
      {isModalOpen && (
        <ComparisonModal onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}
