import Link from "next/link";
import { Building2, Heart } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-12 text-slate-600">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Building2 className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold text-slate-900">
              Space<span className="text-blue-600">247</span>
            </span>
            <span className="text-xs text-slate-400 ml-2">
              Nền tảng Bất động sản AI & Hybrid Search đa nền tảng
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-500">
            <span>FastAPI + pgvector (768-dim)</span>
            <span>Next.js 16 App Router</span>
            <span>HNSW & PostgreSQL FTS</span>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-100 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
          <p>© {new Date().getFullYear()} Space247. All rights reserved.</p>
          <div className="flex items-center gap-1">
            <span>Made with</span>
            <Heart className="h-3.5 w-3.5 text-red-500 fill-red-500" />
            <span>for Vietnamese Real Estate</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
