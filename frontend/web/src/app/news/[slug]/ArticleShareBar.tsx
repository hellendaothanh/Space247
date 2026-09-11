"use client";

import { useState } from "react";
import { Share2, Check, Link2 } from "lucide-react";

interface ArticleShareBarProps {
  title: string;
  slug: string;
}

export default function ArticleShareBar({ title, slug }: ArticleShareBarProps) {
  const [copied, setCopied] = useState(false);

  const getFullUrl = () => {
    if (typeof window !== "undefined") {
      return `${window.location.origin}/news/${slug}`;
    }
    return `https://space247.vn/news/${slug}`;
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(getFullUrl());
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
      setCopied(false);
    }
  };

  const shareFacebook = () => {
    const url = encodeURIComponent(getFullUrl());
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, "_blank", "width=600,height=400");
  };

  const shareZalo = () => {
    const url = encodeURIComponent(getFullUrl());
    window.open(`https://zalo.me/share?url=${url}`, "_blank", "width=600,height=400");
  };

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-xs font-medium text-slate-400 sm:inline">Chia sẻ:</span>

      {/* Facebook */}
      <button
        type="button"
        onClick={shareFacebook}
        title="Chia sẻ qua Facebook"
        className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-blue-600 shadow-2xs transition hover:border-blue-300 hover:bg-blue-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-blue-700"
      >
        <span className="font-extrabold text-xs">f</span>
      </button>

      {/* Zalo */}
      <button
        type="button"
        onClick={shareZalo}
        title="Chia sẻ qua Zalo"
        className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white font-bold text-[11px] text-sky-600 shadow-2xs transition hover:border-sky-300 hover:bg-sky-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-sky-700"
      >
        Z
      </button>

      {/* Copy link */}
      <button
        type="button"
        onClick={handleCopyLink}
        className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold shadow-2xs transition ${
          copied
            ? "border border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
            : "border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
        }`}
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Đã sao chép!</span>
          </>
        ) : (
          <>
            <Link2 className="h-3.5 w-3.5" />
            <span>Sao chép link</span>
          </>
        )}
      </button>
    </div>
  );
}
