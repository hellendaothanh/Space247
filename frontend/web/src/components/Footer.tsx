import Link from "next/link";
import { Building2, Mail, Phone, ShieldCheck, Globe, Video, MessageCircle, Send } from "lucide-react";

interface FooterLink {
  label: string;
  href?: string;
}

const buyAndProjectLinks: FooterLink[] = [
  { label: "Mua bán nhà đất Hà Nội", href: "/?listing_type=sale" },
  { label: "Mua bán nhà đất TP.HCM", href: "/?listing_type=sale" },
  { label: "Dự án Đà Nẵng", href: "/projects" },
  { label: "Dự án Cần Thơ", href: "/projects" },
];

const rentalLinks: FooterLink[] = [
  { label: "Phòng trọ khu Bách Khoa", href: "/rentals" },
  { label: "Căn hộ dịch vụ Tây Hồ", href: "/rentals" },
  { label: "Căn hộ dịch vụ Quận 7", href: "/rentals" },
  { label: "Nhà nguyên căn cho thuê", href: "/rentals" },
];

const utilityLinks: FooterLink[] = [
  { label: "Cổng Chủ nhà (Host Portal)", href: "/host/dashboard" },
  { label: "Ký hợp đồng điện tử & KYC", href: "/profile" },
  { label: "Tính lãi vay mua nhà", href: "/properties" },
  { label: "Tra cứu quy hoạch & bản đồ", href: "/?view=map" },
];

const socialLinks = [
  { label: "Facebook", href: "https://facebook.com", icon: Globe },
  { label: "YouTube", href: "https://youtube.com", icon: Video },
  { label: "Zalo", href: "https://zalo.me", icon: MessageCircle },
  { label: "Telegram", href: "https://t.me", icon: Send },
];

function LinkColumn({ title, links }: { title: string; links: FooterLink[] }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-white">{title}</h2>
      <ul className="mt-5 space-y-3">
        {links.map((link) => (
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
  );
}

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-300">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_repeat(3,1fr)] lg:gap-8">
          {/* Column 1: Brand & legal */}
          <div className="max-w-sm">
            <Link href="/" className="inline-flex items-center gap-2 text-xl font-bold text-white">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-600/20">
                <Building2 className="h-5 w-5" />
              </span>
              Space<span className="text-blue-400">247</span>
            </Link>
            <p className="mt-5 text-sm leading-6 text-slate-400">
              Nền tảng công nghệ bất động sản thế hệ mới: mua bán, thuê trọ và căn hộ dịch vụ
              minh bạch — giao dịch nhanh, an toàn 24/7.
            </p>
            <div className="mt-4 inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Đã đăng ký giao dịch BĐS & xác thực KYC điện tử</span>
            </div>
            <div className="mt-6 space-y-3 text-sm">
              <a href="tel:1900247247" className="flex items-center gap-2 text-slate-300 transition hover:text-white">
                <Phone className="h-4 w-4 text-blue-400" /> Hotline: 1900 247 247
              </a>
              <a href="mailto:support@space247.vn" className="flex items-center gap-2 text-slate-300 transition hover:text-white">
                <Mail className="h-4 w-4 text-blue-400" /> support@space247.vn
              </a>
            </div>
            <div className="mt-6 flex items-center gap-2">
              {socialLinks.map(({ label, href, icon: Icon }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-800 bg-slate-900/60 text-slate-400 transition hover:border-blue-500/50 hover:text-blue-300"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          <LinkColumn title="Mua bán & Dự án" links={buyAndProjectLinks} />
          <LinkColumn title="Cho thuê & Phòng trọ" links={rentalLinks} />
          <LinkColumn title="Tiện ích & Hỗ trợ" links={utilityLinks} />
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 flex flex-col gap-3 border-t border-slate-800 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Space247. Bản quyền thuộc về Nền tảng Bất động sản Space247.</p>
          <p className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-slate-500" />
            Cam kết bảo mật dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP
          </p>
        </div>
      </div>
    </footer>
  );
}
