"use client";

import { useState } from "react";
import { Share2, Check } from "lucide-react";

interface PropertyShareButtonProps {
  title: string;
  className?: string;
}

export default function PropertyShareButton({
  title,
  className = "",
}: PropertyShareButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const url = typeof window !== "undefined" ? window.location.href : "";

    if (navigator.share) {
      try {
        await navigator.share({
          title,
          text: `Xem bất động sản: ${title}`,
          url,
        });
        return;
      } catch (err: any) {
        // User cancelled or share aborted - ignore AbortError silently
        if (err?.name === "AbortError") {
          return;
        }
      }
    }

    // Fallback: Copy URL to clipboard
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Ignore if clipboard fails
    }
  };

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={handleShare}
        className={`inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 shadow-xs hover:bg-slate-50 transition cursor-pointer ${className}`}
      >
        {copied ? (
          <Check className="h-4 w-4 text-emerald-600" />
        ) : (
          <Share2 className="h-4 w-4 text-slate-500" />
        )}
        <span>{copied ? "Đã sao chép liên kết!" : "Chia sẻ"}</span>
      </button>

      {/* Floating Toast Notification */}
      {copied && (
        <div className="absolute right-0 top-full mt-1.5 z-50 whitespace-nowrap rounded-lg bg-slate-900 px-3 py-1.5 text-xs text-white shadow-lg">
          Đã sao chép liên kết vào bộ nhớ tạm
        </div>
      )}
    </div>
  );
}
