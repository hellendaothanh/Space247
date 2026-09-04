"use client";

import React, { useState } from "react";
import { Heart } from "lucide-react";
import { useFavorites } from "@/lib/favorites";

interface PropertyFavoriteButtonProps {
  propertyId: string;
}

export default function PropertyFavoriteButton({ propertyId }: PropertyFavoriteButtonProps) {
  const { isFavorite, toggleFavorite } = useFavorites();
  const [isPending, setIsPending] = useState(false);
  const fav = isFavorite(propertyId);

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (isPending) return;
    try {
      setIsPending(true);
      await toggleFavorite(propertyId);
    } catch {
      // Context handles error rollback
    } finally {
      setIsPending(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      disabled={isPending}
      className={`inline-flex items-center gap-1.5 rounded-xl border px-3.5 py-2 text-xs font-medium shadow-xs transition cursor-pointer disabled:opacity-50 ${
        fav
          ? "border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100"
          : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
      }`}
      title={fav ? "Bỏ lưu tin" : "Lưu tin này"}
    >
      <Heart className={`h-4 w-4 transition-transform ${fav ? "fill-rose-500 text-rose-500 scale-110" : "text-slate-500"}`} />
      <span>{fav ? "Đã lưu tin" : "Lưu tin"}</span>
    </button>
  );
}
