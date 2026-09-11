"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import Image from "next/image";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Search,
  Calendar,
  Eye,
  Clock,
  TrendingUp,
  MapPin,
  Calculator,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BookOpen,
  Send,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import type { ArticleListItem, NewsCategory } from "@shared/types";

// Default fallback categories
const DEFAULT_CATEGORIES: NewsCategory[] = [
  {
    id: "cat-1",
    name: "Thị trường BĐS",
    slug: "thi-truong-bds",
    description: "Phân tích biến động cung cầu, giá bán và xu hướng vĩ mô",
    icon: "trending-up",
    display_order: 1,
    article_count: 3,
  },
  {
    id: "cat-2",
    name: "Dự án & Quy hoạch",
    slug: "du-an-quy-hoach",
    description: "Cập nhật tiến độ dự án, thông tin hạ tầng giao thông",
    icon: "building",
    display_order: 2,
    article_count: 2,
  },
  {
    id: "cat-3",
    name: "Tài chính & Ngân hàng",
    slug: "tai-chinh-ngan-hang",
    description: "Gói vay mua nhà, lãi suất thả nổi và phương án dòng tiền",
    icon: "banknote",
    display_order: 3,
    article_count: 2,
  },
  {
    id: "cat-4",
    name: "Phong thủy & Nhà ở",
    slug: "phong-thuy-nha-o",
    description: "Bí quyết kiến tạo không gian sống hài hòa, đón tài lộc",
    icon: "compass",
    display_order: 4,
    article_count: 1,
  },
];

// Default fallback articles
const DEFAULT_ARTICLES: ArticleListItem[] = [
  {
    id: "art-1",
    title: "Toàn cảnh thị trường bất động sản 2026: Điểm sáng phục hồi và chu kỳ tăng trưởng mới",
    slug: "toan-canh-thi-truong-bat-dong-san-2026-diem-sang-phuc-hoi",
    summary:
      "Báo cáo phân tích chuyên sâu về làn sóng phục hồi nguồn cung căn hộ, tác động của 3 bộ luật bất động sản mới và dòng vốn ngoại FDI giải ngân vào hạ tầng.",
    thumbnail_url: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-1",
    category: DEFAULT_CATEGORIES[0],
    tags: ["thị trường 2026", "luật đất đai", "tổng quan"],
    view_count: 3420,
    is_published: true,
    published_at: "2026-09-08T08:30:00Z",
    created_at: "2026-09-08T08:30:00Z",
  },
  {
    id: "art-2",
    title: "Tiến độ đường Vành đai 3 TP.HCM và tiềm năng kích nổ các đô thị vệ tinh",
    slug: "tien-do-duong-vanh-dai-3-tphcm-tiem-nang-do-thi-ve-tinh",
    summary:
      "Cập nhật những nhịp cầu vượt sông Đồng Nai, các nút giao trọng điểm và danh sách các đại đô thị hưởng lợi trực tiếp từ trục hạ tầng huyết mạch.",
    thumbnail_url: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-2",
    category: DEFAULT_CATEGORIES[1],
    tags: ["vành đai 3", "hạ tầng", "đô thị vệ tinh"],
    view_count: 2840,
    is_published: true,
    published_at: "2026-09-06T14:15:00Z",
    created_at: "2026-09-06T14:15:00Z",
  },
  {
    id: "art-3",
    title: "Chiến lược đòn bẩy tài chính: Có nên vay mua nhà khi lãi suất ưu đãi chỉ 5.5%/năm?",
    slug: "chien-luoc-don-bay-tai-chinh-vay-mua-nha-lai-suat-5-5",
    summary:
      "Phân tích ma trận dòng tiền trả nợ, cách chọn kỳ hạn vay 20-30 năm và công thức an toàn '30-40-30' để tránh rủi ro khi lãi suất thả nổi sau thời gian ưu đãi.",
    thumbnail_url: "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-3",
    category: DEFAULT_CATEGORIES[2],
    tags: ["tài chính", "lãi suất", "vay mua nhà"],
    view_count: 2150,
    is_published: true,
    published_at: "2026-09-04T09:00:00Z",
    created_at: "2026-09-04T09:00:00Z",
  },
  {
    id: "art-4",
    title: "Phong thủy căn hộ chung cư: Bí quyết chọn hướng đón sinh khí và bài trí nội thất cát lành",
    slug: "phong-thuy-can-ho-chung-cu-huong-sinh-khi-bai-tri-noi-that",
    summary:
      "Hướng dẫn xác định hướng nhà theo ban công hay cửa chính, cách khắc phục lỗi nhà đối diện thang máy và tối ưu ánh sáng cho không gian sống hiện đại.",
    thumbnail_url: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-4",
    category: DEFAULT_CATEGORIES[3],
    tags: ["phong thủy", "hướng nhà", "không gian sống"],
    view_count: 1890,
    is_published: true,
    published_at: "2026-09-02T10:00:00Z",
    created_at: "2026-09-02T10:00:00Z",
  },
  {
    id: "art-5",
    title: "Đại đô thị sinh thái thông minh: Xu hướng định hình phong cách sống thế hệ mới",
    slug: "dai-do-thi-sinh-thai-thong-minh-xu-huong-dinh-hinh-phong-cach-song",
    summary:
      "Vì sao các khu đô thị tích hợp đa tiện ích all-in-one kề cận sông hồ tự nhiên đang trở thành lựa chọn số một của giới chuyên gia và trí thức.",
    thumbnail_url: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-1",
    category: DEFAULT_CATEGORIES[0],
    tags: ["sống xanh", "đại đô thị", "wellness"],
    view_count: 1650,
    is_published: true,
    published_at: "2026-08-30T11:20:00Z",
    created_at: "2026-08-30T11:20:00Z",
  },
  {
    id: "art-6",
    title: "Đầu tư Shophouse khối đế và Nhà phố kinh doanh: Bí quyết tính tỷ suất hoàn vốn ROI",
    slug: "dau-tu-shophouse-khoi-de-va-nha-pho-kinh-doanh-tinh-ty-suat-roi",
    summary:
      "Phương pháp thẩm định lưu lượng khách bộ hành, chi phí cải tạo mặt bằng và bài toán dòng tiền cho thuê đạt trên 6%/năm kèm biên độ tăng giá vốn.",
    thumbnail_url: "https://images.unsplash.com/photo-1582407947304-fd86f028f716?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-3",
    category: DEFAULT_CATEGORIES[2],
    tags: ["shophouse", "dòng tiền", "đầu tư", "roi"],
    view_count: 2890,
    is_published: true,
    published_at: "2026-08-25T16:00:00Z",
    created_at: "2026-08-25T16:00:00Z",
  },
];

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Gần đây";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "Gần đây";
  }
}

