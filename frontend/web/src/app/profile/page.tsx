"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User as UserIcon,
  Shield,
  KeyRound,
  Building2,
  Heart,
  Bell,
  CheckCircle2,
  AlertCircle,
  Clock,
  Phone,
  Mail,
  ShieldCheck,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { apiClient } from "@/lib/api";
import type { UserProfileDetailResponse } from "@shared/types";

export default function ProfilePage() {
  const router = useRouter();
  const { user, token, isLoading, updateUser } = useAuth();

  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");
  const [loading, setLoading] = useState<boolean>(true);
  const [profileData, setProfileData] = useState<UserProfileDetailResponse | null>(null);

  // Profile Form state
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [profileMessage, setProfileMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password Form state
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    if (!token) {
      if (!isLoading) setLoading(false);
      return;
    }

    async function fetchProfile() {
      setLoading(true);
      try {
        const data = await apiClient.getMyProfile();
        setProfileData(data);
        setFullName(data.full_name || "");
        setPhone(data.phone || data.phone_number || "");
        setAvatarUrl(data.avatar_url || "");
      } catch (err) {
        console.error("Failed to load profile", err);
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, [token, isLoading]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);
    setIsUpdatingProfile(true);

    try {
      const updated = await apiClient.updateMyProfile({
        full_name: fullName.trim(),
        phone: phone.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      });

      setProfileMessage({ type: "success", text: "Cập nhật thông tin tài khoản thành công!" });
      updateUser(updated);
      if (profileData) {
        setProfileData({
          ...profileData,
          full_name: updated.full_name,
          phone: updated.phone || updated.phone_number,
          avatar_url: updated.avatar_url,
        });
      }
    } catch (err: any) {
      setProfileMessage({
        type: "error",
        text: err.message || "Không thể cập nhật thông tin. Vui lòng thử lại.",
      });
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    if (newPassword.length < 8) {
      setPasswordMessage({
        type: "error",
        text: "Mật khẩu mới phải có độ dài tối thiểu 8 ký tự.",
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordMessage({
        type: "error",
        text: "Mật khẩu xác nhận không khớp với mật khẩu mới.",
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await apiClient.changeMyPassword({
        old_password: oldPassword,
        new_password: newPassword,
      });

      setPasswordMessage({
        type: "success",
        text: res.message || "Đổi mật khẩu thành công!",
      });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordMessage({
        type: "error",
        text: err.message || "Đổi mật khẩu không thành công. Vui lòng kiểm tra lại mật khẩu cũ.",
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <ShieldAlert className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <h2 className="text-xl font-bold text-slate-900">Vui lòng đăng nhập</h2>
          <p className="mt-2 text-sm text-slate-600">
            Bạn cần đăng nhập để truy cập và quản lý thông tin tài khoản Space247.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/login"
              className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition"
            >
              Đăng nhập ngay
            </Link>
            <Link
              href="/"
              className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Về trang chủ
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const roleBadge = (role: string) => {
    switch (role) {
      case "superadmin":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-200">
            <ShieldAlert className="h-3.5 w-3.5 text-purple-600" />
            Superadmin (Quản trị tối cao)
          </span>
        );
      case "admin":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
            <ShieldCheck className="h-3.5 w-3.5 text-indigo-600" />
            Quản trị viên (Admin)
          </span>
        );
      case "agent":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <Building2 className="h-3.5 w-3.5 text-blue-600" />
            Môi giới chuyên nghiệp (Agent)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <UserIcon className="h-3.5 w-3.5 text-emerald-600" />
            Khách hàng (User)
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/60 pb-16 pt-6">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Hồ sơ & Thiết lập Tài khoản
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Quản lý thông tin định danh cá nhân, vai trò hệ thống và bảo mật tài khoản Space247
            </p>
          </div>
          {profileData?.role === "superadmin" && (
            <Link
              href="/admin/users"
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-purple-700 transition"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>Trang Quản lý Người dùng (RBAC)</span>
            </Link>
          )}
        </div>

        {/* Overview Stats Cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link
            href={user?.role === "user" ? "/properties" : "/properties/my"}
            className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-blue-500 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tin đăng sở hữu</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition">
                <Building2 className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900">
                {profileData ? profileData.total_properties : "..."}
              </span>
              <span className="ml-1.5 text-xs text-slate-400">bất động sản</span>
            </div>
          </Link>

          <Link
            href="/favorites"
            className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-rose-500 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Bất động sản đã lưu</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-50 text-rose-600 group-hover:bg-rose-600 group-hover:text-white transition">
                <Heart className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900">
                {profileData ? profileData.total_favorites : "..."}
              </span>
              <span className="ml-1.5 text-xs text-slate-400">tin quan tâm</span>
            </div>
          </Link>

          <Link
            href="/profile/alerts"
            className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-amber-500 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Cảnh báo tìm kiếm</span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition">
                <Bell className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-slate-900">
                {profileData ? profileData.total_alerts : "..."}
              </span>
              <span className="ml-1.5 text-xs text-slate-400">tiêu chí đăng ký</span>
            </div>
          </Link>
        </div>

        {/* Main Content Card */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
          {/* Tabs Navigation */}
          <div className="flex border-b border-slate-200 bg-slate-50/50 px-6">
            <button
              onClick={() => setActiveTab("profile")}
              className={`flex items-center gap-2 border-b-2 py-4 text-sm font-semibold transition cursor-pointer ${
                activeTab === "profile"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <UserIcon className="h-4 w-4" />
              <span>Thông tin cá nhân</span>
            </button>

            <button
              onClick={() => setActiveTab("security")}
              className={`ml-8 flex items-center gap-2 border-b-2 py-4 text-sm font-semibold transition cursor-pointer ${
                activeTab === "security"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <KeyRound className="h-4 w-4" />
              <span>Bảo mật & Đổi mật khẩu</span>
            </button>
          </div>

          <div className="p-6 sm:p-8">
            {activeTab === "profile" && (
              <div>
                {profileMessage && (
                  <div
                    className={`mb-6 flex items-center gap-2.5 rounded-xl p-4 text-sm ${
                      profileMessage.type === "success"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "bg-rose-50 text-rose-800 border border-rose-200"
                    }`}
                  >
                    {profileMessage.type === "success" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                    )}
                    <span>{profileMessage.text}</span>
                  </div>
                )}

                {/* Account Badges Bar */}
                <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-4 border border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-500">Vai trò tài khoản:</span>
                    {profileData && roleBadge(profileData.role)}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      Đăng ký: {profileData?.created_at ? new Date(profileData.created_at).toLocaleDateString("vi-VN") : "..."}
                    </span>
                    {profileData?.last_login_at && (
                      <span className="flex items-center gap-1 border-l border-slate-200 pl-3">
                        Đăng nhập gần nhất: {new Date(profileData.last_login_at).toLocaleString("vi-VN")}
                      </span>
                    )}
                  </div>
                </div>

                <form onSubmit={handleUpdateProfile} className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Họ và tên
                      </label>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Nguyễn Văn A"
                        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Địa chỉ Email (Định danh đăng nhập)
                      </label>
                      <div className="relative">
                        <input
                          type="email"
                          disabled
                          value={profileData?.email || ""}
                          className="w-full rounded-xl border border-slate-200 bg-slate-100 px-4 py-2.5 text-sm text-slate-500 cursor-not-allowed"
                        />
                        <Mail className="absolute right-3.5 top-3 h-4 w-4 text-slate-400" />
                      </div>
                      <p className="mt-1 text-[11px] text-slate-400">
                        Email được dùng làm tên đăng nhập cố định của tài khoản.
                      </p>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Số điện thoại liên hệ
                        </label>
                        {profileData?.phone_verified ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" /> Đã xác thực
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                            <AlertCircle className="h-3 w-3" /> Chưa xác thực
                          </span>
                        )}
                      </div>
                      <div className="relative">
                        <input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="0912345678"
                          className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        />
                        <Phone className="absolute right-3.5 top-3 h-4 w-4 text-slate-400" />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Đường dẫn Ảnh đại diện (Avatar URL)
                      </label>
                      <input
                        type="url"
                        value={avatarUrl}
                        onChange={(e) => setAvatarUrl(e.target.value)}
                        placeholder="https://images.unsplash.com/photo-..."
                        className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end pt-4 border-t border-slate-100">
                    <button
                      type="submit"
                      disabled={isUpdatingProfile}
                      className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition disabled:opacity-50 cursor-pointer"
                    >
                      {isUpdatingProfile ? "Đang lưu..." : "Lưu thay đổi"}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {activeTab === "security" && (
              <div>
                {passwordMessage && (
                  <div
                    className={`mb-6 flex items-center gap-2.5 rounded-xl p-4 text-sm ${
                      passwordMessage.type === "success"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "bg-rose-50 text-rose-800 border border-rose-200"
                    }`}
                  >
                    {passwordMessage.type === "success" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                    )}
                    <span>{passwordMessage.text}</span>
                  </div>
                )}

                <form onSubmit={handleChangePassword} className="max-w-xl space-y-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Mật khẩu hiện tại
                    </label>
                    <input
                      type="password"
                      required
                      value={oldPassword}
                      onChange={(e) => setOldPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Mật khẩu mới (tối thiểu 8 ký tự)
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Xác nhận mật khẩu mới
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div className="pt-3">
                    <button
                      type="submit"
                      disabled={isChangingPassword}
                      className="rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition disabled:opacity-50 cursor-pointer"
                    >
                      {isChangingPassword ? "Đang xử lý..." : "Cập nhật mật khẩu"}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
