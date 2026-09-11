import { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Calendar,
  Eye,
  Clock,
  ChevronRight,
  Share2,
  Bookmark,
  User as UserIcon,
  Check,
  ArrowLeft,
  BookOpen,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ArticleDetail, ArticleListItem } from "@shared/types";
import ArticleShareBar from "./ArticleShareBar";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

// Fallback articles dictionary for offline / SSR resilience
const FALLBACK_ARTICLES: Record<string, ArticleDetail> = {
  "toan-canh-thi-truong-bat-dong-san-2026-diem-sang-phuc-hoi": {
    id: "art-1",
    title: "Toàn cảnh thị trường bất động sản 2026: Điểm sáng phục hồi và chu kỳ tăng trưởng mới",
    slug: "toan-canh-thi-truong-bat-dong-san-2026-diem-sang-phuc-hoi",
    summary:
      "Báo cáo phân tích chuyên sâu về làn sóng phục hồi nguồn cung căn hộ, tác động của 3 bộ luật bất động sản mới và dòng vốn ngoại FDI giải ngân vào hạ tầng.",
    content: `## 1. Nguồn cung căn hộ mở rộng với pháp lý minh bạch

Bước sang năm 2026, thị trường bất động sản Việt Nam chứng kiến sự chuyển biến mạnh mẽ sau khi bộ 3 luật quan trọng: **Luật Đất đai (sửa đổi), Luật Nhà ở (sửa đổi), và Luật Kinh doanh Bất động sản (sửa đổi)** đi vào thực thi đồng bộ.

Các dự án mới được cấp phép đều phải đáp ứng tiêu chuẩn khắt khe về năng lực tài chính của chủ đầu tư, bảo lãnh ngân hàng và công khai tiến độ thi công thực tế trên cổng thông tin số quốc gia.

### Điểm sáng tại hai đô thị đầu tàu
- **Hà Nội:** Nguồn cung căn hộ sơ cấp ghi nhận mức tăng trưởng 25% so với cùng kỳ, tập trung vào các đại đô thị phía Đông và phía Tây.
- **TP. Hồ Chí Minh:** Phân khúc nhà ở vừa túi tiền và căn hộ dịch vụ dành cho chuyên gia nước ngoài có tỷ lệ hấp thụ đạt trên 85% ngay trong đợt mở bán đầu tiên.

> "Thị trường BĐS năm 2026 không còn chỗ cho các đợt sốt ảo hay đầu cơ lướt sóng. Dòng tiền thông minh đang dịch chuyển rõ nét về các tài sản có giá trị sử dụng thật và pháp lý hoàn chỉnh." — *Ban Nghiên Cứu Thị Trường Space247*

## 2. Xu hướng hạ tầng giao thông dẫn lối đầu tư

Sự bứt phá của hạ tầng giao thông liên vùng tiếp tục đóng vai trò là "bệ phóng" chiến lược cho thị trường địa ốc:

1. **Đường Vành đai 3 TP.HCM & Vành đai 4 Vùng Thủ đô** rút ngắn thời gian di chuyển từ các vùng phụ cận về trung tâm chỉ còn dưới 40 phút.
2. **Hệ thống Metro** bắt đầu vận hành thương mại các tuyến trọng điểm, tạo nên khái niệm *Transit-Oriented Development (TOD)* thúc đẩy giá trị bất động sản quanh ga metro tăng từ 15-20%.
3. **Cảng hàng không quốc tế Long Thành** đẩy nhanh tiến độ hoàn thiện giai đoạn 1, hình thành chuỗi đô thị sân bay và logistics hiện đại.

## 3. Lời khuyên cho người mua nhà và nhà đầu tư cá nhân

Đối với người mua ở thực, đây là thời điểm lý tưởng để lựa chọn các dự án có chính sách thanh toán giãn tiến độ và liên kết hỗ trợ lãi suất từ các ngân hàng thương mại lớn.

Nhà đầu tư dài hạn nên ưu tiên các sản phẩm shophouse khối đế tại khu đô thị đã có cư dân lấp đầy từ 60% trở lên, hoặc các căn hộ studio gần các cụm trường đại học và khu công nghệ cao.`,
    thumbnail_url: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    category_id: "cat-1",
    category: {
      id: "cat-1",
      name: "Thị trường BĐS",
      slug: "thi-truong-bds",
      description: "Phân tích xu hướng",
      display_order: 1,
      article_count: 3,
    },
    author_id: "author-1",
    author: {
      id: "author-1",
      full_name: "Thanh Đào (Trưởng bộ phận Nghiên cứu)",
      email: "research@space247.vn",
      avatar_url: null,
    },
    tags: ["thị trường 2026", "luật đất đai", "tổng quan", "đầu tư"],
    view_count: 3420,
    is_published: true,
    published_at: "2026-09-08T08:30:00Z",
    created_at: "2026-09-08T08:30:00Z",
    related_articles: [
      {
        id: "art-5",
        title: "Đại đô thị sinh thái thông minh: Xu hướng định hình phong cách sống thế hệ mới",
        slug: "dai-do-thi-sinh-thai-thong-minh-xu-huong-dinh-hinh-phong-cach-song",
        summary: "Vì sao các khu đô thị tích hợp all-in-one kề cận sông hồ tự nhiên đang trở thành lựa chọn số một.",
        thumbnail_url: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        category_id: "cat-1",
        tags: ["sống xanh", "đại đô thị"],
        view_count: 1650,
        is_published: true,
        published_at: "2026-08-30T11:20:00Z",
        created_at: "2026-08-30T11:20:00Z",
      },
      {
        id: "art-2",
        title: "Tiến độ đường Vành đai 3 TP.HCM và tiềm năng kích nổ các đô thị vệ tinh",
        slug: "tien-do-duong-vanh-dai-3-tphcm-tiem-nang-do-thi-ve-tinh",
        summary: "Cập nhật những nhịp cầu vượt sông Đồng Nai và các đô thị hưởng lợi trực tiếp từ hạ tầng huyết mạch.",
        thumbnail_url: "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        category_id: "cat-2",
        tags: ["vành đai 3", "hạ tầng"],
        view_count: 2840,
        is_published: true,
        published_at: "2026-09-06T14:15:00Z",
        created_at: "2026-09-06T14:15:00Z",
      },
      {
        id: "art-3",
        title: "Chiến lược đòn bẩy tài chính: Có nên vay mua nhà khi lãi suất ưu đãi chỉ 5.5%/năm?",
        slug: "chien-luoc-don-bay-tai-chinh-vay-mua-nha-lai-suat-5-5",
        summary: "Phân tích ma trận dòng tiền trả nợ và công thức an toàn 30-40-30 để tránh rủi ro lãi suất.",
        thumbnail_url: "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80",
        category_id: "cat-3",
        tags: ["tài chính", "vay mua nhà"],
        view_count: 2150,
        is_published: true,
        published_at: "2026-09-04T09:00:00Z",
        created_at: "2026-09-04T09:00:00Z",
      },
    ],
  },
};

