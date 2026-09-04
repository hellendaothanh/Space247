"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import L from "leaflet";
import { PropertyResponse, SearchResultItem } from "@shared/types";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";

interface PropertyMapClientProps {
  items: (SearchResultItem | PropertyResponse)[];
  selectedId?: string | null;
  onSelectProperty?: (id: string) => void;
}

function escapeHtml(str: string | null | undefined): string {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export default function PropertyMapClient({
  items,
  selectedId,
  onSelectProperty,
}: PropertyMapClientProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const router = useRouter();

  // Keep a ref for callbacks to avoid re-triggering marker reconstruction on every render
  const onSelectPropertyRef = useRef(onSelectProperty);
  onSelectPropertyRef.current = onSelectProperty;

  // Initialize map once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [16.0544, 107.5843],
        zoom: 6,
        scrollWheelZoom: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const markersLayer = L.layerGroup().addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = markersLayer;

      // Invalidate map size after mounting to avoid tile rendering glitches
      setTimeout(() => {
        map.invalidateSize();
      }, 150);
    }
  }, []);

  // Update markers when `items` changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();
    const validCoordinates: [number, number][] = [];

    items.forEach((item, index) => {
      const property: PropertyResponse =
        "property" in item ? (item as SearchResultItem).property : (item as PropertyResponse);
      const similarityScore =
        "property" in item ? (item as SearchResultItem).similarity_score : null;

      // Validate coordinate bounds: Vietnam approx lat 8-24, lng 102-110, reject (0,0)
      if (
        property.latitude !== null &&
        property.latitude !== undefined &&
        property.longitude !== null &&
        property.longitude !== undefined &&
        !Number.isNaN(property.latitude) &&
        !Number.isNaN(property.longitude) &&
        property.latitude >= -90 &&
        property.latitude <= 90 &&
        property.longitude >= -180 &&
        property.longitude <= 180 &&
        !(property.latitude === 0 && property.longitude === 0)
      ) {
        const lat = property.latitude;
        const lng = property.longitude;
        validCoordinates.push([lat, lng]);

        const isSale = property.listing_type === "sale";
        const priceText = escapeHtml(
          formatPrice(property.price, property.currency || "VND", property.listing_type)
        );
        const imageUrl = escapeHtml(getPlaceholderImage(property.property_type, index));
        const safeTitle = escapeHtml(property.title);
        const safePropertyType = escapeHtml(formatPropertyType(property.property_type));
        const safeLocation = escapeHtml(
          [property.district, property.city].filter(Boolean).join(", ")
        );

        const markerHtml = `
          <div role="button" tabindex="0" aria-label="${safeTitle}" class="cursor-pointer transition-transform duration-200 hover:scale-110">
            <div class="flex items-center gap-1 rounded-full ${
              isSale ? "bg-blue-600" : "bg-emerald-600"
            } px-2.5 py-1 text-white font-bold text-[11px] shadow-lg border-2 border-white whitespace-nowrap">
              <span>${priceText}</span>
            </div>
          </div>
        `;

        const customIcon = L.divIcon({
          className: "custom-property-marker",
          html: markerHtml,
          iconSize: [70, 26],
          iconAnchor: [35, 13],
          popupAnchor: [0, -14],
        });

        const marker = L.marker([lat, lng], { icon: customIcon });

        const popupContent = `
          <div style="width: 240px; font-family: inherit;">
            <div style="position: relative; aspect-ratio: 16/10; width: 100%; overflow: hidden; border-radius: 12px; background-color: #f1f5f9;">
              <img src="${imageUrl}" alt="${safeTitle}" style="width: 100%; height: 100%; object-fit: cover;" />
              <div style="position: absolute; top: 6px; left: 6px; background: rgba(15,23,42,0.75); color: #fff; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 9999px;">
                ${safePropertyType}
              </div>
              ${
                typeof similarityScore === "number" && !Number.isNaN(similarityScore)
                  ? `<div style="position: absolute; top: 6px; right: 6px; background: rgba(255,255,255,0.95); color: #4338ca; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 9999px;">
                      ${(similarityScore * 100).toFixed(0)}% phù hợp
                     </div>`
                  : ""
              }
            </div>
            <div style="padding-top: 8px;">
              <div style="font-size: 15px; font-weight: 700; color: #1d4ed8;">
                ${priceText}
              </div>
              <div style="font-size: 13px; font-weight: 600; color: #0f172a; margin-top: 4px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                ${safeTitle}
              </div>
              <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                ${property.area_sqm} m² ${
          property.num_bedrooms ? ` • ${property.num_bedrooms} PN` : ""
        } ${property.num_bathrooms ? ` • ${property.num_bathrooms} WC` : ""}
              </div>
              <div style="font-size: 11px; color: #94a3b8; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${safeLocation}
              </div>
              <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end;">
                <button
                  type="button"
                  data-property-id="${property.id}"
                  class="btn-popup-navigate"
                  style="cursor: pointer; border: none; background-color: #2563eb; color: #ffffff; padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 600;"
                >
                  Xem chi tiết &rarr;
                </button>
              </div>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 280, closeButton: false });

        marker.on("click", () => {
          if (onSelectPropertyRef.current) {
            onSelectPropertyRef.current(property.id);
          }
        });

        markersLayer.addLayer(marker);
      }
    });

    // Auto-fit bounds if we have valid coordinates
    if (validCoordinates.length > 0) {
      const bounds = L.latLngBounds(validCoordinates);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }

    // Attach delegated click listener for popup navigation button to use Next.js router
    const container = mapContainerRef.current;
    if (container) {
      const handlePopupClick = (e: MouseEvent) => {
        const target = (e.target as HTMLElement).closest(".btn-popup-navigate");
        if (target) {
          const propId = target.getAttribute("data-property-id");
          if (propId) {
            router.push(`/properties/${propId}`);
          }
        }
      };
      container.addEventListener("click", handlePopupClick);
      return () => {
        container.removeEventListener("click", handlePopupClick);
      };
    }
  }, [items, router]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="relative h-[650px] w-full overflow-hidden rounded-3xl border border-slate-200/80 bg-slate-100 shadow-md">
      <div ref={mapContainerRef} className="h-full w-full z-10" />
    </div>
  );
}
