"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Compass,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Play,
  Eye,
  MapPin,
  Building,
  ArrowRight,
  Flame,
  Trees,
  Train,
  Banknote,
  Palette,
  Search,
  X,
  ExternalLink,
  ChevronRight,
  Activity,
  Coins,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import {
  CuratedCollection,
  CityMarketStats,
  HotArea,
} from "@shared/types";
import PropertyCard from "@/components/common/PropertyCard";

// AI Inspiration Suggestions
const AI_PROMPTS = [
  "Căn hộ gần công viên có ban công thoáng",
  "Nhà phố kinh doanh dòng tiền tốt",
  "Studio gác lửng gần ga Metro",
  "Biệt thự view hồ sinh thái nghỉ dưỡng",
  "Căn hộ cao cấp đầy đủ tiện ích gym hồ bơi",
];

const COLLECTION_FILTER_MAP: Record<string, string> = {
  eco: "ven hồ công viên không gian xanh sinh thái",
  metro: "metro ga tàu điện hạ tầng",
  high_yield: "dòng tiền shophouse kinh doanh cho thuê",
  young_creative: "studio duplex gác lửng phong cách hiện đại",
};

// Fallback Collections in case backend has no initial seed
const FALLBACK_COLLECTIONS: CuratedCollection[] = [
  {
    id: "eco",
    title: "Sống Xanh Ven Hồ",
    subtitle: "Hòa mình cùng thiên nhiên trong lành",
    description: "Tổng hợp các căn hộ cao cấp, biệt thự sinh thái liền kề hồ điều hòa, công viên cây xanh đại ngàn và bãi biển tự nhiên.",
    tag: "Không gian xanh & Wellness",
    icon: "Trees",
    cover_image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    item_count: 4,
    properties: [],
  },
  {
    id: "metro",
    title: "Đón Đầu Tuyến Metro",
    subtitle: "Kết nối siêu tốc 10 phút vào trung tâm",
    description: "Bất động sản đón đầu quy hoạch hạ tầng đô thị hiện đại, chỉ cách ga tàu điện trên cao và metro ngầm vài phút tản bộ.",
    tag: "Hạ tầng & Tiềm năng bứt phá",
    icon: "Train",
    cover_image: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
    item_count: 4,
    properties: [],
  },
  {
    id: "high_yield",
    title: "BĐS Dòng Tiền Vàng",
    subtitle: "Tỷ suất sinh lời cho thuê > 5.5%/năm",
    description: "Tuyển tập shophouse kinh doanh đắc địa, căn hộ cho thuê chuyên gia nước ngoài và mặt bằng thương mại dòng tiền bền vững.",
    tag: "Đầu tư & Thu nhập thụ động",
    icon: "Coins",
    cover_image: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    item_count: 4,
    properties: [],
  },
  {
    id: "young_creative",
    title: "Không Gian Trẻ & Sáng Tạo",
    subtitle: "Phong cách Studio & Gác lửng Duplex",
    description: "Dành riêng cho thế hệ cư dân trẻ năng động: Căn hộ dịch vụ tiện nghi, phòng trọ gác lửng thông minh và studio tự do sáng tạo.",
    tag: "Gen Z & Chuyên gia trẻ",
    icon: "Sparkles",
    cover_image: "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
    item_count: 4,
    properties: [],
  },
];

