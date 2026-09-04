"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  Sparkles,
  PlusCircle,
  LogIn,
  User,
  LogOut,
  ChevronDown,
  LayoutDashboard,
  Heart,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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
          <Link href="/favorites" className="transition hover:text-rose-600 flex items-center gap-1.5">
            <Heart className="h-4 w-4 text-rose-500" />
            <span>Tin đã lưu</span>
          </Link>
          <Link href="/#ai-search" className="flex items-center gap-1.5 text-blue-600">
            <Sparkles className="h-4 w-4" />
            Tìm kiếm bằng AI
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/properties/create"
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition"
          >
            <PlusCircle className="h-4 w-4" />
            Đăng tin
          </Link>

          {user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <Link
                href="/favorites"
                className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition"
                title="Tin bất động sản đã lưu"
              >
                <Heart className="h-3.5 w-3.5 text-rose-500 fill-rose-500/20" />
                <span>Đã lưu</span>
              </Link>

              <Link
                href="/properties/my"
                className="hidden lg:inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition"
                title="Quản lý tin đăng của tôi"
              >
                <LayoutDashboard className="h-3.5 w-3.5 text-blue-600" />
                <span>Tin của tôi</span>
              </Link>

              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setDropdownOpen((prev) => !prev)}
                  className="flex items-center gap-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 py-1.5 px-3 transition text-left cursor-pointer focus:outline-hidden focus:ring-2 focus:ring-blue-500/30"
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-xs">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-slate-700 max-w-[110px] truncate leading-tight">
                      {user.full_name}
                    </span>
                    <span className="text-[9px] font-medium uppercase tracking-wider text-blue-600">
                      {user.role}
                    </span>
                  </div>
                  <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl ring-1 ring-slate-900/5 z-50">
                    <div className="px-3 py-2 border-b border-slate-100 mb-1">
                      <p className="text-xs font-bold text-slate-900 truncate">{user.full_name}</p>
                      <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
                    </div>

                    <Link
                      href="/favorites"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-rose-50 hover:text-rose-700 transition"
                    >
                      <Heart className="h-4 w-4 text-rose-500" />
                      <span>Tin đã lưu (Yêu thích)</span>
                    </Link>

                    <Link
                      href="/properties/my"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition"
                    >
                      <LayoutDashboard className="h-4 w-4 text-blue-600" />
                      <span>Quản lý tin đăng</span>
                    </Link>

                    <Link
                      href="/properties/create"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition"
                    >
                      <PlusCircle className="h-4 w-4 text-emerald-600" />
                      <span>Đăng tin mới</span>
                    </Link>

                    <div className="my-1 border-t border-slate-100" />

                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        logout();
                      }}
                      className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>Đăng xuất</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
              >
                <LogIn className="h-4 w-4 text-slate-500" />
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="hidden sm:inline-flex items-center rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
              >
                Đăng ký
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

