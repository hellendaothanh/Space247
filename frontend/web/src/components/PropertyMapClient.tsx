"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import L from "leaflet";
import {
  AmenityPOI,
  IsochronePropertyItem,
  IsochroneSearchResponse,
  PropertyResponse,
  SearchResultItem,
  TransportMode,
} from "@shared/types";
import { apiClient } from "@/lib/api";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import {
  Compass,
  Clock,
  Car,
  Bike,
  Footprints,
  Bus,
  Search,
  RotateCcw,
  Layers,
  GraduationCap,
  Hospital,
  Train,
  ShoppingCart,
  Loader2,
  MapPin,
} from "lucide-react";

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
  const isochroneLayerRef = useRef<L.GeoJSON | null>(null);
  const landmarkMarkerRef = useRef<L.Marker | null>(null);
  const heatmapLayerRef = useRef<any | null>(null);
  const poiLayerRef = useRef<L.LayerGroup | null>(null);
  const router = useRouter();

  // Isochrone Search State
  const [landmarkQuery, setLandmarkQuery] = useState("");
  const [durationMinutes, setDurationMinutes] = useState<number>(15);
  const [transportMode, setTransportMode] = useState<TransportMode>("motorcycle");
  const [isochroneLoading, setIsochroneLoading] = useState(false);
  const [isochroneResult, setIsochroneResult] = useState<IsochroneSearchResponse | null>(null);
  const [isochroneError, setIsochroneError] = useState("");

  // Amenity Heatmap Layer Controls
  const [activeAmenity, setActiveAmenity] = useState<string | null>(null);
  const [amenityLoading, setAmenityLoading] = useState(false);
  const [poisList, setPoisList] = useState<AmenityPOI[]>([]);

  // Keep a ref for callbacks
  const onSelectPropertyRef = useRef(onSelectProperty);
  onSelectPropertyRef.current = onSelectProperty;

  // 1. Initialize Map once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Require leaflet.heat in browser runtime
      if (typeof window !== "undefined") {
        try {
          require("leaflet.heat");
        } catch {
          // Heat layer fallback will handle if unavailable
        }
      }

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
      const poiLayer = L.layerGroup().addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = markersLayer;
      poiLayerRef.current = poiLayer;

      setTimeout(() => {
        map.invalidateSize();
      }, 200);
    }
  }, []);

  // 2. Render Property Markers
  const activeItems = isochroneResult
    ? isochroneResult.properties.map((item) => item.property)
    : items;

  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();
    const validCoordinates: [number, number][] = [];

    activeItems.forEach((item, index) => {
      const property: PropertyResponse =
        "property" in item ? (item as SearchResultItem).property : (item as PropertyResponse);
      const similarityScore =
        "property" in item ? (item as SearchResultItem).similarity_score : null;

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

        const isSelected = selectedId === property.id;
        const priceFormatted = formatPrice(
          property.price,
          property.currency,
          property.listing_type
        );
        const typeLabel = formatPropertyType(property.property_type);
        const imageUrl = getPlaceholderImage(property.property_type, index);

        // Custom HTML Marker Pin
        const customIcon = L.divIcon({
          className: "space247-custom-marker",
          html: `
            <div class="group relative flex flex-col items-center cursor-pointer transition-transform duration-200 hover:scale-110 ${
              isSelected ? "scale-110 z-50" : "z-10"
            }">
              <div class="px-2.5 py-1 rounded-full font-bold text-xs shadow-md border backdrop-blur-xs flex items-center gap-1 transition-colors whitespace-nowrap ${
                isSelected
                  ? "bg-blue-600 text-white border-blue-700 shadow-blue-500/40 ring-2 ring-blue-400"
                  : "bg-white/95 text-slate-800 border-slate-200/90 shadow-slate-900/10 hover:bg-blue-50 hover:text-blue-700"
              }">
                <span class="text-[10px] uppercase tracking-wider font-semibold opacity-80">${escapeHtml(
                  typeLabel
                )}</span>
                <span class="font-extrabold text-blue-700 ${
                  isSelected ? "text-white" : ""
                }">${escapeHtml(priceFormatted)}</span>
              </div>
              <div class="w-2 h-2 rotate-45 -mt-1 shadow-xs ${
                isSelected ? "bg-blue-600" : "bg-white border-r border-b border-slate-200"
              }"></div>
            </div>
          `,
          iconSize: [120, 36],
          iconAnchor: [60, 36],
        });

        const marker = L.marker([lat, lng], { icon: customIcon });

        // Popup Content
        const popupContent = `
          <div class="w-64 font-sans text-slate-900 overflow-hidden rounded-xl shadow-xs">
            <div class="relative aspect-16/9 w-full bg-slate-100 overflow-hidden">
              <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(
          property.title
        )}" class="w-full h-full object-cover" />
              <div class="absolute top-2 left-2 px-2 py-0.5 rounded-full text-[10px] font-bold text-white ${
                property.listing_type === "sale" ? "bg-blue-600/90" : "bg-emerald-600/90"
              }">
                ${property.listing_type === "sale" ? "Bán" : "Cho thuê"}
              </div>
            </div>
            <div class="p-3">
              <div class="flex items-baseline justify-between gap-1 mb-1">
                <span class="text-sm font-bold text-blue-700">${escapeHtml(priceFormatted)}</span>
                <span class="text-xs font-semibold text-slate-500">${property.area_sqm} m²</span>
              </div>
              <h4 class="text-xs font-semibold line-clamp-2 text-slate-800 mb-2 leading-snug">${escapeHtml(
                property.title
              )}</h4>
              <p class="text-[11px] text-slate-500 line-clamp-1 mb-3">📍 ${escapeHtml(
                [property.district, property.city].filter(Boolean).join(", ")
              )}</p>
              <a href="/properties/${escapeHtml(
                property.id
              )}" class="block w-full text-center py-1.5 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium transition cursor-pointer">
                Xem chi tiết
              </a>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent, {
          closeButton: true,
          offset: [0, -32],
          maxWidth: 280,
          className: "space247-leaflet-popup",
        });

        marker.on("click", () => {
          if (onSelectPropertyRef.current) {
            onSelectPropertyRef.current(property.id);
          }
        });

        markersLayer.addLayer(marker);
      }
    });

    // If no isochrone active, auto fit markers
    if (!isochroneResult && validCoordinates.length > 0) {
      if (validCoordinates.length === 1) {
        map.setView(validCoordinates[0], 14);
      } else {
        const bounds = L.latLngBounds(validCoordinates);
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
      }
    }
  }, [activeItems, selectedId, isochroneResult]);

  // 3. Handle Isochrone Search
  const handleIsochroneSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!landmarkQuery.trim()) return;

    setIsochroneLoading(true);
    setIsochroneError("");

    try {
      const res = await apiClient.isochroneSearch({
        target_landmark: landmarkQuery.trim(),
        max_duration_minutes: durationMinutes,
        transport_mode: transportMode,
      });

      setIsochroneResult(res);

      const map = mapInstanceRef.current;
      if (!map) return;

      // Clear previous isochrone layer and landmark marker
      if (isochroneLayerRef.current) {
        map.removeLayer(isochroneLayerRef.current);
        isochroneLayerRef.current = null;
      }
      if (landmarkMarkerRef.current) {
        map.removeLayer(landmarkMarkerRef.current);
        landmarkMarkerRef.current = null;
      }

      // Add Isochrone Polygon
      const isochroneGeo = L.geoJSON(res.isochrone_geojson, {
        style: {
          color: "#4f46e5",
          weight: 2.5,
          opacity: 0.85,
          dashArray: "6, 6",
          fillColor: "#6366f1",
          fillOpacity: 0.18,
        },
      }).addTo(map);

      isochroneLayerRef.current = isochroneGeo;

      // Add Landmark Pin
      const landmarkIcon = L.divIcon({
        className: "space247-landmark-pin",
        html: `
          <div class="relative flex items-center justify-center">
            <div class="absolute w-8 h-8 rounded-full bg-indigo-500/30 animate-ping"></div>
            <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg border-2 border-white">
              <span class="text-sm">🎯</span>
            </div>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const landmarkMarker = L.marker(
        [res.target_location.latitude, res.target_location.longitude],
        { icon: landmarkIcon }
      ).addTo(map);

      landmarkMarker.bindPopup(`
        <div class="p-2 font-sans">
          <div class="font-bold text-sm text-indigo-900">${escapeHtml(res.target_location.name)}</div>
          <div class="text-xs text-slate-500 mt-0.5">${escapeHtml(
            res.target_location.formatted_address || "Điểm mốc tìm kiếm"
          )}</div>
          <div class="mt-2 text-xs font-semibold text-indigo-600">
            ⏱️ Bán kính: ${res.max_duration_minutes} phút (${res.transport_mode})
          </div>
        </div>
      `);

      landmarkMarkerRef.current = landmarkMarker;

      // Fit map to polygon bounds
      map.fitBounds(isochroneGeo.getBounds(), { padding: [40, 40] });
    } catch (err: any) {
      setIsochroneError(err.message || "Không thể tính toán vùng di chuyển.");
    } finally {
      setIsochroneLoading(false);
    }
  };

  const handleClearIsochrone = () => {
    setLandmarkQuery("");
    setIsochroneResult(null);
    setIsochroneError("");
    const map = mapInstanceRef.current;
    if (map) {
      if (isochroneLayerRef.current) {
        map.removeLayer(isochroneLayerRef.current);
        isochroneLayerRef.current = null;
      }
      if (landmarkMarkerRef.current) {
        map.removeLayer(landmarkMarkerRef.current);
        landmarkMarkerRef.current = null;
      }
    }
  };

  // 4. Handle Amenity Heatmap Layer
  const toggleAmenityLayer = async (category: string) => {
    const map = mapInstanceRef.current;
    const poiLayer = poiLayerRef.current;
    if (!map || !poiLayer) return;

    if (activeAmenity === category) {
      // Turn off
      setActiveAmenity(null);
      setPoisList([]);
      poiLayer.clearLayers();
      if (heatmapLayerRef.current) {
        map.removeLayer(heatmapLayerRef.current);
        heatmapLayerRef.current = null;
      }
      return;
    }

    // Turn on
    setActiveAmenity(category);
    setAmenityLoading(true);

    try {
      const res = await apiClient.getAmenityHeatmap({ category });
      setPoisList(res.pois);
      poiLayer.clearLayers();

      if (heatmapLayerRef.current) {
        map.removeLayer(heatmapLayerRef.current);
        heatmapLayerRef.current = null;
      }

      // 1. Render Heatmap layer if L.heatLayer exists
      if ((L as any).heatLayer && res.heatmap_points.length > 0) {
        const heat = (L as any).heatLayer(res.heatmap_points, {
          radius: 28,
          blur: 18,
          maxZoom: 16,
          gradient: {
            0.2: "#10b981",
            0.4: "#06b6d4",
            0.6: "#eab308",
            0.8: "#f97316",
            1.0: "#ef4444",
          },
        }).addTo(map);
        heatmapLayerRef.current = heat;
      }

      // 2. Render POI Markers with category icons
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
          className: "space247-poi-marker",
          html: `
            <div class="w-6 h-6 rounded-full bg-white shadow-md border border-slate-300 flex items-center justify-center text-xs cursor-pointer hover:scale-125 transition-transform" title="${escapeHtml(poi.name)}">
              ${getCategoryEmoji(poi.category)}
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([poi.latitude, poi.longitude], { icon });
        marker.bindPopup(`
          <div class="p-2 font-sans">
            <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">${poi.category}</div>
            <div class="font-bold text-xs text-slate-800">${escapeHtml(poi.name)}</div>
            ${poi.address ? `<div class="text-[11px] text-slate-500 mt-1">📍 ${escapeHtml(poi.address)}</div>` : ""}
          </div>
        `);
        poiLayer.addLayer(marker);
      });
    } catch (e) {
      console.error("Failed to load amenity heatmap:", e);
    } finally {
      setAmenityLoading(false);
    }
  };

  return (
    <div className="relative h-[650px] w-full overflow-hidden rounded-3xl border border-slate-200/90 shadow-md">
      {/* 1. Top Isochrone Advanced Search Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-col gap-2 max-w-2xl bg-white/95 backdrop-blur-md p-3.5 rounded-2xl shadow-xl border border-slate-200/80">
        <form onSubmit={handleIsochroneSearch} className="flex flex-wrap items-center gap-2">
          {/* Target landmark input */}
          <div className="relative flex-1 min-w-[200px]">
            <Compass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-600" />
            <input
              type="text"
              value={landmarkQuery}
              onChange={(e) => setLandmarkQuery(e.target.value)}
              placeholder="Nhập địa điểm làm việc/học tập (Keangnam, Bến Thành, Landmark 81...)"
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500 font-medium text-slate-800"
            />
          </div>

          {/* Transport mode selector */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 shrink-0">
            <button
              type="button"
              onClick={() => setTransportMode("motorcycle")}
              title="Xe máy"
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                transportMode === "motorcycle"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <Bike className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Xe máy</span>
            </button>
            <button
              type="button"
              onClick={() => setTransportMode("car")}
              title="Ô tô"
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                transportMode === "car"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <Car className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ô tô</span>
            </button>
            <button
              type="button"
              onClick={() => setTransportMode("walking")}
              title="Đi bộ"
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                transportMode === "walking"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <Footprints className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Đi bộ</span>
            </button>
          </div>

          {/* Search CTA */}
          <button
            type="submit"
            disabled={isochroneLoading || !landmarkQuery.trim()}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-sm disabled:opacity-50 cursor-pointer"
          >
            {isochroneLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Search className="w-3.5 h-3.5" />
            )}
            <span>Tìm theo vùng</span>
          </button>

          {/* Reset Isochrone */}
          {isochroneResult && (
            <button
              type="button"
              onClick={handleClearIsochrone}
              title="Bỏ lọc vùng di chuyển"
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </form>

        {/* Duration slider */}
        <div className="flex items-center justify-between text-xs px-1 text-slate-600 gap-4">
          <div className="flex items-center gap-1.5 font-medium shrink-0">
            <Clock className="w-3.5 h-3.5 text-indigo-500" />
            <span>Thời gian di chuyển tối đa:</span>
            <span className="font-bold text-indigo-700">{durationMinutes} phút</span>
          </div>
          <input
            type="range"
            min="5"
            max="30"
            step="5"
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(parseInt(e.target.value))}
            className="w-48 accent-indigo-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
          />
        </div>

        {/* Status / Error note */}
        {isochroneError && (
          <div className="text-[11px] text-rose-600 font-medium px-1">
            ⚠️ {isochroneError}
          </div>
        )}
        {isochroneResult && !isochroneError && (
          <div className="flex items-center justify-between text-[11px] bg-indigo-50/80 px-2.5 py-1 rounded-lg border border-indigo-100 text-indigo-900 font-medium">
            <span>
              🎯 <strong>{isochroneResult.target_location.name}</strong> • Tìm thấy{" "}
              <strong>{isochroneResult.total}</strong> bất động sản trong bán kính{" "}
              {isochroneResult.max_duration_minutes} phút di chuyển.
            </span>
          </div>
        )}
      </div>

      {/* 2. Top-Right Amenity Heatmap Layer Toggles */}
      <div className="absolute top-4 right-4 z-20 hidden md:flex flex-col gap-1.5 bg-white/95 backdrop-blur-md p-2.5 rounded-2xl shadow-xl border border-slate-200">
        <div className="flex items-center gap-1.5 px-1 text-xs font-bold text-slate-700">
          <Layers className="w-3.5 h-3.5 text-slate-500" />
          <span>Lớp Bản Đồ Nhiệt:</span>
          {amenityLoading && <Loader2 className="w-3 h-3 animate-spin text-blue-600" />}
        </div>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => toggleAmenityLayer("school")}
            className={`flex items-center justify-between gap-3 px-2.5 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeAmenity === "school"
                ? "bg-emerald-100 text-emerald-800 font-bold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <span className="flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-emerald-600" />
              <span>Trường học</span>
            </span>
            <span className="text-[10px] text-slate-400">🏫</span>
          </button>

          <button
            onClick={() => toggleAmenityLayer("hospital")}
            className={`flex items-center justify-between gap-3 px-2.5 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeAmenity === "hospital"
                ? "bg-rose-100 text-rose-800 font-bold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <span className="flex items-center gap-1.5">
              <Hospital className="w-3.5 h-3.5 text-rose-600" />
              <span>Bệnh viện</span>
            </span>
            <span className="text-[10px] text-slate-400">🏥</span>
          </button>

          <button
            onClick={() => toggleAmenityLayer("metro")}
            className={`flex items-center justify-between gap-3 px-2.5 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeAmenity === "metro"
                ? "bg-blue-100 text-blue-800 font-bold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <span className="flex items-center gap-1.5">
              <Train className="w-3.5 h-3.5 text-blue-600" />
              <span>Metro / Xe buýt</span>
            </span>
            <span className="text-[10px] text-slate-400">🚇</span>
          </button>

          <button
            onClick={() => toggleAmenityLayer("supermarket")}
            className={`flex items-center justify-between gap-3 px-2.5 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              activeAmenity === "supermarket"
                ? "bg-amber-100 text-amber-800 font-bold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <span className="flex items-center gap-1.5">
              <ShoppingCart className="w-3.5 h-3.5 text-amber-600" />
              <span>Siêu thị / TTTM</span>
            </span>
            <span className="text-[10px] text-slate-400">🛒</span>
          </button>
        </div>
      </div>

      {/* 3. Bottom-Left Map Legend */}
      <div className="absolute bottom-4 left-4 z-20 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-xl shadow-md border border-slate-200 text-[11px] font-medium text-slate-600 flex items-center gap-3">
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
          <span>Bất động sản</span>
        </div>
        {activeAmenity && (
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">| Mật độ tiện ích:</span>
            <span className="w-12 h-2 rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"></span>
            <span className="text-[10px] text-slate-400">Cao</span>
          </div>
        )}
      </div>

      {/* Map DOM Element */}
      <div ref={mapContainerRef} className="h-full w-full bg-slate-100 z-0" />
    </div>
  );
}
