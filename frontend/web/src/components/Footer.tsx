import Link from "next/link";
import { Building2, Mail, Phone } from "lucide-react";

const footerColumns = [
  {
    title: "Danh Mục Bất Động Sản",
    links: [
      { label: "Mua bán nhà đất", href: "/?listing_type=sale" },
      { label: "Căn hộ dự án", href: "/projects" },
      { label: "Phòng trọ & Căn hộ dịch vụ", href: "/rentals" },
      { label: "Homestay nghỉ dưỡng", href: "/rentals" },
    ],
  },
  {
    title: "Dành Cho Khách Hàng & Đối Tác",
    links: [
      { label: "Đăng tin bất động sản", href: "/properties/create" },
      { label: "Dành cho Chủ nhà (Host Portal)", href: "/host/dashboard" },
      { label: "Tiện ích tính lãi vay" },
      { label: "So sánh BĐS bằng AI" },
    ],
  },
  {
    title: "Chính Sách & Hỗ Trợ",
    links: [
      { label: "Quy chế hoạt động" },
      { label: "Chính sách bảo mật dữ liệu" },
      { label: "Quy trình đặt cọc giữ chỗ VietQR", href: "/rentals" },
      { label: "Giải quyết tranh chấp" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-950 text-slate-300">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.35fr_repeat(3,1fr)] lg:gap-8">
          <div className="max-w-sm">
            <Link href="/" className="inline-flex items-center gap-2 text-xl font-bold text-white">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-600/20">
                <Building2 className="h-5 w-5" />
              </span>
              Space<span className="text-blue-400">247</span>
            </Link>
            <p className="mt-5 text-sm leading-6 text-slate-400">
              Nền tảng công nghệ bất động sản thế hệ mới, kết nối mua bán, thuê trọ và căn hộ dịch vụ minh bạch, nhanh chóng.
            </p>
            <div className="mt-6 space-y-3 text-sm">
              <a href="tel:1900247247" className="flex items-center gap-2 text-slate-300 transition hover:text-white">
                <Phone className="h-4 w-4 text-blue-400" /> Hotline: 1900 247 247
              </a>
              <a href="mailto:support@space247.vn" className="flex items-center gap-2 text-slate-300 transition hover:text-white">
                <Mail className="h-4 w-4 text-blue-400" /> support@space247.vn
              </a>
            </div>
          </div>

          {footerColumns.map((column) => (
            <div key={column.title}>
              <h2 className="text-sm font-semibold text-white">{column.title}</h2>
              <ul className="mt-5 space-y-3">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.href ? (
                      <Link href={link.href} className="text-sm leading-6 text-slate-400 transition hover:text-blue-300">
                        {link.label}
                      </Link>
                    ) : (
                      <span className="text-sm leading-6 text-slate-400">{link.label}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-slate-800 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Space247. Bản quyền thuộc về Nền tảng Bất động sản Space247.</p>
          <p>Phát triển vì trải nghiệm bất động sản tại Việt Nam.</p>
        </div>
      </div>
    </footer>
  );
}