function calculateReadingTime(summary: string): string {
  const words = summary.split(/\s+/).length * 4;
  const minutes = Math.max(3, Math.ceil(words / 150));
  return `${minutes} phút đọc`;
}

function NewsHubContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeCategory = searchParams.get("category") || "all";
  const urlQuery = searchParams.get("q") || "";

  const [categories, setCategories] = useState<NewsCategory[]>(DEFAULT_CATEGORIES);
  const [articles, setArticles] = useState<ArticleListItem[]>(DEFAULT_ARTICLES);
  const [featuredArticles, setFeaturedArticles] = useState<ArticleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(urlQuery);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [subscribed, setSubscribed] = useState(false);
  const [emailInput, setEmailInput] = useState("");

  // Fetch categories & featured articles
  useEffect(() => {
    let mounted = true;
    async function loadInitialData() {
      try {
        const [catsRes, featRes] = await Promise.allSettled([
          apiClient.getNewsCategories(),
          apiClient.getFeaturedArticles(5),
        ]);

        if (mounted) {
          if (catsRes.status === "fulfilled" && catsRes.value?.length > 0) {
            setCategories(catsRes.value);
          }
          if (featRes.status === "fulfilled" && featRes.value?.length > 0) {
            setFeaturedArticles(featRes.value);
          }
        }
      } catch (err) {
        console.error("Failed to load initial news data:", err);
      }
    }
    loadInitialData();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch articles based on category, search, page
  useEffect(() => {
    let mounted = true;
    async function loadArticles() {
      setLoading(true);
      try {
        const res = await apiClient.getArticles({
          page,
          page_size: 6,
          category_slug: activeCategory === "all" ? undefined : activeCategory,
          q: urlQuery || undefined,
        });

        if (mounted && res && res.items?.length > 0) {
          setArticles(res.items);
          setTotalPages(res.total_pages || 1);
        } else if (mounted) {
          // Fallback filtering
          let filtered = [...DEFAULT_ARTICLES];
          if (activeCategory !== "all") {
            filtered = filtered.filter((a) => a.category?.slug === activeCategory);
          }
          if (urlQuery) {
            const lowerQ = urlQuery.toLowerCase();
            filtered = filtered.filter(
              (a) => a.title.toLowerCase().includes(lowerQ) || a.summary.toLowerCase().includes(lowerQ)
            );
          }
          setArticles(filtered);
          setTotalPages(Math.max(1, Math.ceil(filtered.length / 6)));
        }
      } catch {
        if (mounted) {
          let filtered = [...DEFAULT_ARTICLES];
          if (activeCategory !== "all") {
            filtered = filtered.filter((a) => a.category?.slug === activeCategory);
          }
          if (urlQuery) {
            const lowerQ = urlQuery.toLowerCase();
            filtered = filtered.filter(
              (a) => a.title.toLowerCase().includes(lowerQ) || a.summary.toLowerCase().includes(lowerQ)
            );
          }
          setArticles(filtered);
          setTotalPages(1);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadArticles();
    return () => {
      mounted = false;
    };
  }, [activeCategory, urlQuery, page]);

  // Featured hero article (top 1 featured or first article)
  const heroArticle = useMemo(() => {
    if (featuredArticles.length > 0) return featuredArticles[0];
    return articles[0] || DEFAULT_ARTICLES[0];
  }, [featuredArticles, articles]);

  // Trending sidebar list
  const trendingList = useMemo(() => {
    if (featuredArticles.length > 0) return featuredArticles.slice(0, 5);
    return [...DEFAULT_ARTICLES].sort((a, b) => b.view_count - a.view_count).slice(0, 5);
  }, [featuredArticles]);

  const handleCategoryChange = (slug: string) => {
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    if (slug === "all") {
      params.delete("category");
    } else {
      params.set("category", slug);
    }
    router.push(`/news?${params.toString()}`);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    if (searchQuery.trim()) {
      params.set("q", searchQuery.trim());
    } else {
      params.delete("q");
    }
    router.push(`/news?${params.toString()}`);
  };

  const clearSearch = () => {
    setSearchQuery("");
    setPage(1);
    const params = new URLSearchParams(searchParams.toString());
    params.delete("q");
    router.push(`/news?${params.toString()}`);
  };

  const totalArticleCount = useMemo(() => {
    return categories.reduce((sum, c) => sum + (c.article_count || 0), 0) || DEFAULT_ARTICLES.length;
  }, [categories]);

  return (
    <div className="min-h-screen bg-slate-50/60 pb-20 dark:bg-slate-950">
      {/* Header Banner */}
      <div className="relative border-b border-slate-200/80 bg-white py-10 dark:border-slate-800 dark:bg-slate-900 md:py-14">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
            <div className="max-w-2xl space-y-2">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-blue-200/80 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/40 dark:text-blue-300">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Editorial News & Insights Hub</span>
              </div>
              <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-3xl lg:text-4xl">
                Tin Tức & Kiến Thức Bất Động Sản
              </h1>
              <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                Phân tích xu hướng thị trường, quy hoạch hạ tầng, cẩm nang tài chính và phong thủy chuẩn xác 24/7 từ chuyên gia hàng đầu.
              </p>
            </div>

            {/* Quick Search */}
            <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
              <input
                type="text"
                placeholder="Tìm kiếm bài viết, chủ đề..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 py-2.5 pl-10 pr-10 text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-800/80 dark:text-white dark:placeholder:text-slate-500"
              />
              <Search className="pointer-events-none absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-2.5 rounded-full p-0.5 text-slate-400 hover:bg-slate-200 hover:text-slate-600 dark:hover:bg-slate-700"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </form>
          </div>

          {/* Featured Hero Article Banner */}
          {heroArticle && activeCategory === "all" && !urlQuery && (
            <div className="mt-8 overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="grid grid-cols-1 lg:grid-cols-12">
                <div className="relative aspect-16/10 lg:aspect-auto lg:col-span-7">
                  <Image
                    src={heroArticle.thumbnail_url || "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"}
                    alt={heroArticle.title}
                    fill
                    priority
                    className="object-cover transition duration-500 hover:scale-102"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent lg:hidden" />
                </div>

                <div className="flex flex-col justify-between p-6 sm:p-8 lg:col-span-5">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-blue-600 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider text-white shadow-xs">
                        Tiêu điểm
                      </span>
                      {heroArticle.category && (
                        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          {heroArticle.category.name}
                        </span>
                      )}
                    </div>

                    <Link href={`/news/${heroArticle.slug}`} className="group block">
                      <h2 className="text-lg font-extrabold text-slate-900 transition group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400 sm:text-xl lg:text-2xl">
                        {heroArticle.title}
                      </h2>
                    </Link>

                    <p className="line-clamp-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400 sm:text-sm">
                      {heroArticle.summary}
                    </p>
                  </div>

                  <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 dark:border-slate-800/80">
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{formatDate(heroArticle.published_at)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{calculateReadingTime(heroArticle.summary)}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-3.5 w-3.5" />
                        <span>{heroArticle.view_count.toLocaleString("vi-VN")}</span>
                      </span>
                    </div>

                    <Link
                      href={`/news/${heroArticle.slug}`}
                      className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 transition hover:gap-1.5 hover:text-blue-700 dark:text-blue-400"
                    >
                      <span>Đọc tiếp</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        {/* Category Filter Pills */}
        <div className="no-scrollbar flex items-center gap-2 overflow-x-auto pb-2">
          <button
            type="button"
            onClick={() => handleCategoryChange("all")}
            className={`flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition ${
              activeCategory === "all"
                ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                : "border border-slate-200 bg-white text-slate-600 hover:border-blue-200 hover:bg-blue-50/50 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
            }`}
          >
            <span>Tất cả bài viết</span>
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                activeCategory === "all"
                  ? "bg-blue-700 text-white"
                  : "bg-slate-100 text-slate-500 dark:bg-slate-800"
              }`}
            >
              {totalArticleCount}
            </span>
          </button>

          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => handleCategoryChange(cat.slug)}
              className={`flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition ${
                activeCategory === cat.slug
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "border border-slate-200 bg-white text-slate-600 hover:border-blue-200 hover:bg-blue-50/50 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
              }`}
            >
              <span>{cat.name}</span>
              {cat.article_count > 0 && (
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                    activeCategory === cat.slug
                      ? "bg-blue-700 text-white"
                      : "bg-slate-100 text-slate-500 dark:bg-slate-800"
                  }`}
                >
                  {cat.article_count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* 2-Column Grid: Articles (Col 8) + Sidebar (Col 4) */}
        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Main Articles List */}
          <div className="space-y-6 lg:col-span-8">
            {urlQuery && (
              <div className="flex items-center justify-between rounded-2xl border border-blue-100 bg-blue-50/60 px-4 py-3 text-xs text-slate-700 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-slate-300">
                <span>
                  Kết quả tìm kiếm cho từ khóa: <strong className="font-semibold text-blue-700 dark:text-blue-400">"{urlQuery}"</strong>
                </span>
                <button
                  type="button"
                  onClick={clearSearch}
                  className="font-medium text-blue-600 underline hover:text-blue-800"
                >
                  Xóa bộ lọc
                </button>
              </div>
            )}

            {loading ? (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                    <div className="aspect-16/10 rounded-xl bg-slate-200 dark:bg-slate-800" />
                    <div className="mt-4 h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
                    <div className="mt-2 h-3 w-full rounded bg-slate-200 dark:bg-slate-800" />
                    <div className="mt-1 h-3 w-2/3 rounded bg-slate-200 dark:bg-slate-800" />
                  </div>
                ))}
              </div>
            ) : articles.length === 0 ? (
              <div className="rounded-3xl border border-slate-200/80 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
                <BookOpen className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700" />
                <h3 className="mt-4 text-base font-bold text-slate-800 dark:text-white">Không tìm thấy bài viết phù hợp</h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Thử tìm kiếm với từ khóa khác hoặc chuyển sang danh mục tin tức tổng hợp.
                </p>
                <button
                  type="button"
                  onClick={() => handleCategoryChange("all")}
                  className="mt-5 rounded-full bg-blue-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-blue-500/20 hover:bg-blue-700"
                >
                  Xem tất cả bài viết
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {articles.map((article) => (
                  <article
                    key={article.id}
                    className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition duration-200 hover:-translate-y-1 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                  >
                    <Link href={`/news/${article.slug}`} className="relative aspect-16/10 overflow-hidden bg-slate-100 dark:bg-slate-800">
                      <Image
                        src={article.thumbnail_url || "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"}
                        alt={article.title}
                        fill
                        className="object-cover transition duration-300 group-hover:scale-105"
                      />
                      {article.category && (
                        <span className="absolute left-3 top-3 rounded-lg bg-white/90 px-2.5 py-1 text-[10px] font-bold text-slate-800 shadow-xs backdrop-blur-xs dark:bg-slate-900/90 dark:text-slate-200">
                          {article.category.name}
                        </span>
                      )}
                    </Link>

                    <div className="flex flex-1 flex-col justify-between p-5">
                      <div className="space-y-2">
                        <Link href={`/news/${article.slug}`} className="block">
                          <h3 className="line-clamp-2 text-sm font-bold leading-snug text-slate-900 transition group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400">
                            {article.title}
                          </h3>
                        </Link>
                        <p className="line-clamp-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                          {article.summary}
                        </p>
                      </div>

                      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-[11px] text-slate-400 dark:border-slate-800/80">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(article.published_at)}</span>
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            <span>{article.view_count.toLocaleString("vi-VN")}</span>
                          </span>
                        </div>
                        <span className="font-semibold text-blue-600 dark:text-blue-400">Chi tiết →</span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-6">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-40 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setPage(num)}
                    className={`flex h-9 min-w-9 items-center justify-center rounded-xl px-2 text-xs font-bold transition ${
                      page === num
                        ? "bg-blue-600 text-white shadow-xs"
                        : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                    }`}
                  >
                    {num}
                  </button>
                ))}
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-40 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>

          {/* Sidebar (Col 4) */}
          <div className="space-y-6 lg:col-span-4">
            {/* Widget: Tin Đọc Nhiều Nhất */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-3.5 dark:border-slate-800">
                <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Tin Đọc Nhiều Nhất</h3>
              </div>

              <div className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
                {trendingList.map((item, idx) => (
                  <Link
                    key={item.id}
                    href={`/news/${item.slug}`}
                    className="group flex items-start gap-3 py-3 transition first:pt-0 last:pb-0"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-xs font-extrabold text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                      0{idx + 1}
                    </span>
                    <div className="space-y-1">
                      <h4 className="line-clamp-2 text-xs font-semibold text-slate-800 transition group-hover:text-blue-600 dark:text-slate-200 dark:group-hover:text-blue-400">
                        {item.title}
                      </h4>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span>{item.category?.name || "Thị trường"}</span>
                        <span>•</span>
                        <span className="flex items-center gap-0.5">
                          <Eye className="h-3 w-3" />
                          <span>{item.view_count.toLocaleString("vi-VN")}</span>
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Widget: Bảng Tính Vay Mua Nhà */}
            <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-blue-50/80 p-5 dark:border-indigo-900/40 dark:from-indigo-950/30 dark:to-blue-950/30">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-500/20">
                  <Calculator className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white">Bảng Tính Vay Mua Nhà</h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Dự phóng gốc & lãi hàng tháng</p>
                </div>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                Tính toán chính xác lịch trả nợ theo phương thức dư nợ giảm dần với lãi suất ưu đãi cập nhật mới nhất từ 15+ ngân hàng.
              </p>
              <Link
                href="/properties"
                className="mt-4 flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 py-2.5 text-xs font-bold text-white shadow-xs transition hover:bg-indigo-700"
              >
                <span>Mở bảng tính tài chính</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Widget: Tra cứu Bản Đồ Quy Hoạch */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
                  <MapPin className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white">Bản Đồ Thông Minh 24/7</h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Tra cứu vị trí và tiện ích bán kính</p>
                </div>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                Khám phá bản đồ nhiệt giá đất, quy hoạch phân khu và tiện ích trường học, bệnh viện trực quan trên nền tảng số.
              </p>
              <Link
                href="/#map-view"
                className="mt-4 flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
              >
                <span>Xem bản đồ vệ tinh</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {/* Widget: Newsletter Subscription */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <h4 className="text-xs font-bold text-slate-900 dark:text-white">Đăng Ký Nhận Bản Tin Tuần</h4>
              <p className="mt-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                Nhận tổng hợp báo cáo thị trường và cơ hội đầu tư BĐS tiềm năng trực tiếp qua email vào mỗi sáng thứ Hai.
              </p>

              {subscribed ? (
                <div className="mt-4 rounded-xl bg-emerald-50 p-3 text-center text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                  ✓ Đăng ký thành công! Cảm ơn bạn.
                </div>
              ) : (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (emailInput.trim()) setSubscribed(true);
                  }}
                  className="mt-3 space-y-2"
                >
                  <input
                    type="email"
                    required
                    placeholder="Nhập email của bạn..."
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-hidden dark:border-slate-800 dark:bg-slate-800 dark:text-white"
                  />
                  <button
                    type="submit"
                    className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-slate-900 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>Đăng ký ngay</span>
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NewsHubPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 py-12 text-center text-slate-400 dark:bg-slate-950">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-xs font-medium">Đang tải Tin tức & Kiến thức Space247...</p>
        </div>
      }
    >
      <NewsHubContent />
    </Suspense>
  );
}
