"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
  Building2,
  Search,
  Plus,
  Edit2,
  UserX,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  X,
  RotateCcw,
  Clock,
  Phone,
  Lock,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { apiClient } from "@/lib/api";
import type {
  UserResponse,
  UserRole,
  UserCreateByAdminRequest,
  UserUpdateByAdminRequest,
} from "@shared/types";

export default function AdminUsersPage() {
  const router = useRouter();
  const { user, token, isLoading } = useAuth();

  const [users, setUsers] = useState<UserResponse[]>([]);
  const [totalUsers, setTotalUsers] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(15);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [searchInput, setSearchInput] = useState<string>("");
  const [activeSearch, setActiveSearch] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);

  // Form states
  const [addForm, setAddForm] = useState<UserCreateByAdminRequest>({
    email: "",
    password: "",
    full_name: "",
    phone: "",
    avatar_url: "",
    role: "user",
    is_active: true,
    phone_verified: false,
  });

  const [editForm, setEditForm] = useState<UserUpdateByAdminRequest>({
    full_name: "",
    phone: "",
    avatar_url: "",
    role: "user",
    is_active: true,
    phone_verified: false,
    reset_password: "",
  });

  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchUsers = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const activeParam =
        statusFilter === "active" ? true : statusFilter === "inactive" ? false : undefined;

      const res = await apiClient.getAdminUsers({
        q: activeSearch.trim() || undefined,
        role: roleFilter || undefined,
        is_active: activeParam,
        page,
        page_size: pageSize,
      });

      setUsers(res.items);
      setTotalUsers(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      console.error("Lỗi khi tải danh sách người dùng:", err);
      setFeedback({
        type: "error",
        text: err.message || "Không thể tải danh sách người dùng.",
      });
    } finally {
      setLoading(false);
    }
  }, [token, activeSearch, roleFilter, statusFilter, page, pageSize]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveSearch(searchInput);
    setPage(1);
  };

  const handleResetFilters = () => {
    setSearchInput("");
    setActiveSearch("");
    setRoleFilter("");
    setStatusFilter("");
    setPage(1);
  };

  const handleOpenAddModal = () => {
    setAddForm({
      email: "",
      password: "",
      full_name: "",
      phone: "",
      avatar_url: "",
      role: "user",
      is_active: true,
      phone_verified: false,
    });
    setModalError(null);
    setFeedback(null);
    setIsAddModalOpen(true);
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setModalError(null);
    try {
      await apiClient.createAdminUser({
        ...addForm,
        email: addForm.email.trim(),
        full_name: addForm.full_name.trim(),
        phone: addForm.phone?.trim() || null,
        avatar_url: addForm.avatar_url?.trim() || null,
      });

      setFeedback({ type: "success", text: "Thêm người dùng mới thành công!" });
      setIsAddModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      setModalError(err.message || "Tạo người dùng thất bại.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenEditModal = (u: UserResponse) => {
    setSelectedUser(u);
    setEditForm({
      full_name: u.full_name,
      phone: u.phone || u.phone_number || "",
      avatar_url: u.avatar_url || "",
      role: u.role,
      is_active: u.is_active,
      phone_verified: u.phone_verified,
      reset_password: "",
    });
    setModalError(null);
    setFeedback(null);
    setIsEditModalOpen(true);
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setSubmitting(true);
    setModalError(null);
    try {
      const payload: UserUpdateByAdminRequest = {
        full_name: editForm.full_name?.trim(),
        phone: editForm.phone?.trim() || null,
        avatar_url: editForm.avatar_url?.trim() || null,
        role: editForm.role,
        is_active: editForm.is_active,
        phone_verified: editForm.phone_verified,
      };
      if (editForm.reset_password && editForm.reset_password.trim().length >= 6) {
        payload.reset_password = editForm.reset_password.trim();
      }

      await apiClient.updateAdminUser(selectedUser.id, payload);
      setFeedback({ type: "success", text: `Đã cập nhật tài khoản ${selectedUser.email} thành công!` });
      setIsEditModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      setModalError(err.message || "Cập nhật người dùng thất bại.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActiveStatus = async (targetUser: UserResponse) => {
    if (user?.id === targetUser.id) {
      setFeedback({
        type: "error",
        text: "Bạn không thể tự khóa/mở khóa tài khoản của chính mình.",
      });
      return;
    }

    const nextState = !targetUser.is_active;
    const confirmMsg = nextState
      ? `Bạn có chắc chắn muốn kích hoạt lại tài khoản ${targetUser.email}?`
      : `Bạn có chắc chắn muốn khóa tài khoản ${targetUser.email}? Người dùng này sẽ không thể đăng nhập.`;

    if (!window.confirm(confirmMsg)) return;

    try {
      await apiClient.updateAdminUser(targetUser.id, { is_active: nextState });
      setFeedback({
        type: "success",
        text: `Đã ${nextState ? "kích hoạt" : "vô hiệu hóa"} tài khoản ${targetUser.email}.`,
      });
      fetchUsers();
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Thao tác thất bại." });
    }
  };

  // Guard: Loading State
  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Guard: Unauthorized or Non-Superadmin
  if (!token) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <ShieldAlert className="mx-auto h-12 w-12 text-rose-600 mb-4" />
          <h2 className="text-xl font-bold text-slate-900">Yêu cầu đăng nhập</h2>
          <p className="mt-2 text-sm text-slate-600">
            Vui lòng đăng nhập với tài khoản Superadmin để truy cập khu vực quản trị.
          </p>
          <div className="mt-6">
            <Link
              href="/login"
              className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition"
            >
              Đăng nhập ngay
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (user && user.role !== "superadmin") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-8 shadow-sm">
          <ShieldAlert className="mx-auto h-12 w-12 text-rose-600 mb-4" />
          <h2 className="text-xl font-bold text-rose-950">Quyền truy cập bị từ chối (403 Forbidden)</h2>
          <p className="mt-2 text-sm text-rose-700">
            Trang này chỉ dành riêng cho Quản trị viên tối cao (Superadmin). Tài khoản hiện tại ({user.email}) có vai trò <span className="font-bold uppercase">{user.role}</span>.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/profile"
              className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 transition"
            >
              Xem hồ sơ cá nhân
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

  const roleBadge = (role: UserRole | string) => {
    switch (role) {
      case "superadmin":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
            <ShieldAlert className="h-3 w-3 text-purple-600" />
            Superadmin
          </span>
        );
      case "admin":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
            <ShieldCheck className="h-3 w-3 text-indigo-600" />
            Admin
          </span>
        );
      case "agent":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <Building2 className="h-3 w-3 text-blue-600" />
            Agent
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <UserIcon className="h-3 w-3 text-emerald-600" />
            User
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/60 pb-16 pt-6">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb & Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-1">
              <Link href="/" className="hover:text-blue-600">Trang chủ</Link>
              <span>/</span>
              <span className="text-slate-900 font-semibold">Quản trị người dùng & Phân quyền RBAC</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
              <ShieldCheck className="h-7 w-7 text-purple-600" />
              <span>Quản lý Tài khoản & Phân quyền</span>
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Tổng số tài khoản: <span className="font-semibold text-slate-800">{totalUsers}</span> người dùng trong hệ thống
            </p>
          </div>

          <button
            onClick={handleOpenAddModal}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>Thêm Người dùng Mới</span>
          </button>
        </div>

        {/* Global Feedback Banner */}
        {feedback && (
          <div
            className={`mb-6 flex items-center justify-between gap-2.5 rounded-xl p-4 text-sm ${
              feedback.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}
          >
            <div className="flex items-center gap-2">
              {feedback.type === "success" ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
              )}
              <span>{feedback.text}</span>
            </div>
            <button
              onClick={() => setFeedback(null)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Search and Filters Bar */}
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-12">
            <div className="sm:col-span-5 relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Tìm kiếm theo họ tên hoặc email..."
                className="w-full rounded-xl border border-slate-200 pl-10 pr-4 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
            </div>

            <div className="sm:col-span-3">
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Tất cả vai trò</option>
                <option value="superadmin">Superadmin</option>
                <option value="admin">Quản trị viên (Admin)</option>
                <option value="agent">Môi giới (Agent)</option>
                <option value="user">Khách hàng (User)</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Tất cả trạng thái</option>
                <option value="active">Đang hoạt động</option>
                <option value="inactive">Đã vô hiệu hóa</option>
              </select>
            </div>

            <div className="sm:col-span-2 flex gap-2">
              <button
                type="submit"
                className="flex-1 rounded-xl bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition"
              >
                Lọc
              </button>
              <button
                type="button"
                onClick={handleResetFilters}
                title="Đặt lại bộ lọc"
                className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 transition"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Users Table */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Người dùng</th>
                  <th scope="col" className="px-4 py-3.5">Vai trò</th>
                  <th scope="col" className="px-4 py-3.5">Trạng thái</th>
                  <th scope="col" className="px-4 py-3.5">Số điện thoại</th>
                  <th scope="col" className="px-4 py-3.5">Đăng nhập gần nhất</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                      Đang tải danh sách người dùng...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                      Không tìm thấy người dùng nào phù hợp với bộ lọc.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/70 transition">
                      {/* Name & Email */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-blue-600 font-bold text-xs shrink-0">
                            {u.full_name ? u.full_name.charAt(0).toUpperCase() : "U"}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-slate-900 truncate flex items-center gap-1.5">
                              <span>{u.full_name}</span>
                              {user?.id === u.id && (
                                <span className="rounded bg-blue-100 px-1.5 py-0.2 text-[10px] font-bold text-blue-700">
                                  Bạn
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400 truncate">{u.email}</div>
                          </div>
                        </div>
                      </td>

                      {/* Role */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        {roleBadge(u.role)}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" /> Đang hoạt động
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                            <UserX className="h-3 w-3" /> Đã vô hiệu hóa
                          </span>
                        )}
                      </td>

                      {/* Phone & Verification */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        {u.phone || u.phone_number ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-700">{u.phone || u.phone_number}</span>
                            {u.phone_verified ? (
                              <span title="SĐT đã xác thực" className="text-emerald-600 font-bold">✓</span>
                            ) : (
                              <span title="SĐT chưa xác thực" className="text-slate-400">✕</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>

                      {/* Last Login */}
                      <td className="px-4 py-4 whitespace-nowrap text-[11px] text-slate-400">
                        {u.last_login_at
                          ? new Date(u.last_login_at).toLocaleString("vi-VN")
                          : "Chưa ghi nhận"}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleOpenEditModal(u)}
                            className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 hover:text-blue-600 transition cursor-pointer"
                            title="Chỉnh sửa thông tin / Đổi vai trò"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>

                          {user?.id !== u.id && (
                            <button
                              onClick={() => handleToggleActiveStatus(u)}
                              className={`rounded-lg p-1.5 transition cursor-pointer ${
                                u.is_active
                                  ? "text-rose-600 hover:bg-rose-50"
                                  : "text-emerald-600 hover:bg-emerald-50"
                              }`}
                              title={u.is_active ? "Khóa tài khoản" : "Kích hoạt lại"}
                            >
                              {u.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-6 py-3.5 bg-slate-50/50">
              <span className="text-xs text-slate-500">
                Trang {page} / {totalPages} ({totalUsers} người dùng)
              </span>
              <div className="flex gap-1">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-100 disabled:opacity-40 transition"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-100 disabled:opacity-40 transition"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MODAL: THÊM NGƯỜI DÙNG */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl animate-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Plus className="h-5 w-5 text-blue-600" />
                <span>Thêm tài khoản người dùng mới</span>
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4">
              {modalError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                  {modalError}
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Địa chỉ Email <span className="text-rose-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={addForm.email}
                  onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
                  placeholder="user@space247.vn"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Mật khẩu khởi tạo <span className="text-rose-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={addForm.password}
                  onChange={(e) => setAddForm({ ...addForm, password: e.target.value })}
                  placeholder="Tối thiểu 6 ký tự"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Họ và tên <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={addForm.full_name}
                    onChange={(e) => setAddForm({ ...addForm, full_name: e.target.value })}
                    placeholder="Nguyễn Văn A"
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Số điện thoại
                  </label>
                  <input
                    type="tel"
                    value={addForm.phone || ""}
                    onChange={(e) => setAddForm({ ...addForm, phone: e.target.value })}
                    placeholder="0912345678"
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Ảnh đại diện (URL)
                </label>
                <input
                  type="url"
                  value={addForm.avatar_url || ""}
                  onChange={(e) => setAddForm({ ...addForm, avatar_url: e.target.value })}
                  placeholder="https://images.unsplash.com/..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Phân quyền vai trò (Role)
                </label>
                <select
                  value={addForm.role}
                  onChange={(e) => setAddForm({ ...addForm, role: e.target.value as UserRole })}
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                >
                  <option value="user">Khách hàng thông thường (User)</option>
                  <option value="agent">Môi giới bất động sản (Agent)</option>
                  <option value="admin">Quản trị viên (Admin)</option>
                  <option value="superadmin">Superadmin (Quản trị tối cao)</option>
                </select>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 border border-slate-100">
                <span className="text-xs font-medium text-slate-700">Kích hoạt tài khoản ngay</span>
                <input
                  type="checkbox"
                  checked={addForm.is_active}
                  onChange={(e) => setAddForm({ ...addForm, is_active: e.target.checked })}
                  className="h-4 w-4 rounded text-blue-600 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-xl bg-blue-600 px-5 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                >
                  {submitting ? "Đang tạo..." : "Xác nhận tạo"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CHỈNH SỬA NGƯỜI DÙNG */}
      {isEditModalOpen && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl animate-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Edit2 className="h-5 w-5 text-purple-600" />
                <span>Cập nhật tài khoản: {selectedUser.email}</span>
              </h3>
              <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateUser} className="space-y-4">
              {modalError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                  {modalError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Họ và tên
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.full_name || ""}
                    onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Số điện thoại
                  </label>
                  <input
                    type="tel"
                    value={editForm.phone || ""}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Ảnh đại diện (URL)
                </label>
                <input
                  type="url"
                  value={editForm.avatar_url || ""}
                  onChange={(e) => setEditForm({ ...editForm, avatar_url: e.target.value })}
                  placeholder="https://images.unsplash.com/..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Vai trò phân quyền
                </label>
                <select
                  disabled={user?.id === selectedUser.id}
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value as UserRole })}
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs focus:border-blue-500 focus:outline-none disabled:bg-slate-100 disabled:cursor-not-allowed"
                >
                  <option value="user">Khách hàng (User)</option>
                  <option value="agent">Môi giới (Agent)</option>
                  <option value="admin">Quản trị viên (Admin)</option>
                  <option value="superadmin">Superadmin (Quản trị tối cao)</option>
                </select>
                {user?.id === selectedUser.id && (
                  <p className="mt-1 text-[10px] text-slate-400">
                    Không thể tự đổi vai trò của tài khoản đang đăng nhập.
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 border border-slate-100">
                  <span className="text-xs font-medium text-slate-700">Đang hoạt động</span>
                  <input
                    type="checkbox"
                    disabled={user?.id === selectedUser.id}
                    checked={editForm.is_active}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                    className="h-4 w-4 rounded text-blue-600 focus:ring-blue-500 disabled:opacity-40"
                  />
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 border border-slate-100">
                  <span className="text-xs font-medium text-slate-700">Đã xác thực SĐT</span>
                  <input
                    type="checkbox"
                    checked={editForm.phone_verified}
                    onChange={(e) => setEditForm({ ...editForm, phone_verified: e.target.checked })}
                    className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3">
                <label className="block text-xs font-bold text-amber-900 mb-1 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-amber-600" />
                  <span>Đặt lại mật khẩu mới (Tùy chọn)</span>
                </label>
                <input
                  type="password"
                  value={editForm.reset_password || ""}
                  onChange={(e) => setEditForm({ ...editForm, reset_password: e.target.value })}
                  placeholder="Để trống nếu không muốn đổi mật khẩu"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-1.5 text-xs focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-xl bg-purple-600 px-5 py-2 text-xs font-semibold text-white hover:bg-purple-700 disabled:opacity-50 cursor-pointer"
                >
                  {submitting ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
