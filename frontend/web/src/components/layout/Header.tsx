"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  Building2,
  Plus,
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

const ROLE_LABELS: Record<string, string> = {
  superadmin: "Quản trị hệ thống",
  admin: "Quản trị viên",
  agent: "Môi giới",
  user: "Thành viên",
};

function HeaderContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const listingType = searchParams.get("listing_type");
  const view = searchParams.get("view");

  const isExploreActive = pathname.startsWith("/explore");
  const isSaleActive = pathname === "/" && listingType === "sale";
  const isRentActive = pathname === "/rentals" || (pathname === "/" && listingType === "rent");
  const isMapActive = pathname === "/" && (view === "map" || (typeof window !== "undefined" && window.location.hash === "#map-view"));

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

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

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
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
    setNotifications([]);
    setUnreadCount(0);
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
        setNotifications((prev) => prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n)));
      } catch {
        // Ignored
      }
    }
    setNotifDropdownOpen(false);
  };

  const handleMapNavClick = (e: React.MouseEvent) => {
    if (pathname === "/") {
      e.preventDefault();
      const mapEl = document.getElementById("map-view");
      if (mapEl) {
        mapEl.scrollIntoView({ behavior: "smooth", block: "start" });
        window.history.replaceState(null, "", "/#map-view");
      }
    }
  };

  const navItems = [
    { label: "Khám phá", href: "/explore", active: isExploreActive },
    { label: "Mua bán", href: "/?listing_type=sale", active: isSaleActive },
    { label: "Cho thuê", href: "/rentals", active: isRentActive },
    { label: "Dự án", href: "/projects", active: pathname.startsWith("/projects") },
    { label: "Bản đồ thông minh", href: "/#map-view", active: isMapActive, icon: true },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/50 bg-white/80 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand Cluster */}
        <Link href="/" className="group flex shrink-0 items-center gap-2.5">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md shadow-blue-500/25 transition group-hover:shadow-lg group-hover:shadow-blue-500/30">
            <Building2 className="h-5 w-5" />
          </span>
          <span className="flex flex-col">
            <span className="text-xl font-bold leading-none tracking-tight text-slate-900">
              Space<span className="text-blue-600">247</span>
            </span>
            <span className="mt-1 text-[10px] font-medium tracking-wide text-slate-500">
              Sàn bất động sản số 24/7
            </span>
          </span>
        </Link>

        {/* Center Navigation */}
        <nav className="hidden items-center gap-1 lg:flex">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              onClick={item.label === "Bản đồ thông minh" ? handleMapNavClick : undefined}
              className={`group relative rounded-full px-3.5 py-2 text-sm transition ${
                item.active
                  ? "bg-blue-50 font-semibold text-blue-700"
                  : "font-medium text-slate-600 hover:bg-slate-100/80 hover:text-slate-900"
              }`}
            >
              <span className="flex items-center gap-1.5">
                {item.icon && <MapPin className="h-3.5 w-3.5 text-blue-600" />}
                <span>{item.label}</span>
              </span>
            </Link>
          ))}
        </nav>

        {/* Right Action Cluster */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          <Link
            href="/properties/create"
            className="hidden items-center gap-1.5 rounded-full bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-blue-500/25 transition hover:bg-blue-700 active:scale-95 sm:inline-flex"
          >
            <Plus className="h-4 w-4" />
            <span>Đăng tin</span>
          </Link>

          <Link
            href="/favorites"
            className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-200/70 bg-white/70 text-slate-600 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
            title="Tin yêu thích"
            aria-label="Tin yêu thích"
          >
            <Heart className={`h-4 w-4 transition ${favoriteIds.size > 0 ? "fill-rose-500/20 text-rose-500" : ""}`} />
            {favoriteIds.size > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white shadow-xs">
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
                  className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-200/70 bg-white/70 text-slate-600 transition hover:bg-slate-100"
                  title="Thông báo"
                  aria-expanded={notifDropdownOpen}
                  aria-label="Thông báo"
                >
                  <Bell className="h-4 w-4" />
                  {unreadCount > 0 && (
                    <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white shadow-xs">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </button>

                {notifDropdownOpen && (
                  <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl ring-1 ring-slate-900/5 animate-in fade-in zoom-in-95 duration-100 sm:w-96">
                    <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-4 py-3">
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
                          className="flex cursor-pointer items-center gap-1 text-[11px] font-semibold text-blue-600 transition hover:text-blue-800"
                        >
                          <CheckCheck className="h-3.5 w-3.5" />
                          <span>Đã đọc tất cả</span>
                        </button>
                      )}
                    </div>

                    <div className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-6 text-center text-xs text-slate-400">
                          <Bell className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                          <p>Chưa có thông báo nào</p>
                          <p className="mt-1 text-[10px] text-slate-400">
                            Lưu tiêu chí tìm kiếm để nhận thông báo tự động khi có bất động sản mới!
                          </p>
                        </div>
                      ) : (
                        notifications.map((n) => (
                          <div
                            key={n.id}
                            onClick={() => handleNotificationClick(n)}
                            className={`flex cursor-pointer gap-3 p-3.5 transition ${
                              !n.is_read ? "bg-blue-50/40 hover:bg-blue-50/70" : "hover:bg-slate-50"
                            }`}
                          >
                            <div className="mt-0.5">
                              <span
                                className={`flex h-7 w-7 items-center justify-center rounded-full ${
                                  !n.is_read ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500"
                                }`}
                              >
                                <Building2 className="h-3.5 w-3.5" />
                              </span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center justify-between gap-1">
                                <h4 className="truncate text-xs font-bold text-slate-900">{n.title}</h4>
                                {!n.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />}
                              </div>
                              <p className="mt-0.5 line-clamp-2 text-[11px] leading-relaxed text-slate-600">{n.message}</p>
                              <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
                                <span>{new Date(n.created_at).toLocaleString("vi-VN")}</span>
                                {n.property_id && (
                                  <Link
                                    href={`/properties/${n.property_id}`}
                                    className="flex items-center gap-0.5 font-semibold text-blue-600 hover:underline"
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

                    <div className="border-t border-slate-100 bg-slate-50 p-2 text-center">
                      <Link
                        href="/profile/alerts"
                        onClick={() => setNotifDropdownOpen(false)}
                        className="block py-1 text-xs font-bold text-blue-600 transition hover:text-blue-800"
                      >
                        Quản lý cảnh báo tìm kiếm & tiêu chí →
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              {/* User Profile Card */}
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setDropdownOpen((prev) => !prev)}
                  className="flex items-center gap-2 rounded-full border border-slate-200/70 bg-white/70 py-1 pl-1 pr-2.5 transition hover:border-blue-200 hover:bg-blue-50/60"
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-blue-700 font-bold text-xs text-white shadow-xs">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
                  </span>
                  <span className="hidden max-w-[110px] truncate text-xs font-semibold text-slate-800 lg:block">
                    {user.full_name}
                  </span>
                  <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 z-50 mt-2 w-60 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-2xl ring-1 ring-slate-900/5 animate-in fade-in zoom-in-95 duration-100">
                    <div className="mb-1 border-b border-slate-100 px-3 py-2.5">
                      <p className="truncate text-xs font-bold text-slate-900">{user.full_name}</p>
                      <p className="truncate text-[11px] text-slate-500">{user.email}</p>
                      <p className="mt-1 inline-flex rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                        {ROLE_LABELS[user.role] || user.role}
                      </p>
                    </div>

                    <Link
                      href="/profile"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-blue-50 hover:text-blue-700"
                    >
                      <UserIcon className="h-4 w-4 text-blue-600" />
                      <span>Trang cá nhân</span>
                    </Link>

                    <Link
                      href="/host/rentals"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-emerald-50 hover:text-emerald-700"
                    >
                      <Building2 className="h-4 w-4 text-emerald-600" />
                      <span>Host Portal (Quản lý khu trọ)</span>
                    </Link>

                    <Link
                      href="/properties/my"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-blue-50 hover:text-blue-700"
                    >
                      <LayoutDashboard className="h-4 w-4 text-blue-600" />
                      <span>Quản lý tin đăng</span>
                    </Link>

                    {user.role === "superadmin" && (
                      <>
                        <Link
                          href="/admin/users"
                          onClick={() => setDropdownOpen(false)}
                          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-purple-700 transition hover:bg-purple-50"
                        >
                          <ShieldCheck className="h-4 w-4 text-purple-600" />
                          <span>Superadmin Portal</span>
                        </Link>
                        <Link
                          href="/admin/kyc"
                          onClick={() => setDropdownOpen(false)}
                          className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-purple-700 transition hover:bg-purple-50"
                        >
                          <ShieldCheck className="h-4 w-4 text-purple-600" />
                          <span>Duyệt hồ sơ KYC</span>
                        </Link>
                      </>
                    )}

                    <div className="my-1 border-t border-slate-100" />

                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        logout();
                      }}
                      className="flex w-full cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-600 transition hover:bg-rose-50"
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
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/70 px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                <LogIn className="h-4 w-4 text-slate-500" />
                <span>Đăng nhập</span>
              </Link>
              <Link
                href="/register"
                className="hidden rounded-full bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 sm:inline-flex"
              >
                Đăng ký
              </Link>
            </div>
          )}

          {/* Mobile Hamburger Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="ml-1 flex h-9 w-9 items-center justify-center rounded-full border border-slate-200/70 bg-white/70 text-slate-700 transition hover:bg-slate-100 lg:hidden"
            aria-label={mobileMenuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="animate-in slide-in-from-top-2 space-y-3 border-t border-slate-200/70 bg-white/95 px-4 pb-5 pt-3 shadow-lg backdrop-blur-md duration-150 lg:hidden">
          <nav className="flex flex-col space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                onClick={(e) => {
                  setMobileMenuOpen(false);
                  if (item.label === "Bản đồ thông minh") {
                    handleMapNavClick(e);
                  }
                }}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition ${
                  item.active ? "bg-blue-50 font-semibold text-blue-700" : "font-medium text-slate-700 hover:bg-slate-50 hover:text-blue-600"
                }`}
              >
                {item.label === "Bản đồ thông minh" ? (
                  <MapPin className="h-4 w-4 text-blue-600" />
                ) : (
                  <Compass className="h-4 w-4 text-blue-600" />
                )}
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          <div className="flex flex-col gap-2 border-t border-slate-100 pt-2">
            <Link
              href="/properties/create"
              onClick={() => setMobileMenuOpen(false)}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white shadow-xs transition hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              <span>Đăng tin miễn phí</span>
            </Link>

            {user ? (
              <div className="flex flex-col gap-1.5 border-t border-slate-100 pt-1">
                <Link
                  href="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-blue-50"
                >
                  <UserIcon className="h-4 w-4 text-blue-600" />
                  <span>Trang cá nhân ({user.full_name})</span>
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2 text-left text-xs font-medium text-rose-600 transition hover:bg-rose-50"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Đăng xuất</span>
                </button>
              </div>
            ) : (
              <div className="mt-1 grid grid-cols-2 gap-2">
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  <LogIn className="h-4 w-4" />
                  <span>Đăng nhập</span>
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center rounded-xl bg-slate-900 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
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

export default function Header() {
  return (
    <Suspense
      fallback={<header className="sticky top-0 z-50 h-16 w-full border-b border-slate-200/50 bg-white/80 backdrop-blur-md" />}
    >
      <HeaderContent />
    </Suspense>
  );
}
