"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { AmenityPOI } from "@shared/types";
import { apiClient } from "@/lib/api";
import { formatPrice, formatPropertyType } from "@/lib/utils";
import {
  ExternalLink,
  Navigation,
  Layers,
  GraduationCap,
  Hospital,
  Train,
  ShoppingCart,
  Loader2,
} from "lucide-react";

interface PropertyDetailMapClientProps {
  latitude: number;
  longitude: number;
  title: string;
  address?: string;
  price?: number;
  currency?: string;
  propertyType?: string;
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

export default function PropertyDetailMapClient({
  latitude,
  longitude,
  title,
  address,
  price,
  currency = "VND",
  propertyType = "apartment",
}: PropertyDetailMapClientProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const poiLayerRef = useRef<L.LayerGroup | null>(null);

  const [activeAmenity, setActiveAmenity] = useState<string | null>(null);
  const [loadingPoi, setLoadingPoi] = useState(false);
  const [pois, setPois] = useState<AmenityPOI[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [latitude, longitude],
        zoom: 15,
        scrollWheelZoom: false,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      // Add property marker
      const priceText = price ? formatPrice(price, currency) : "";
      const typeText = formatPropertyType(propertyType);

      const propertyIcon = L.divIcon({
        className: "space247-property-detail-marker",
        html: `
          <div class="flex flex-col items-center cursor-pointer">
            <div class="px-3 py-1.5 rounded-full font-bold text-xs bg-blue-600 text-white shadow-xl border-2 border-white flex items-center gap-1.5 whitespace-nowrap">
              <span>🏠</span>
              <span>${escapeHtml(priceText || typeText)}</span>
            </div>
            <div class="w-3 h-3 bg-blue-600 rotate-45 -mt-1.5 border-r-2 border-b-2 border-white shadow-xs"></div>
          </div>
        `,
        iconSize: [120, 42],
        iconAnchor: [60, 42],
      });

      const marker = L.marker([latitude, longitude], { icon: propertyIcon }).addTo(map);
      marker.bindPopup(`
        <div class="p-2 font-sans">
          <div class="font-bold text-xs text-slate-800">${escapeHtml(title)}</div>
          ${address ? `<div class="text-[11px] text-slate-500 mt-1">📍 ${escapeHtml(address)}</div>` : ""}
          <div class="mt-2 text-xs font-bold text-blue-700">${escapeHtml(priceText)}</div>
        </div>
      `).openPopup();

      // Radius circle (1km neighborhood)
      L.circle([latitude, longitude], {
        radius: 1000,
        color: "#3b82f6",
        fillColor: "#60a5fa",
        fillOpacity: 0.08,
        weight: 1.5,
        dashArray: "4, 4",
      }).addTo(map);

      const poiLayer = L.layerGroup().addTo(map);
      poiLayerRef.current = poiLayer;
      mapInstanceRef.current = map;

      setTimeout(() => {
        map.invalidateSize();
      }, 150);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [latitude, longitude, title, address, price, currency, propertyType]);

  // Toggle Amenity POIs around this property
  const toggleAmenity = async (category: string) => {
    const map = mapInstanceRef.current;
    const poiLayer = poiLayerRef.current;
    if (!map || !poiLayer) return;

    if (activeAmenity === category) {
      setActiveAmenity(null);
      setPois([]);
      poiLayer.clearLayers();
      return;
    }

    setActiveAmenity(category);
    setLoadingPoi(true);

    try {
      const res = await apiClient.getAmenityHeatmap({
        category,
        center_lat: latitude,
        center_lng: longitude,
        radius_km: 3.5,
      });

      setPois(res.pois);
      poiLayer.clearLayers();

      const getCategoryEmoji = (cat: string) => {
        switch (cat) {
          case "school": return "🏫";
          case "hospital": return "🏥";
          case "metro": return "🚇";
          case "supermarket": return "🛒";
          default: return "📍";
        }
      };

      res.pois.forEach((poi) => {
        const icon = L.divIcon({
          className: "space247-poi-detail-pin",
          html: `
            <div class="w-6 h-6 rounded-full bg-white shadow-md border border-slate-300 flex items-center justify-center text-xs cursor-pointer hover:scale-125 transition-transform">
              ${getCategoryEmoji(poi.category)}
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([poi.latitude, poi.longitude], { icon });
        const distText = poi.distance_meters
          ? `${(poi.distance_meters / 1000).toFixed(1)} km`
          : "";

        marker.bindPopup(`
          <div class="p-2 font-sans text-xs">
            <div class="font-bold text-slate-800">${escapeHtml(poi.name)}</div>
            ${distText ? `<div class="text-blue-600 font-semibold mt-0.5">Khoảng cách: ~${distText}</div>` : ""}
            ${poi.address ? `<div class="text-slate-500 mt-1">📍 ${escapeHtml(poi.address)}</div>` : ""}
          </div>
        `);
        poiLayer.addLayer(marker);
      });
    } catch (err) {
      console.error("Failed to load nearby amenities:", err);
    } finally {
      setLoadingPoi(false);
    }
  };

  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
  const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;

  return (
    <div className="space-y-3">
      {/* Map Container */}
      <div className="relative h-[380px] w-full overflow-hidden rounded-2xl border border-slate-200 shadow-inner">
        {/* Floating Quick Navigation Buttons */}
        <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
          <a
            href={directionsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition"
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Chỉ đường</span>
          </a>
          <a
            href={googleMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/95 hover:bg-white text-slate-700 font-semibold text-xs shadow-md border border-slate-200 transition"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Google Maps</span>
          </a>
        </div>

        {/* Floating Amenity Filters */}
        <div className="absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-1.5 bg-white/95 backdrop-blur-md p-1.5 rounded-xl shadow-md border border-slate-200">
          <span className="text-[11px] font-bold text-slate-600 px-1.5 flex items-center gap-1">
            <Layers className="w-3 h-3 text-slate-400" />
            <span>Tiện ích lân cận:</span>
            {loadingPoi && <Loader2 className="w-3 h-3 animate-spin text-blue-600" />}
          </span>
          <button
            type="button"
            onClick={() => toggleAmenity("school")}
            className={`px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer ${
              activeAmenity === "school"
                ? "bg-emerald-100 text-emerald-800 font-bold"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <GraduationCap className="w-3 h-3 text-emerald-600" />
            <span>Trường học</span>
          </button>
          <button
            type="button"
            onClick={() => toggleAmenity("hospital")}
            className={`px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer ${
              activeAmenity === "hospital"
                ? "bg-rose-100 text-rose-800 font-bold"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Hospital className="w-3 h-3 text-rose-600" />
            <span>Bệnh viện</span>
          </button>
          <button
            type="button"
            onClick={() => toggleAmenity("metro")}
            className={`px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer ${
              activeAmenity === "metro"
                ? "bg-blue-100 text-blue-800 font-bold"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Train className="w-3 h-3 text-blue-600" />
            <span>Metro / Bus</span>
          </button>
          <button
            type="button"
            onClick={() => toggleAmenity("supermarket")}
            className={`px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1 transition cursor-pointer ${
              activeAmenity === "supermarket"
                ? "bg-amber-100 text-amber-800 font-bold"
                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <ShoppingCart className="w-3 h-3 text-amber-600" />
            <span>Siêu thị</span>
          </button>
        </div>

        {/* Map div */}
        <div ref={mapContainerRef} className="h-full w-full bg-slate-100 z-0" />
      </div>

      {/* POI summary if active */}
      {activeAmenity && pois.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto py-1 text-xs">
          <span className="text-slate-500 shrink-0 font-medium">Tìm thấy {pois.length} điểm:</span>
          {pois.map((p) => (
            <div
              key={p.id}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 shrink-0 flex items-center gap-1"
            >
              <span className="font-semibold">{p.name}</span>
              {p.distance_meters && (
                <span className="text-blue-600 font-medium">
                  (~{(p.distance_meters / 1000).toFixed(1)}km)
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
