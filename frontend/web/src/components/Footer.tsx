import Link from "next/link";
import { Building2, Mail, Phone, ShieldCheck } from "lucide-react";

interface FooterLink {
  label: string;
  href: string;
}

const realEstateLinks: FooterLink[] = [
  { label: "Mua bán nhà đất", href: "/?listing_type=sale" },
  { label: "Căn hộ dự án", href: "/projects" },
  { label: "Thuê phòng trọ sinh viên", href: "/rentals" },
  { label: "Căn hộ dịch vụ Studio", href: "/rentals" },
  { label: "Biệt thự & Homestay", href: "/rentals" },
];

const serviceLinks: FooterLink[] = [
  { label: "Cổng Chủ nhà (Host Portal)", href: "/host/dashboard" },
  { label: "Bản đồ tra cứu quy hoạch", href: "/?view=map" },
  { label: "Bảng tính lãi suất vay", href: "/properties" },
  { label: "Định giá thông minh AVM", href: "/properties" },
];

export default function Footer() {
  return (
    <footer className="border-t border-slate-200/80 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400 py-12 md:py-16 pb-20 md:pb-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-12 lg:gap-12">
          {/* Cột 1: Thương Hiệu & Hỗ Trợ (md:col-span-4) */}
          <div className="space-y-4 md:col-span-4">
            <Link href="/" className="group inline-flex items-center gap-2.5 text-xl font-extrabold text-slate-900 dark:text-white">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20 transition-transform duration-200 group-hover:scale-105">
                <Building2 className="h-5 w-5" />
              </span>
              <span className="tracking-tight">
                Space<span className="text-blue-600 dark:text-blue-400">247</span>
              </span>
            </Link>

            <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400 max-w-sm">
              Nền tảng công nghệ bất động sản số, kết nối minh bạch và an toàn 24/7.
            </p>

            <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200/80 bg-emerald-50/80 px-2.5 py-1 text-[11px] font-medium text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>Hệ thống xác thực KYC & Hợp đồng điện tử</span>
            </div>

            {/* Khối liên hệ nhanh dạng chip */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <a
                href="tel:1900247247"
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs transition hover:border-blue-300 hover:bg-blue-50/60 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-blue-700 dark:hover:text-blue-400"
              >
                <Phone className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                <span>1900 247 247</span>
              </a>
              <a
                href="mailto:support@space247.vn"
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs transition hover:border-blue-300 hover:bg-blue-50/60 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-blue-700 dark:hover:text-blue-400"
              >
                <Mail className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                <span>support@space247.vn</span>
              </a>
            </div>
          </div>

          {/* Cột 2: Danh Mục Bất Động Sản (md:col-span-2) */}
          <div className="md:col-span-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Danh mục bất động sản
            </h3>
            <ul className="mt-4 space-y-2.5">
              {realEstateLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Cột 3: Dịch Vụ & Tiện Ích (md:col-span-2) */}
          <div className="md:col-span-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Dịch vụ & Tiện ích
            </h3>
            <ul className="mt-4 space-y-2.5">
              {serviceLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs text-slate-600 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Cột 4: Bảo Mật & Kết Nối (md:col-span-4) */}
          <div className="space-y-4 md:col-span-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Bảo mật & Kết nối
            </h3>
            <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Space247 cam kết bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP. Mọi thông tin người dùng, dữ liệu giao dịch và hồ sơ KYC đều được bảo mật và mã hóa đa tầng.
            </p>

            {/* Cụm nút icon mạng xã hội tròn nhỏ thanh lịch */}
            <div className="flex items-center gap-2 pt-1">
              <a
                href="https://facebook.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Facebook Space247"
                className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-2xs transition-all hover:border-blue-500 hover:bg-blue-50 hover:text-blue-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-blue-600 dark:hover:bg-blue-950/40 dark:hover:text-blue-400"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" />
                </svg>
              </a>

              <a
                href="https://zalo.me"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Zalo Space247"
                className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-2xs transition-all hover:border-sky-500 hover:bg-sky-50 hover:text-sky-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-sky-600 dark:hover:bg-sky-950/40 dark:hover:text-sky-400"
              >
                <span className="text-[10px] font-extrabold tracking-tighter">Zalo</span>
              </a>

              <a
                href="https://youtube.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="YouTube Space247"
                className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-2xs transition-all hover:border-rose-500 hover:bg-rose-50 hover:text-rose-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                </svg>
              </a>

              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn Space247"
                className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-2xs transition-all hover:border-blue-700 hover:bg-blue-50 hover:text-blue-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-blue-700 dark:hover:bg-blue-950/40 dark:hover:text-blue-400"
              >
                <svg className="h-3.5 w-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Dải Đáy Chân Trang (Bottom Sub-Footer) */}
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-slate-200 pt-6 text-xs text-slate-500 dark:border-slate-800/80 dark:text-slate-400 md:flex-row">
          <p>© 2026 Space247 Platform. Bản quyền được bảo lưu.</p>
          <div className="flex flex-wrap items-center gap-3">
            <Link href="/terms" className="transition hover:text-slate-800 dark:hover:text-slate-200">
              Quy chế hoạt động
            </Link>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <Link href="/privacy" className="transition hover:text-slate-800 dark:hover:text-slate-200">
              Chính sách bảo mật
            </Link>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <Link href="/complaints" className="transition hover:text-slate-800 dark:hover:text-slate-200">
              Giải quyết khiếu nại
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
