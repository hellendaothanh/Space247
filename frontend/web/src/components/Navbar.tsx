"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  Building2,
  PlusCircle,
  LogIn,
  LogOut,
  ChevronDown,
  LayoutDashboard,
  Heart,
  Bell,
  CheckCheck,
  ExternalLink,
  Menu,
  X,
  MapPin,
  Compass,
  User as UserIcon,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useFavorites } from "@/lib/favorites";
import { apiClient } from "@/lib/api";
import type { UserNotification } from "@shared/types";

function NavbarContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const listingType = searchParams.get("listing_type");
  const view = searchParams.get("view");

  const isExploreActive = pathname === "/" && !listingType && view !== "map";
  const isSaleActive = pathname === "/" && listingType === "sale";
  const isRentActive = pathname === "/" && listingType === "rent";
  const isMapActive = pathname === "/" && view === "map";

  const { user, logout } = useAuth();
  const { favoriteIds } = useFavorites();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Notification Bell state
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<UserNotification[]>([]);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

  // Close mobile menu on page navigation
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Fetch notifications for authenticated user
  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const res = await apiClient.getNotifications(10, 0);
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch {
      // Ignored if unauth or network error
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      // Poll notifications every 30s
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    } else {
      setNotifications([]);
      setUnreadCount(0);
    }
  }, [user]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
      if (notifDropdownRef.current && !notifDropdownRef.current.contains(event.target as Node)) {
        setNotifDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await apiClient.markAllNotificationsRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  };

  const handleNotificationClick = async (notif: UserNotification) => {
    if (!notif.is_read) {
      try {
        await apiClient.markNotificationRead(notif.id);
        setUnreadCount((c) => Math.max(0, c - 1));
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch {
        // Ignored
      }
    }
    setNotifDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20 group-hover:bg-blue-700 transition">
            <Building2 className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight text-slate-900 leading-none">
              Space<span className="text-blue-600">247</span>
            </span>
            <span className="text-[10px] font-medium tracking-wide text-slate-500 mt-1">
              Cổng Thông Tin Bất Động Sản
            </span>
          </div>
        </Link>

        {/* Primary Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-700">
          <Link
            href="/"
            className={`transition hover:text-blue-600 ${
              isExploreActive ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Khám phá
          </Link>
          <Link
            href="/?listing_type=sale"
            className={`transition hover:text-blue-600 ${
              isSaleActive ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Mua bán
          </Link>
          <Link
            href="/?listing_type=rent"
            className={`transition hover:text-blue-600 ${
              isRentActive ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Cho thuê
          </Link>
          <Link
            href="/projects"
            className={`transition hover:text-blue-600 ${
              pathname.startsWith("/projects") ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Dự án
          </Link>
          <Link
            href="/?view=map#map-view"
            className={`flex items-center gap-1.5 transition hover:text-blue-600 ${
              isMapActive ? "text-blue-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <MapPin className="h-3.5 w-3.5 text-blue-600" />
            <span>Bản đồ</span>
          </Link>
        </nav>

        {/* Right Action Cluster */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Post Property CTA */}
          <Link
            href="/properties/create"
            className="hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 active:scale-98 transition cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Đăng tin</span>
          </Link>

          {/* Dedicated Saved Properties / Favorites Button */}
          <Link
            href="/favorites"
            className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-600 border border-slate-200/70 transition cursor-pointer"
            title="Bất động sản đã lưu"
            aria-label="Xem tin đã lưu"
          >
            <Heart className={`h-4 w-4 ${favoriteIds.size > 0 ? "text-rose-500 fill-rose-500/20" : ""}`} />
            {favoriteIds.size > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white shadow-xs">
                {favoriteIds.size > 99 ? "99+" : favoriteIds.size}
              </span>
            )}
          </Link>

          {user ? (
            <div className="flex items-center gap-2">
              {/* Notification Bell Dropdown */}
              <div className="relative" ref={notifDropdownRef}>
                <button
                  type="button"
                  onClick={() => setNotifDropdownOpen((prev) => !prev)}
                  className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200/70 transition cursor-pointer"
                  title="Thông báo bất động sản"
                  aria-expanded={notifDropdownOpen}
                  aria-label="Thông báo"
                >
                  <Bell className="h-4 w-4" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white shadow-xs">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </button>

                {notifDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl border border-slate-200 bg-white shadow-2xl ring-1 ring-slate-900/5 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/70">
                      <div className="flex items-center gap-2">
                        <Bell className="h-4 w-4 text-blue-600" />
                        <span className="text-xs font-bold text-slate-900">Thông báo</span>
                        {unreadCount > 0 && (
                          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                            {unreadCount} mới
                          </span>
                        )}
                      </div>
                      {unreadCount > 0 && (
                        <button
                          type="button"
                          onClick={handleMarkAllRead}
                          className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition cursor-pointer"
                        >
                          <CheckCheck className="h-3.5 w-3.5" />
                          <span>Đã đọc tất cả</span>
                        </button>
                      )}
                    </div>

                    <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                      {notifications.length === 0 ? (
                        <div className="p-6 text-center text-xs text-slate-400">
                          <Bell className="h-8 w-8 mx-auto text-slate-300 mb-2" />
                          <p>Chưa có thông báo nào</p>
                          <p className="text-[10px] text-slate-400 mt-1">
                            Lưu tiêu chí tìm kiếm để nhận thông báo tự động khi có bất động sản mới!
                          </p>
                        </div>
                      ) : (
                        notifications.map((n) => (
                          <div
                            key={n.id}
                            onClick={() => handleNotificationClick(n)}
                            className={`p-3.5 transition cursor-pointer flex gap-3 ${
                              !n.is_read ? "bg-blue-50/40 hover:bg-blue-50/70" : "hover:bg-slate-50"
                            }`}
                          >
                            <div className="mt-0.5">
                              <span
                                className={`flex h-7 w-7 items-center justify-center rounded-full ${
                                  !n.is_read
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-100 text-slate-500"
                                }`}
                              >
                                <Building2 className="h-3.5 w-3.5" />
                              </span>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-1">
                                <h4 className="text-xs font-bold text-slate-900 truncate">
                                  {n.title}
                                </h4>
                                {!n.is_read && (
                                  <span className="h-2 w-2 rounded-full bg-blue-600 shrink-0" />
                                )}
                              </div>
                              <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">
                                {n.message}
                              </p>
                              <div className="flex items-center justify-between mt-1.5 text-[10px] text-slate-400">
                                <span>{new Date(n.created_at).toLocaleString("vi-VN")}</span>
                                {n.property_id && (
                                  <Link
                                    href={`/properties/${n.property_id}`}
                                    className="text-blue-600 font-semibold hover:underline flex items-center gap-0.5"
                                  >
                                    Xem tin <ExternalLink className="h-2.5 w-2.5" />
                                  </Link>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>

                    <div className="p-2 border-t border-slate-100 bg-slate-50 text-center">
                      <Link
                        href="/profile/alerts"
                        onClick={() => setNotifDropdownOpen(false)}
                        className="text-xs font-bold text-blue-600 hover:text-blue-800 transition block py-1"
                      >
                        Quản lý cảnh báo tìm kiếm & tiêu chí →
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              {/* User Account Menu */}
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setDropdownOpen((prev) => !prev)}
                  className="flex items-center gap-2 rounded-xl bg-slate-100 hover:bg-slate-200/80 py-1 px-2 sm:px-2.5 border border-slate-200/70 transition text-left cursor-pointer"
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-xs shrink-0">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
                  </div>
                  <div className="hidden lg:flex flex-col">
                    <span className="text-xs font-semibold text-slate-700 max-w-[100px] truncate leading-tight">
                      {user.full_name}
                    </span>
                    <span className="text-[9px] font-medium uppercase tracking-wider text-blue-600">
                      {user.role}
                    </span>
                  </div>
                  <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-2xl ring-1 ring-slate-900/5 z-50 animate-in fade-in zoom-in-95 duration-100">
                    <div className="px-3 py-2 border-b border-slate-100 mb-1">
                      <p className="text-xs font-bold text-slate-900 truncate">{user.full_name}</p>
                      <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
                    </div>

                    <Link
                      href="/profile"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition"
                    >
                      <UserIcon className="h-4 w-4 text-blue-600" />
                      <span>Thông tin tài khoản</span>
                    </Link>

                    {user.role === "superadmin" && (
                      <Link
                        href="/admin/users"
                        onClick={() => setDropdownOpen(false)}
                        className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-purple-700 bg-purple-50/50 hover:bg-purple-100/70 transition"
                      >
                        <ShieldCheck className="h-4 w-4 text-purple-600" />
                        <span>Quản lý người dùng (RBAC)</span>
                      </Link>
                    )}

                    <Link
                      href="/properties/my"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition"
                    >
                      <LayoutDashboard className="h-4 w-4 text-blue-600" />
                      <span>Quản lý tin đăng</span>
                    </Link>

                    <Link
                      href="/profile/alerts"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition"
                    >
                      <Bell className="h-4 w-4 text-blue-600" />
                      <span>Cảnh báo tìm kiếm</span>
                    </Link>

                    <Link
                      href="/favorites"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-rose-50 hover:text-rose-700 transition"
                    >
                      <Heart className="h-4 w-4 text-rose-500" />
                      <span>Bất động sản đã lưu</span>
                    </Link>

                    <Link
                      href="/properties/create"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition"
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
                      className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 transition cursor-pointer"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>Đăng xuất</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition"
              >
                <LogIn className="h-4 w-4 text-slate-500" />
                <span>Đăng nhập</span>
              </Link>
              <Link
                href="/register"
                className="hidden sm:inline-flex items-center rounded-xl bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
              >
                Đăng ký
              </Link>
            </div>
          )}

          {/* Mobile Hamburger Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="md:hidden flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/70 transition cursor-pointer ml-1"
            aria-label={mobileMenuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-5 space-y-3 shadow-lg animate-in slide-in-from-top-2 duration-150">
          <nav className="flex flex-col space-y-1">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                isExploreActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
              }`}
            >
              <Compass className="h-4 w-4 text-blue-600" />
              <span>Khám phá bất động sản</span>
            </Link>
            <Link
              href="/?listing_type=sale"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                isSaleActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
              }`}
            >
              <Building2 className="h-4 w-4 text-slate-400" />
              <span>Nhà đất bán</span>
            </Link>
            <Link
              href="/?listing_type=rent"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                isRentActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
              }`}
            >
              <Building2 className="h-4 w-4 text-slate-400" />
              <span>Nhà đất cho thuê</span>
            </Link>
            <Link
              href="/projects"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                pathname.startsWith("/projects")
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
              }`}
            >
              <Building2 className="h-4 w-4 text-slate-400" />
              <span>Dự án nổi bật</span>
            </Link>
            <Link
              href="/?view=map#map-view"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition ${
                isMapActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
              }`}
            >
              <MapPin className="h-4 w-4 text-blue-600" />
              <span>Bản đồ trực quan</span>
            </Link>
          </nav>

          <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
            <Link
              href="/properties/create"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Đăng tin miễn phí</span>
            </Link>

            {user ? (
              <div className="flex flex-col gap-1.5 pt-1 border-t border-slate-100">
                <Link
                  href="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-700 hover:bg-blue-50 transition"
                >
                  <UserIcon className="h-4 w-4 text-blue-600" />
                  <span>Hồ sơ tài khoản ({user.full_name})</span>
                </Link>
                {user.role === "superadmin" && (
                  <Link
                    href="/admin/users"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-purple-700 bg-purple-50/50 hover:bg-purple-100 transition"
                  >
                    <ShieldCheck className="h-4 w-4 text-purple-600" />
                    <span>Quản lý người dùng (RBAC)</span>
                  </Link>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 mt-1">
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                >
                  <LogIn className="h-4 w-4" />
                  <span>Đăng nhập</span>
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center rounded-xl bg-slate-900 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition"
                >
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

export default function Navbar() {
  return (
    <Suspense
      fallback={
        <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/95 h-16" />
      }
    >
      <NavbarContent />
    </Suspense>
  );
}
