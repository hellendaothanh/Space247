"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Bell,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Loader2,
  Filter,
  CheckCheck,
  RefreshCw,
  Clock,
  MapPin,
  Tag,
  Home,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/utils";
import type { SavedSearchAlert, UserNotification, CreateAlertRequest } from "@shared/types";

export default function AlertsManagementPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [alerts, setAlerts] = useState<SavedSearchAlert[]>([]);
  const [notifications, setNotifications] = useState<UserNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"alerts" | "notifications">("alerts");

  // Create alert modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDistrict, setNewDistrict] = useState("");
  const [newCity, setNewCity] = useState("Hà Nội");
  const [newPropertyType, setNewPropertyType] = useState("apartment");
  const [newListingType, setNewListingType] = useState("sale");
  const [newMinPrice, setNewMinPrice] = useState<string>("");
  const [newMaxPrice, setNewMaxPrice] = useState<string>("");
  const [newMinBeds, setNewMinBeds] = useState<string>("");
  const [newFrequency, setNewFrequency] = useState<string>("instant");

  const fetchData = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      const [alertsRes, notifsRes] = await Promise.all([
        apiClient.getAlerts(),
        apiClient.getNotifications(50, 0),
      ]);
      setAlerts(alertsRes);
      setNotifications(notifsRes.items);
    } catch (err) {
      console.error("Failed to load alerts/notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading) {
      if (user) {
        fetchData();
      } else {
        setLoading(false);
      }
    }
  }, [user, authLoading, fetchData]);

  const handleToggleAlert = async (alertItem: SavedSearchAlert) => {
    try {
      const updated = await apiClient.updateAlert(alertItem.id, {
        is_active: !alertItem.is_active,
      });
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertItem.id ? { ...a, is_active: updated.is_active } : a))
      );
    } catch (err) {
      console.error("Failed to toggle alert status:", err);
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa tiêu chí cảnh báo này?")) return;
    try {
      await apiClient.deleteAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (err) {
      console.error("Failed to delete alert:", err);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setIsSubmitting(true);
    try {
      const criteria: Record<string, any> = {};
      if (newCity) criteria.city = newCity;
      if (newDistrict.trim()) criteria.district = newDistrict.trim();
      if (newPropertyType) criteria.property_type = newPropertyType;
      if (newListingType) criteria.listing_type = newListingType;
      if (newMinPrice) criteria.min_price = Number(newMinPrice);
      if (newMaxPrice) criteria.max_price = Number(newMaxPrice);
      if (newMinBeds) criteria.min_bedrooms = Number(newMinBeds);

      const created = await apiClient.createAlert({
        title: newTitle.trim(),
        criteria,
        frequency: newFrequency,
      });

      setAlerts((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setNewTitle("");
      setNewDistrict("");
      setNewMinPrice("");
      setNewMaxPrice("");
      setNewMinBeds("");
    } catch (err) {
      console.error("Failed to create alert:", err);
      alert("Có lỗi khi tạo cảnh báo. Vui lòng kiểm tra lại!");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  };

  const handleDeleteNotification = async (id: string) => {
    try {
      await apiClient.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.error("Failed to delete notification:", err);
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-[450px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md text-center py-16 px-4">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 text-blue-600">
          <Bell className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Đăng nhập để quản lý cảnh báo</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vui lòng đăng nhập để lưu và nhận thông báo khi có bất động sản mới phù hợp nhu cầu của bạn.
        </p>
        <Link
          href="/login"
          className="mt-6 inline-flex items-center justify-center rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition"
        >
          Đăng nhập ngay
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Quản lý Cảnh báo & Tiêu chí Tìm kiếm
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Nhận thông báo ngay khi có bất động sản mới đăng phù hợp với ngân sách và vị trí mong muốn.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>Tạo cảnh báo mới</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-slate-200">
        <button
          type="button"
          onClick={() => setActiveTab("alerts")}
          className={`pb-3 text-sm font-bold transition border-b-2 cursor-pointer ${
            activeTab === "alerts"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          Cảnh báo đã lưu ({alerts.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("notifications")}
          className={`pb-3 text-sm font-bold transition border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "notifications"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          <span>Lịch sử thông báo</span>
          {notifications.filter((n) => !n.is_read).length > 0 && (
            <span className="rounded-full bg-rose-600 text-white text-[10px] font-extrabold px-1.5 py-0.5">
              {notifications.filter((n) => !n.is_read).length}
            </span>
          )}
        </button>
      </div>

      {loading ? (
        <div className="flex min-h-[300px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : activeTab === "alerts" ? (
        /* Alerts List */
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-xs">
              <Bell className="h-12 w-12 mx-auto text-slate-300 mb-3" />
              <h3 className="text-base font-bold text-slate-900">Chưa có cảnh báo tìm kiếm nào</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-6">
                Lưu tiêu chí tìm kiếm (khoảng giá, khu vực, số phòng ngủ) để hệ thống tự động thông báo
                ngay khi có người đăng bán hoặc cho thuê căn phù hợp!
              </p>
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-blue-700 transition"
              >
                <Plus className="h-4 w-4" />
                <span>Thiết lập tiêu chí đầu tiên</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {alerts.map((item) => {
                const crit = item.criteria || {};
                return (
                  <div
                    key={item.id}
                    className={`rounded-2xl border p-5 transition bg-white shadow-xs flex flex-col justify-between ${
                      item.is_active ? "border-slate-200" : "border-slate-200/60 opacity-60 bg-slate-50/50"
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-bold text-sm text-slate-900 line-clamp-1">
                            {item.title}
                          </h3>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Tạo ngày: {new Date(item.created_at).toLocaleDateString("vi-VN")} • Tần suất: {item.frequency}
                          </p>
                        </div>
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                            item.is_active
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-slate-100 text-slate-500 border border-slate-200"
                          }`}
                        >
                          {item.is_active ? "Đang bật" : "Tạm dừng"}
                        </span>
                      </div>

                      {/* Criteria Tags */}
                      <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-100">
                        {crit.city && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-700">
                            <MapPin className="h-3 w-3" />
                            {crit.district ? `${crit.district}, ` : ""}
                            {crit.city}
                          </span>
                        )}
                        {crit.property_type && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-indigo-50 px-2 py-1 text-[11px] font-medium text-indigo-700">
                            <Home className="h-3 w-3" />
                            {crit.property_type}
                          </span>
                        )}
                        {(crit.min_price || crit.max_price) && (
                          <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-700">
                            <Tag className="h-3 w-3" />
                            {crit.min_price ? `Từ ${formatPrice(crit.min_price, "VND", "sale")} ` : ""}
                            {crit.max_price ? `đến ${formatPrice(crit.max_price, "VND", "sale")}` : ""}
                          </span>
                        )}
                        {crit.min_bedrooms && (
                          <span className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700">
                            ≥ {crit.min_bedrooms} PN
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-100 text-xs">
                      <button
                        type="button"
                        onClick={() => handleToggleAlert(item)}
                        className={`font-semibold cursor-pointer transition ${
                          item.is_active ? "text-slate-600 hover:text-slate-900" : "text-blue-600 hover:text-blue-800"
                        }`}
                      >
                        {item.is_active ? "Tạm dừng theo dõi" : "Kích hoạt lại"}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteAlert(item.id)}
                        className="text-rose-600 hover:text-rose-800 font-medium flex items-center gap-1 cursor-pointer transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Xóa</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Notifications List */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">
              Tổng số {notifications.length} thông báo nhận được
            </span>
            {notifications.some((n) => !n.is_read) && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition cursor-pointer"
              >
                <CheckCheck className="h-4 w-4" />
                <span>Đánh dấu tất cả đã đọc</span>
              </button>
            )}
          </div>

          {notifications.length === 0 ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-xs">
              <Bell className="h-10 w-10 mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-bold text-slate-800">Chưa có thông báo nào</p>
              <p className="text-xs text-slate-400 mt-1">
                Khi có tin đăng mới khớp với cảnh báo bạn theo dõi, thông báo sẽ hiển thị tại đây.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
              {notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-4 transition flex items-start justify-between gap-4 ${
                    !notif.is_read ? "bg-blue-50/40" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex gap-3">
                    <span
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full mt-0.5 ${
                        !notif.is_read ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      <Bell className="h-4 w-4" />
                    </span>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{notif.title}</h4>
                      <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{notif.message}</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">
                        {new Date(notif.created_at).toLocaleString("vi-VN")}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {notif.property_id && (
                      <Link
                        href={`/properties/${notif.property_id}`}
                        className="inline-flex items-center gap-1 rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition"
                      >
                        <span>Xem tin</span>
                        <ExternalLink className="h-3 w-3" />
                      </Link>
                    )}
                    <button
                      type="button"
                      onClick={() => handleDeleteNotification(notif.id)}
                      className="text-slate-400 hover:text-rose-600 p-1 transition cursor-pointer"
                      title="Xóa thông báo"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Alert Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 relative animate-in fade-in zoom-in-95">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-6">
              <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Bell className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Thiết lập cảnh báo tìm kiếm mới</h3>
                <p className="text-xs text-slate-500">Nhận thông báo khi có căn nhà mới xuất hiện</p>
              </div>
            </div>

            <form onSubmit={handleCreateAlert} className="space-y-4 text-xs font-medium">
              <div>
                <label className="block text-slate-700 mb-1">Tên gợi nhớ cảnh báo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Căn hộ 2PN Cầu Giấy 3-5 tỷ"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs focus:border-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1">Thành phố</label>
                  <select
                    value={newCity}
                    onChange={(e) => setNewCity(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs bg-white focus:border-blue-500 focus:outline-hidden"
                  >
                    <option value="Hà Nội">Hà Nội</option>
                    <option value="Hồ Chí Minh">Hồ Chí Minh</option>
                    <option value="Đà Nẵng">Đà Nẵng</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 mb-1">Quận / Huyện</label>
                  <input
                    type="text"
                    placeholder="Ví dụ: Cầu Giấy, Bình Thạnh..."
                    value={newDistrict}
                    onChange={(e) => setNewDistrict(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1">Loại BĐS</label>
                  <select
                    value={newPropertyType}
                    onChange={(e) => setNewPropertyType(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs bg-white focus:border-blue-500 focus:outline-hidden"
                  >
                    <option value="apartment">Căn hộ chung cư</option>
                    <option value="house">Nhà phố / Nhà riêng</option>
                    <option value="villa">Biệt thự / Villa</option>
                    <option value="land">Đất nền</option>
                    <option value="commercial">Mặt bằng kinh doanh</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 mb-1">Nhu cầu</label>
                  <select
                    value={newListingType}
                    onChange={(e) => setNewListingType(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs bg-white focus:border-blue-500 focus:outline-hidden"
                  >
                    <option value="sale">Mua bán</option>
                    <option value="rent">Cho thuê</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1">Giá tối thiểu (VND)</label>
                  <input
                    type="number"
                    placeholder="Ví dụ: 3000000000"
                    value={newMinPrice}
                    onChange={(e) => setNewMinPrice(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 mb-1">Giá tối đa (VND)</label>
                  <input
                    type="number"
                    placeholder="Ví dụ: 5000000000"
                    value={newMaxPrice}
                    onChange={(e) => setNewMaxPrice(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1">Số phòng ngủ tối thiểu</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    placeholder="Ví dụ: 2"
                    value={newMinBeds}
                    onChange={(e) => setNewMinBeds(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 mb-1">Tần suất thông báo</label>
                  <select
                    value={newFrequency}
                    onChange={(e) => setNewFrequency(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-slate-900 text-xs bg-white focus:border-blue-500 focus:outline-hidden"
                  >
                    <option value="instant">Tức thì khi có tin mới</option>
                    <option value="daily">Tổng hợp hàng ngày</option>
                    <option value="weekly">Hàng tuần</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-slate-600 hover:bg-slate-50 transition"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !newTitle.trim()}
                  className="rounded-xl bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700 transition disabled:opacity-50"
                >
                  {isSubmitting ? "Đang lưu..." : "Lưu cảnh báo"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