// Fallback Market Data
const FALLBACK_CITIES: CityMarketStats[] = [
  {
    city: "Thành phố Hà Nội",
    short_name: "Hà Nội",
    avg_price_per_sqm: 68.5,
    min_price_per_sqm: 45.0,
    max_price_per_sqm: 115.0,
    total_listings: 1240,
    change_pct: 4.2,
    trending_district: "Quận Cầu Giấy",
  },
  {
    city: "Thành phố Hồ Chí Minh",
    short_name: "TP.HCM",
    avg_price_per_sqm: 82.0,
    min_price_per_sqm: 52.0,
    max_price_per_sqm: 145.0,
    total_listings: 1890,
    change_pct: 5.1,
    trending_district: "Quận Bình Thạnh",
  },
  {
    city: "Thành phố Đà Nẵng",
    short_name: "Đà Nẵng",
    avg_price_per_sqm: 46.5,
    min_price_per_sqm: 32.0,
    max_price_per_sqm: 85.0,
    total_listings: 620,
    change_pct: 3.4,
    trending_district: "Quận Sơn Trà",
  },
  {
    city: "Thành phố Cần Thơ",
    short_name: "Cần Thơ",
    avg_price_per_sqm: 31.0,
    min_price_per_sqm: 22.0,
    max_price_per_sqm: 55.0,
    total_listings: 310,
    change_pct: 2.8,
    trending_district: "Quận Ninh Kiều",
  },
];

const FALLBACK_HOT_AREAS: HotArea[] = [
  {
    district: "Thành phố Thủ Đức",
    city: "TP.HCM",
    search_volume_score: 98,
    avg_price_million: 78.5,
    highlight: "Hưởng lợi trực tiếp từ tuyến Metro số 1 Bến Thành - Suối Tiên và quy hoạch Trung tâm Đổi mới Sáng tạo.",
  },
  {
    district: "Nam Từ Liêm & Cầu Giấy",
    city: "Hà Nội",
    search_volume_score: 94,
    avg_price_million: 72.0,
    highlight: "Tập trung các tòa tháp văn phòng công nghệ, cộng đồng chuyên gia quốc tế và hạ tầng giao thông đồng bộ.",
  },
  {
    district: "Ngũ Hành Sơn & Sơn Trà",
    city: "Đà Nẵng",
    search_volume_score: 88,
    avg_price_million: 52.5,
    highlight: "Trục phát triển đô thị du lịch nghỉ dưỡng cao cấp ven biển Mỹ Khê và ven sông Cổ Cò.",
  },
  {
    district: "Quận Ninh Kiều & Cái Răng",
    city: "Cần Thơ",
    search_volume_score: 82,
    avg_price_million: 33.0,
    highlight: "Trung tâm kinh tế Tây Nam Bộ với hàng loạt tuyến cao tốc trục liên vùng đang gấp rút hoàn thiện.",
  },
];

// Media Showcase items (Vertical Shorts & 3D Tours)
interface MediaShowcaseItem {
  id: string;
  title: string;
  location: string;
  type: "shorts" | "tour3d" | "review";
  badge: string;
  duration: string;
  views: string;
  thumbnail: string;
  creator: string;
  highlight: string;
  propertyLink?: string;
}

const MEDIA_SHOWCASE_ITEMS: MediaShowcaseItem[] = [
  {
    id: "media-1",
    title: "Tour thực tế Penthouse The River Thủ Thiêm",
    location: "Khu đô thị Thủ Thiêm, TP. Thủ Đức, TP.HCM",
    type: "shorts",
    badge: "Shorts 60s",
    duration: "0:58",
    views: "48.5K",
    thumbnail: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
    creator: "Reviewer Quang Huy",
    highlight: "View trọn sông Sài Gòn & ban công Panorama 30m²",
    propertyLink: "/properties",
  },
  {
    id: "media-2",
    title: "Virtual 3D Tour: Studio Duplex Scandinavian Tây Hồ",
    location: "Quảng An, Tây Hồ, Hà Nội",
    type: "tour3d",
    badge: "3D VR Tour",
    duration: "Tương tác 360°",
    views: "36.2K",
    thumbnail: "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
    creator: "Space247 3D Studio",
    highlight: "Thiết kế gác lửng thông minh, ánh sáng tự nhiên",
    propertyLink: "/properties",
  },
  {
    id: "media-3",
    title: "Khám phá Biệt thự sinh thái Eco Green Village",
    location: "Hòa Xuân, Cẩm Lệ, Đà Nẵng",
    type: "review",
    badge: "Review 4K",
    duration: "1:24",
    views: "29.8K",
    thumbnail: "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=80",
    creator: "BĐS Miền Trung 24/7",
    highlight: "Sân vườn nhiệt đới, hồ bơi điện phân muối riêng",
    propertyLink: "/properties",
  },
  {
    id: "media-4",
    title: "Trải nghiệm Căn hộ 2PN Metro Star Xa Lộ Hà Nội",
    location: "Phước Long A, TP. Thủ Đức, TP.HCM",
    type: "shorts",
    badge: "Shorts 45s",
    duration: "0:45",
    views: "52.1K",
    thumbnail: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80",
    creator: "Kiều Oanh Realtor",
    highlight: "Cầu đi bộ trực tiếp nối thẳng vào ga Metro số 1",
    propertyLink: "/properties",
  },
];