async function fetchArticle(slug: string): Promise<ArticleDetail | null> {
  try {
    const cleanUrl = API_BASE_URL.replace(/\/api\/v1\/?$/, "");
    const res = await fetch(`${cleanUrl}/api/v1/news/${encodeURIComponent(slug)}`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // API failed, fallback
  }
  return FALLBACK_ARTICLES[slug] || null;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const article = await fetchArticle(slug);

  if (!article) {
    return {
      title: "Bài viết không tồn tại | Space247 News",
      description: "Không tìm thấy nội dung bài viết yêu cầu trên Space247.",
    };
  }

  return {
    title: `${article.title} | Space247 News`,
    description: article.summary,
    openGraph: {
      title: article.title,
      description: article.summary,
      url: `/news/${article.slug}`,
      type: "article",
      publishedTime: article.published_at || undefined,
      images: [
        {
          url: article.thumbnail_url || "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab",
          width: 1200,
          height: 630,
          alt: article.title,
        },
      ],
    },
    alternates: {
      canonical: `/news/${article.slug}`,
    },
  };
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Gần đây";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  } catch {
    return "Gần đây";
  }
}

function calculateReadingTime(content: string): string {
  const words = content.split(/\s+/).length;
  const minutes = Math.max(3, Math.ceil(words / 180));
  return `${minutes} phút đọc`;
}

