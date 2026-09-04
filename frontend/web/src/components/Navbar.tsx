import Link from "next/link";
import { Building2, Compass, Sparkles, PlusCircle } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <Building2 className="h-6 w-6" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight text-slate-900">
              Space<span className="text-blue-600">247</span>
            </span>
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              AI Real Estate Platform
            </span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          <Link href="/" className="transition hover:text-blue-600">
            Khám phá
          </Link>
          <Link href="/?listing_type=sale" className="transition hover:text-blue-600">
            Mua bán
          </Link>
          <Link href="/?listing_type=rent" className="transition hover:text-blue-600">
            Cho thuê
          </Link>
          <Link href="/#ai-search" className="flex items-center gap-1.5 text-blue-600">
            <Sparkles className="h-4 w-4" />
            Tìm kiếm bằng AI
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <button
            type="button"
            className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50"
          >
            <Compass className="h-4 w-4 text-slate-500" />
            Bản đồ
          </button>
          <Link
            href="/properties/create"
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition"
          >
            <PlusCircle className="h-4 w-4" />
            Đăng tin
          </Link>
        </div>
      </div>
    </header>
  );
}