export default function ExplorePage() {
  const router = useRouter();

  // Search input state
  const [searchQuery, setSearchQuery] = useState("");

  // Curated collections state
  const [collections, setCollections] = useState<CuratedCollection[]>(FALLBACK_COLLECTIONS);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>("eco");

  // Market pulse state
  const [cities, setCities] = useState<CityMarketStats[]>(FALLBACK_CITIES);
  const [hotAreas, setHotAreas] = useState<HotArea[]>(FALLBACK_HOT_AREAS);

  // Active Video Modal
  const [activeMedia, setActiveMedia] = useState<MediaShowcaseItem | null>(null);

  // Fetch collections and pulse
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const [collRes, pulseRes] = await Promise.allSettled([
          apiClient.getCuratedCollections(),
          apiClient.getMarketPulse(),
        ]);

        if (isMounted && collRes.status === "fulfilled" && collRes.value?.collections?.length > 0) {
          setCollections(collRes.value.collections);
          setSelectedCollectionId(collRes.value.collections[0].id);
        }

        if (isMounted && pulseRes.status === "fulfilled" && pulseRes.value) {
          if (pulseRes.value.cities && pulseRes.value.cities.length > 0) {
            setCities(pulseRes.value.cities);
          }
          if (pulseRes.value.hot_areas && pulseRes.value.hot_areas.length > 0) {
            setHotAreas(pulseRes.value.hot_areas);
          }
        }
      } catch (err) {
        console.error("Failed to fetch explore data:", err);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    router.push(`/?q=${encodeURIComponent(searchQuery.trim())}`);
  };

  const handlePromptClick = (prompt: string) => {
    setSearchQuery(prompt);
    router.push(`/?q=${encodeURIComponent(prompt)}`);
  };

  // Selected collection
  const activeCollection = useMemo(() => {
    return collections.find((c) => c.id === selectedCollectionId) || collections[0];
  }, [collections, selectedCollectionId]);

  const activeFilterQuery = useMemo(() => {
    return COLLECTION_FILTER_MAP[activeCollection?.id || ""] || activeCollection?.title || "";
  }, [activeCollection]);

  // Helper render collection icon
  const renderCollectionIcon = (iconName: string, className = "h-5 w-5") => {
    switch (iconName) {
      case "Trees":
        return <Trees className={className} />;
      case "Train":
        return <Train className={className} />;
      case "Coins":
      case "Banknote":
        return <Coins className={className} />;
      case "Sparkles":
      case "Palette":
        return <Sparkles className={className} />;
      default:
        return <Building className={className} />;
    }
  };

  const maxPriceSqm = useMemo(() => {
    const values = cities.map((c) => Number(c?.avg_price_per_sqm ?? 0));
    return Math.max(...values, 100);
  }, [cities]);

  return (
    <div className="min-h-screen bg-slate-50/50 pb-24 text-slate-900">
      {/* 1. Hero: Inspiration Center */}
      <section className="relative overflow-hidden border-b border-slate-200/80 bg-gradient-to-b from-blue-900 via-slate-900 to-slate-900 pt-16 pb-20 text-white shadow-inner">
        {/* Background Ambient Glow & Grid */}
        <div className="pointer-events-none absolute inset-0 opacity-20">
          <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-blue-500 blur-3xl" />
          <div className="absolute top-20 right-0 h-96 w-96 rounded-full bg-indigo-500 blur-3xl" />
          <div className="absolute inset-0 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:24px_24px] opacity-25" />
        </div>

        <div className="relative mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-500/10 px-4 py-1.5 text-xs font-semibold text-blue-300 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5 text-blue-400 animate-pulse" />
            <span>Trung Tâm Cảm Hứng & Xu Hướng Bất Động Sản Space247</span>
          </div>

          <h1 className="mt-5 text-3xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl text-white">
            Khám Phá Không Gian Sống <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-emerald-300 bg-clip-text text-transparent">
              Theo Phong Cách Của Bạn
            </span>
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-sm sm:text-base text-slate-300 leading-relaxed">
            Bộ sưu tập bất động sản tuyển lựa độc bản, phân tích nhịp đập giá thị trường 24/7 và trải nghiệm thực tế với video shorts & 3D tour.
          </p>

          {/* Inspiration Search Bar */}
          <div className="mx-auto mt-8 max-w-3xl">
            <form onSubmit={handleSearchSubmit} className="relative flex items-center">
              <div className="relative w-full">
                <Search className="pointer-events-none absolute left-4.5 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Gõ ý tưởng sống của bạn (VD: Căn hộ gần công viên thoáng mát, studio metro...)"
                  className="h-14 w-full rounded-2xl border border-white/20 bg-white/10 pl-12 pr-32 text-sm text-white placeholder-slate-400 backdrop-blur-xl shadow-2xl transition focus:border-blue-400 focus:bg-white/15 focus:outline-none focus:ring-4 focus:ring-blue-500/20"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-blue-500/30 transition hover:bg-blue-500 active:scale-95"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Tìm kiếm AI</span>
                </button>
              </div>
            </form>

            {/* AI Suggestion Pills */}
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
              <span className="text-xs font-medium text-slate-400">Gợi ý cảm hứng:</span>
              {AI_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handlePromptClick(prompt)}
                  className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium text-slate-200 backdrop-blur-sm transition hover:border-blue-400/50 hover:bg-blue-500/20 hover:text-white"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-20 pt-14">
        {/* 2. Curated Lifestyle Collections */}
        <section id="curated-collections" className="space-y-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600">
                <Compass className="h-4 w-4" />
                <span>Bộ Sưu Tập Tuyển Lựa</span>
              </div>
              <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Không Gian Sống Theo Phong Cách Độc Bản
              </h2>
              <p className="mt-1 text-sm text-slate-500 max-w-xl">
                Tuyển chọn những bất động sản tiêu biểu nhất theo 4 chuẩn mực phong cách sống hàng đầu.
              </p>
            </div>

            <Link
              href={`/?q=${encodeURIComponent(activeFilterQuery)}`}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 transition hover:text-blue-700 group"
            >
              <span>Xem tất cả danh mục này</span>
              <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>

          {/* Collection Tab Selector */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {collections.map((col) => {
              const isSelected = col.id === selectedCollectionId;
              return (
                <button
                  key={col.id}
                  type="button"
                  onClick={() => setSelectedCollectionId(col.id)}
                  className={`group relative flex flex-col text-left rounded-2xl p-5 transition-all duration-200 border ${
                    isSelected
                      ? "border-blue-600 bg-white shadow-xl shadow-blue-600/10 ring-2 ring-blue-600"
                      : "border-slate-200/80 bg-white/70 hover:border-slate-300 hover:bg-white hover:shadow-md"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`flex h-11 w-11 items-center justify-center rounded-xl transition ${
                        isSelected
                          ? "bg-blue-600 text-white shadow-md shadow-blue-500/25"
                          : "bg-slate-100 text-slate-700 group-hover:bg-blue-50 group-hover:text-blue-600"
                      }`}
                    >
                      {renderCollectionIcon(col.icon, "h-5 w-5")}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                        isSelected
                          ? "bg-blue-50 text-blue-700"
                          : "bg-slate-100 text-slate-600 group-hover:bg-slate-200"
                      }`}
                    >
                      {col.tag || "Tuyển chọn"}
                    </span>
                  </div>

                  <h3 className="mt-4 text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {col.title}
                  </h3>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
                    {col.description}
                  </p>

                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-[11px] font-medium text-slate-400">
                    <span>
                      {col.properties && col.properties.length > 0
                        ? `${col.properties.length} tin chọn lọc`
                        : "Khám phá ngay"}
                    </span>
                    <ArrowRight
                      className={`h-3.5 w-3.5 transition-transform ${
                        isSelected ? "text-blue-600 translate-x-1" : "text-slate-400 group-hover:translate-x-1"
                      }`}
                    />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Active Collection Property Showcase */}
          <div className="rounded-3xl border border-slate-200/80 bg-gradient-to-b from-white to-slate-50/50 p-6 sm:p-8 shadow-sm">
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/60 pb-5">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
                  {renderCollectionIcon(activeCollection.icon, "h-5 w-5")}
                </span>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">{activeCollection.title}</h3>
                  <p className="text-xs text-slate-500">{activeCollection.description}</p>
                </div>
              </div>

              <Link
                href={`/?q=${encodeURIComponent(activeFilterQuery)}`}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white shadow-xs transition hover:bg-slate-800"
              >
                <span>Xem tất cả trên bản đồ</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Properties List */}
            {activeCollection.properties && activeCollection.properties.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {activeCollection.properties.slice(0, 6).map((property, idx) => (
                  <PropertyCard key={property.id} item={property} index={idx} />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 mb-4">
                  {renderCollectionIcon(activeCollection.icon, "h-8 w-8")}
                </div>
                <h4 className="text-base font-bold text-slate-900">
                  Khám phá danh sách {activeCollection.title}
                </h4>
                <p className="mt-1 max-w-md text-xs text-slate-500">
                  Hệ thống đang đồng bộ dữ liệu thị trường cho bộ sưu tập này. Bấm nút bên dưới để tìm kiếm tự động với AI.
                </p>
                <Link
                  href={`/?q=${encodeURIComponent(activeFilterQuery)}`}
                  className="mt-5 inline-flex items-center gap-2 rounded-full bg-blue-600 px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/25 transition hover:bg-blue-700"
                >
                  <Search className="h-3.5 w-3.5" />
                  <span>Tìm kiếm bất động sản phù hợp</span>
                </Link>
              </div>
            )}
          </div>
        </section>

        {/* 3. Market Price Pulse */}
        <section id="market-pulse" className="space-y-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-600">
                <Activity className="h-4 w-4" />
                <span>Nhịp Đập Thị Trường</span>
              </div>
              <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Chỉ Số Giá & Điểm Nóng Tuần Này
              </h2>
              <p className="mt-1 text-sm text-slate-500 max-w-xl">
                Thống kê đơn giá trung bình (triệu/m²) tại 4 đô thị trọng điểm và các khu vực có tỷ suất tăng trưởng thanh khoản nổi bật.
              </p>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Dữ liệu giao dịch xác thực 24/7</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* 4 Core Cities Price Benchmark (7 cols) */}
            <div className="lg:col-span-7 rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h3 className="text-base font-bold text-slate-900">
                  Đơn Giá Trung Bình 4 Đô Thị Trọng Điểm
                </h3>
                <span className="text-xs font-medium text-slate-400">Đơn vị: Triệu VNĐ / m²</span>
              </div>

              <div className="mt-6 space-y-6">
                {cities.map((cityStat) => {
                  const avgPrice = Number(cityStat?.avg_price_per_sqm ?? 0);
                  const totalListings = Number(cityStat?.total_listings ?? 0);
                  const changePct = Number(cityStat?.change_pct ?? 0);
                  const pctWidth = Math.min(100, Math.round((avgPrice / maxPriceSqm) * 100));
                  const isPositive = changePct >= 0;
                  const cityName = cityStat.short_name || cityStat.city;

                  return (
                    <div key={cityStat.city} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{cityName}</span>
                          {cityStat.trending_district && (
                            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                              {cityStat.trending_district}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-extrabold text-blue-600">
                            {avgPrice.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}{" "}
                            <span className="text-xs font-normal text-slate-500">tr/m²</span>
                          </span>
                          <span
                            className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                              isPositive ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
                            }`}
                          >
                            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                            <span>{isPositive ? `+${changePct}%` : `${changePct}%`}</span>
                          </span>
                        </div>
                      </div>

                      {/* Visual Bar */}
                      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-1000"
                          style={{ width: `${pctWidth}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>{totalListings.toLocaleString("vi-VN")} tin đăng xác thực</span>
                        <Link
                          href={`/?city=${encodeURIComponent(cityName)}`}
                          className="font-medium text-blue-600 hover:underline"
                        >
                          Khám phá {cityName} &rarr;
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Hot Areas / Trending Sub-markets (5 cols) */}
            <div className="lg:col-span-5 rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-orange-500" />
                  <h3 className="text-base font-bold text-slate-900">Điểm Nóng Tuần Này</h3>
                </div>
                <span className="rounded-full bg-orange-50 px-2.5 py-0.5 text-[10px] font-bold text-orange-700">
                  Top Trending
                </span>
              </div>

              <div className="mt-5 space-y-4">
                {hotAreas.map((area, idx) => {
                  const areaPrice = Number(area?.avg_price_million ?? 0);
                  const searchScore = Number(area?.search_volume_score ?? 90);

                  return (
                    <div
                      key={idx}
                      className="group rounded-2xl border border-slate-100 bg-slate-50/50 p-4 transition hover:border-blue-200 hover:bg-blue-50/30"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                            {area.district}
                          </h4>
                          <div className="flex items-center gap-1.5 text-xs text-slate-500">
                            <MapPin className="h-3 w-3 text-slate-400" />
                            <span>{area.city}</span>
                          </div>
                        </div>
                        <span className="shrink-0 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-bold text-emerald-800">
                          Quan tâm {searchScore}/100
                        </span>
                      </div>

                      <div className="mt-2 text-xs font-semibold text-slate-700">
                        Đơn giá TB:{" "}
                        <span className="text-blue-600 font-bold">
                          {areaPrice > 0 ? `${areaPrice.toFixed(1)} tr/m²` : "Đang cập nhật"}
                        </span>
                      </div>

                      <p className="mt-1.5 text-xs text-slate-500 leading-relaxed">
                        {area.highlight}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* 4. Media Showcase (Shorts & 3D Virtual Tours) */}
        <section id="media-showcase" className="space-y-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-600">
                <Play className="h-4 w-4 fill-purple-600" />
                <span>Media Showcase</span>
              </div>
              <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Khám Phá Qua Video Shorts & 3D Tour
              </h2>
              <p className="mt-1 text-sm text-slate-500 max-w-xl">
                Trải nghiệm thực tế không gian sống bằng video review 60 giây và công nghệ dạo bước không gian 3D Virtual Tour tương tác.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-bold text-purple-700">
                Định dạng 9:16 & VR 360°
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {MEDIA_SHOWCASE_ITEMS.map((item) => (
              <div
                key={item.id}
                onClick={() => setActiveMedia(item)}
                className="group relative cursor-pointer overflow-hidden rounded-3xl border border-slate-200/80 bg-slate-900 shadow-lg transition-all duration-300 hover:-translate-y-1.5 hover:shadow-2xl"
              >
                {/* Vertical Aspect Container (9:16) */}
                <div className="relative aspect-[9/14] w-full overflow-hidden">
                  <img
                    src={item.thumbnail}
                    alt={item.title}
                    className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />

                  {/* Gradient Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-black/20" />

                  {/* Top Badges */}
                  <div className="absolute left-3.5 right-3.5 top-3.5 flex items-center justify-between">
                    <span className="rounded-full bg-white/20 px-2.5 py-1 text-[11px] font-bold text-white backdrop-blur-md">
                      {item.badge}
                    </span>
                    <span className="flex items-center gap-1 rounded-full bg-black/40 px-2.5 py-1 text-[10px] font-medium text-white/90 backdrop-blur-md">
                      <Eye className="h-3 w-3" />
                      <span>{item.views}</span>
                    </span>
                  </div>

                  {/* Center Play Icon with Glow */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/25 text-white backdrop-blur-md shadow-2xl transition group-hover:scale-110 group-hover:bg-blue-600">
                      <Play className="h-6 w-6 fill-white translate-x-0.5" />
                    </div>
                  </div>

                  {/* Bottom Information */}
                  <div className="absolute inset-x-0 bottom-0 p-4 space-y-1.5 text-white">
                    <span className="text-[10px] font-semibold text-blue-300">
                      {item.creator} • {item.duration}
                    </span>
                    <h3 className="text-sm font-bold leading-snug line-clamp-2 group-hover:text-blue-300 transition-colors">
                      {item.title}
                    </h3>
                    <p className="text-[11px] text-slate-300 line-clamp-1">
                      {item.highlight}
                    </p>
                    <div className="flex items-center gap-1 text-[10px] text-slate-400 pt-1">
                      <MapPin className="h-3 w-3 shrink-0" />
                      <span className="truncate">{item.location}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Video / 3D Tour Modal */}
      {activeMedia && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl bg-slate-900 shadow-2xl ring-1 ring-white/10">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 text-white">
              <div className="flex items-center gap-2.5">
                <span className="rounded-full bg-blue-600 px-2.5 py-0.5 text-xs font-bold">
                  {activeMedia.badge}
                </span>
                <h4 className="text-sm font-bold truncate max-w-md">{activeMedia.title}</h4>
              </div>
              <button
                type="button"
                onClick={() => setActiveMedia(null)}
                className="rounded-full p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Media Simulation Player */}
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <img
                src={activeMedia.thumbnail}
                alt={activeMedia.title}
                className="h-full w-full object-cover opacity-80"
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40 text-center p-6 text-white">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 shadow-xl mb-3 animate-pulse">
                  <Play className="h-8 w-8 fill-white translate-x-0.5" />
                </div>
                <h5 className="text-lg font-bold">{activeMedia.title}</h5>
                <p className="mt-1 text-xs text-slate-300 max-w-md">{activeMedia.highlight}</p>
                <span className="mt-3 rounded-full bg-white/10 px-3 py-1 text-[11px] font-medium text-slate-300">
                  Đang tải luồng phát trực tiếp độ phân giải cao 4K...
                </span>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 px-6 py-4 text-white bg-slate-950/60">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <MapPin className="h-3.5 w-3.5 text-blue-400" />
                <span>{activeMedia.location}</span>
              </div>

              <div className="flex items-center gap-2.5 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => setActiveMedia(null)}
                  className="w-full sm:w-auto rounded-xl border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-300 transition hover:bg-slate-800"
                >
                  Đóng
                </button>
                <Link
                  href={activeMedia.propertyLink || "/"}
                  onClick={() => setActiveMedia(null)}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-blue-500/25 transition hover:bg-blue-500"
                >
                  <span>Xem bất động sản tương tự</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