export default async function ArticleDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = await fetchArticle(slug);

  if (!article) {
    notFound();
  }

  return (
    <article className="min-h-screen bg-slate-50/60 pb-20 dark:bg-slate-950">
      {/* Breadcrumbs Navigation */}
      <div className="border-b border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-4xl px-4 py-3 sm:px-6">
          <nav className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <Link href="/" className="hover:text-blue-600 dark:hover:text-blue-400">
              Trang chủ
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
            <Link href="/news" className="hover:text-blue-600 dark:hover:text-blue-400">
              Tin tức
            </Link>
            {article.category && (
              <>
                <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
                <Link
                  href={`/news?category=${article.category.slug}`}
                  className="hover:text-blue-600 dark:hover:text-blue-400"
                >
                  {article.category.name}
                </Link>
              </>
            )}
            <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
            <span className="line-clamp-1 max-w-[200px] font-medium text-slate-800 dark:text-slate-200 sm:max-w-xs">
              {article.title}
            </span>
          </nav>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-4 pt-8 sm:px-6">
        {/* Article Header */}
        <header className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {article.category && (
              <Link
                href={`/news?category=${article.category.slug}`}
                className="rounded-full bg-blue-600 px-3 py-1 text-xs font-bold text-white shadow-xs transition hover:bg-blue-700"
              >
                {article.category.name}
              </Link>
            )}
            <span className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
              <Clock className="h-3.5 w-3.5" />
              <span>{calculateReadingTime(article.content)}</span>
            </span>
          </div>

          <h1 className="text-2xl font-extrabold leading-tight tracking-tight text-slate-900 dark:text-white sm:text-3xl lg:text-4xl">
            {article.title}
          </h1>

          {/* Author & Meta Row */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-y border-slate-200/80 py-3.5 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold text-sm shadow-xs">
                {article.author?.full_name ? article.author.full_name.charAt(0).toUpperCase() : "S"}
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 dark:text-white">
                  {article.author?.full_name || "Ban Biên Tập Space247"}
                </p>
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <span>{formatDate(article.published_at)}</span>
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    <span>{article.view_count.toLocaleString("vi-VN")} lượt xem</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Client Share Actions */}
            <ArticleShareBar title={article.title} slug={article.slug} />
          </div>
        </header>

        {/* Hero Image */}
        {article.thumbnail_url && (
          <figure className="mt-6 overflow-hidden rounded-3xl border border-slate-200/80 bg-slate-100 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="relative aspect-16/9 w-full">
              <Image
                src={article.thumbnail_url}
                alt={article.title}
                fill
                priority
                className="object-cover"
              />
            </div>
            <figcaption className="px-4 py-2 text-center text-[11px] italic text-slate-400 dark:text-slate-500">
              {article.title} — Ảnh minh họa từ Space247 Data Hub.
            </figcaption>
          </figure>
        )}

        {/* Lead Summary Callout */}
        <div className="mt-8 rounded-2xl border-l-4 border-blue-600 bg-white p-5 shadow-xs dark:bg-slate-900">
          <p className="text-sm font-semibold italic leading-relaxed text-slate-700 dark:text-slate-300 sm:text-base">
            "{article.summary}"
          </p>
        </div>

        {/* Article Body Typography (ReactMarkdown) */}
        <div className="mt-8 rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 sm:p-10">
          <div className="prose prose-slate max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h2: ({ children }) => (
                  <h2 className="mt-8 mb-4 border-b border-slate-100 pb-2 text-xl font-bold tracking-tight text-slate-900 dark:border-slate-800 dark:text-white sm:text-2xl">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="mt-6 mb-3 text-lg font-bold text-slate-800 dark:text-slate-200">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="mb-4 text-sm leading-relaxed text-slate-700 dark:text-slate-300 sm:text-base">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="mb-4 list-disc list-inside space-y-2 text-sm text-slate-700 dark:text-slate-300 sm:text-base">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="mb-4 list-decimal list-inside space-y-2 text-sm text-slate-700 dark:text-slate-300 sm:text-base">
                    {children}
                  </ol>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="my-6 rounded-r-2xl border-l-4 border-blue-600 bg-blue-50/60 p-4 italic text-slate-700 dark:bg-blue-950/30 dark:text-slate-300">
                    {children}
                  </blockquote>
                ),
                strong: ({ children }) => (
                  <strong className="font-bold text-slate-900 dark:text-white">{children}</strong>
                ),
              }}
            >
              {article.content}
            </ReactMarkdown>
          </div>

          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="mt-10 border-t border-slate-100 pt-6 dark:border-slate-800">
              <span className="text-xs font-semibold text-slate-400">Từ khóa liên quan:</span>
              <div className="mt-2.5 flex flex-wrap gap-2">
                {article.tags.map((tag) => (
                  <Link
                    key={tag}
                    href={`/news?q=${encodeURIComponent(tag)}`}
                    className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-blue-700 dark:hover:text-blue-400"
                  >
                    #{tag}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Author Box */}
          <div className="mt-8 flex items-center gap-4 rounded-2xl border border-slate-100 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-800/40">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <UserIcon className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                {article.author?.full_name || "Ban Biên Tập & Phân Tích Dữ Liệu Space247"}
              </h4>
              <p className="text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                Cung cấp báo cáo thị trường bất động sản, phân tích chính sách đất đai và cẩm nang tài chính số độc lập, minh bạch và an toàn.
              </p>
            </div>
          </div>
        </div>

        {/* Related Articles Section */}
        {article.related_articles && article.related_articles.length > 0 && (
          <section className="mt-14">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-blue-600" />
                <h3 className="text-base font-extrabold text-slate-900 dark:text-white sm:text-lg">
                  Bài Viết Cùng Chuyên Mục
                </h3>
              </div>
              {article.category && (
                <Link
                  href={`/news?category=${article.category.slug}`}
                  className="text-xs font-semibold text-blue-600 hover:underline dark:text-blue-400"
                >
                  Xem thêm {article.category.name} →
                </Link>
              )}
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
              {article.related_articles.map((rel) => (
                <Link
                  key={rel.id}
                  href={`/news/${rel.slug}`}
                  className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition duration-200 hover:-translate-y-1 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                >
                  <div className="relative aspect-16/10 overflow-hidden bg-slate-100 dark:bg-slate-800">
                    <Image
                      src={rel.thumbnail_url || "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"}
                      alt={rel.title}
                      fill
                      className="object-cover transition duration-300 group-hover:scale-105"
                    />
                  </div>
                  <div className="flex flex-1 flex-col justify-between p-4">
                    <h4 className="line-clamp-2 text-xs font-bold text-slate-900 transition group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400">
                      {rel.title}
                    </h4>
                    <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400">
                      <span>{formatDate(rel.published_at)}</span>
                      <span className="flex items-center gap-0.5">
                        <Eye className="h-3 w-3" />
                        <span>{rel.view_count.toLocaleString("vi-VN")}</span>
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Back button */}
        <div className="mt-10 text-center">
          <Link
            href="/news"
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-xs font-bold text-slate-700 shadow-xs transition hover:border-blue-300 hover:bg-blue-50/50 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Quay lại trang Tin tức</span>
          </Link>
        </div>
      </div>
    </article>
  );
}
