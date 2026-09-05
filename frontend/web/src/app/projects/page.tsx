"use client";

import { useEffect, useState, useCallback } from "react";
import { Building2, Search, Filter, Loader2, X, AlertCircle, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api";
import { ProjectResponse, ProjectStatus } from "@shared/types";
import ProjectCard from "@/components/project/ProjectCard";

const CITIES = ["Tất cả tỉnh thành", "Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Bình Dương", "Đồng Nai"];

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "Tất cả trạng thái" },
  { value: "upcoming", label: "Sắp mở bán" },
  { value: "under_construction", label: "Đang thi công" },
  { value: "handing_over", label: "Đang bàn giao" },
  { value: "completed", label: "Đã bàn giao" },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(9);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [selectedCity, setSelectedCity] = useState("Tất cả tỉnh thành");
  const [selectedStatus, setSelectedStatus] = useState("all");

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const res = await apiClient.getProjects({
        skip,
        limit: pageSize,
        city: selectedCity !== "Tất cả tỉnh thành" ? selectedCity : undefined,
        status: selectedStatus !== "all" ? (selectedStatus as ProjectStatus) : undefined,
        q: searchKeyword.trim() ? searchKeyword.trim() : undefined,
      });
      setProjects(res.items);
      setTotal(res.total);
    } catch (err: any) {
      console.error("Failed to load projects:", err);
      setError(err?.message || "Không thể kết nối đến máy chủ Space247 API.");
      setProjects([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, selectedCity, selectedStatus, searchKeyword]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProjects();
  };

  const clearFilters = () => {
    setSearchKeyword("");
    setSelectedCity("Tất cả tỉnh thành");
    setSelectedStatus("all");
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="min-h-screen bg-slate-50/50 pb-20">
      {/* Hero Header */}
      <div className="border-b border-slate-200/80 bg-white pt-10 pb-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                <Building2 className="h-3.5 w-3.5" />
                <span>Danh mục Đại đô thị & Dự án quy hoạch</span>
              </div>
              <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                Khám phá Dự án Bất động sản
              </h1>
              <p className="mt-2 text-sm text-slate-600 max-w-2xl">
                Tìm kiếm thông tin chính xác về quy mô, chủ đầu tư, mặt bằng tổng thể (master plan),
                tiện ích nội khu và tổng hợp bảng hàng chuyển nhượng - cho thuê thực tế.
              </p>
            </div>
            <div className="text-sm font-medium text-slate-500">
              Tổng cộng: <span className="font-bold text-blue-600">{total}</span> dự án
            </div>
          </div>

          {/* Search & Filter Bar */}
          <form
            onSubmit={handleSearchSubmit}
            className="mt-8 grid grid-cols-1 gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-12 md:items-center"
          >
            {/* Keyword Input */}
            <div className="relative md:col-span-5">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="Tên dự án, chủ đầu tư (Vinhomes, Masterise...)"
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2.5 pl-10 pr-4 text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>

            {/* City Selector */}
            <div className="md:col-span-3">
              <select
                value={selectedCity}
                onChange={(e) => {
                  setSelectedCity(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2.5 px-3 text-xs font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none"
              >
                {CITIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Selector */}
            <div className="md:col-span-3">
              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2.5 px-3 text-xs font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none"
              >
                {STATUS_OPTIONS.map((st) => (
                  <option key={st.value} value={st.value}>
                    {st.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 md:col-span-1">
              <button
                type="submit"
                className="flex w-full items-center justify-center rounded-xl bg-blue-600 py-2.5 px-3 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition"
                title="Lọc dự án"
              >
                <Filter className="h-3.5 w-3.5" />
              </button>
              {(searchKeyword || selectedCity !== "Tất cả tỉnh thành" || selectedStatus !== "all") && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-slate-100 text-slate-500 hover:bg-slate-200 transition"
                  title="Xóa bộ lọc"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8">
        {error ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-red-200 bg-red-50/60 p-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500" />
            <h3 className="mt-4 text-base font-bold text-red-900">Không thể kết nối máy chủ Space247</h3>
            <p className="mt-2 max-w-md text-xs text-red-700 leading-relaxed">{error}</p>
            <button
              onClick={() => fetchProjects()}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-700 transition cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Thử kết nối lại
            </button>
          </div>
        ) : loading ? (
          <div className="flex h-80 w-full flex-col items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="mt-3 text-xs font-medium text-slate-500">Đang tải danh sách dự án...</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <Building2 className="h-12 w-12 text-slate-300" />
            <h3 className="mt-4 text-base font-bold text-slate-900">Không tìm thấy dự án phù hợp</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-sm">
              Thử tìm kiếm với từ khóa khác hoặc xóa bỏ các tiêu chí lọc địa bàn, trạng thái.
            </p>
            <button
              onClick={clearFilters}
              className="mt-5 inline-flex items-center gap-1.5 rounded-xl bg-blue-50 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition"
            >
              Xóa bộ lọc tìm kiếm
            </button>
          </div>
        ) : (
          <>
            {/* Project Cards Grid */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {projects.map((project, idx) => (
                <ProjectCard key={project.id} project={project} index={idx} />
              ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-10 flex items-center justify-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:pointer-events-none transition"
                >
                  Trang trước
                </button>
                <div className="px-3 text-xs font-medium text-slate-600">
                  Trang <span className="font-bold text-slate-900">{page}</span> / {totalPages}
                </div>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:pointer-events-none transition"
                >
                  Trang sau
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
