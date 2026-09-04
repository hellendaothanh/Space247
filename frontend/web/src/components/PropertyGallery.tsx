"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { formatPropertyType, getPlaceholderImage } from "@/lib/utils";

interface PropertyGalleryProps {
  images?: string[];
  propertyType: string;
  title: string;
  listingType?: string;
}

export default function PropertyGallery({
  images,
  propertyType,
  title,
  listingType = "sale",
}: PropertyGalleryProps) {
  const displayImages =
    images && images.length > 0
      ? images
      : [getPlaceholderImage(propertyType, 0)];

  const [currentIndex, setCurrentIndex] = useState(0);

  const prevImage = () => {
    setCurrentIndex((prev) => (prev === 0 ? displayImages.length - 1 : prev - 1));
  };

  const nextImage = () => {
    setCurrentIndex((prev) => (prev === displayImages.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="space-y-3">
      {/* Main Photo Hero */}
      <div className="group relative aspect-16/9 w-full overflow-hidden rounded-3xl bg-slate-100 shadow-lg">
        <img
          src={displayImages[currentIndex]}
          alt={`${title} - ảnh ${currentIndex + 1}`}
          className="h-full w-full object-cover transition duration-300"
        />

        {/* Badges */}
        <div className="absolute top-4 left-4 flex gap-2">
          <span
            className={`rounded-full px-3 py-1 text-xs font-bold shadow-md backdrop-blur-md ${
              listingType === "sale"
                ? "bg-blue-600/90 text-white"
                : "bg-emerald-600/90 text-white"
            }`}
          >
            {listingType === "sale" ? "Bán" : "Cho thuê"}
          </span>
          <span className="rounded-full bg-slate-900/80 px-3 py-1 text-xs font-medium text-white backdrop-blur-md">
            {formatPropertyType(propertyType)}
          </span>
        </div>

        {/* Counter Badge */}
        {displayImages.length > 1 && (
          <div className="absolute bottom-4 right-4 rounded-full bg-black/60 px-3 py-1 text-xs font-medium text-white backdrop-blur-sm">
            {currentIndex + 1} / {displayImages.length}
          </div>
        )}

        {/* Prev / Next Carousel Controls */}
        {displayImages.length > 1 && (
          <>
            <button
              type="button"
              onClick={prevImage}
              aria-label="Ảnh trước"
              className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white opacity-90 transition hover:bg-black/70 focus:outline-hidden cursor-pointer"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={nextImage}
              aria-label="Ảnh kế tiếp"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-2 text-white opacity-90 transition hover:bg-black/70 focus:outline-hidden cursor-pointer"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </>
        )}
      </div>

      {/* Thumbnail Selector Strip */}
      {displayImages.length > 1 && (
        <div className="flex gap-2.5 overflow-x-auto pb-1 pt-1">
          {displayImages.map((img, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setCurrentIndex(idx)}
              aria-label={`Xem ảnh ${idx + 1}`}
              className={`relative h-18 w-24 shrink-0 overflow-hidden rounded-xl border-2 transition cursor-pointer ${
                idx === currentIndex
                  ? "border-blue-600 ring-2 ring-blue-600/30"
                  : "border-transparent opacity-70 hover:opacity-100"
              }`}
            >
              <img
                src={img}
                alt={`Thumbnail ${idx + 1}`}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
