import Link from "next/link";
import { Building2, MapPin, ArrowUpRight, Home, KeyRound, TrendingUp } from "lucide-react";
import { ProjectResponse } from "@shared/types";
import { formatPrice, formatProjectStatus } from "@/lib/utils";

interface ProjectCardProps {
  project: ProjectResponse;
  index?: number;
}

const DEFAULT_PROJECT_IMAGES = [
  "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1000&q=80",
  "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=80",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
];

export default function ProjectCard({ project, index = 0 }: ProjectCardProps) {
  const statusInfo = formatProjectStatus(project.status);
  const imageUrl =
    project.images && project.images.length > 0
      ? project.images[0]
      : DEFAULT_PROJECT_IMAGES[index % DEFAULT_PROJECT_IMAGES.length];

  const formatPriceRange = () => {
    if (project.price_range_min && project.price_range_max) {
      return `${formatPrice(project.price_range_min)} - ${formatPrice(project.price_range_max)}`;
    }
    if (project.price_range_min) {
      return `Từ ${formatPrice(project.price_range_min)}`;
    }
    if (project.price_range_max) {
      return `Đến ${formatPrice(project.price_range_max)}`;
    }
    return "Đang cập nhật";
  };

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
      {/* Image Container */}
      <div className="relative aspect-16/10 w-full overflow-hidden bg-slate-100">
        <img
          src={imageUrl}
          alt={project.name}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />

        {/* Status Tag */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5">
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold shadow-xs backdrop-blur-md ${statusInfo.color}`}>
            {statusInfo.label}
          </span>
          {project.developer && (
            <span className="rounded-full bg-slate-900/75 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-md">
              {project.developer}
            </span>
          )}
        </div>

        {/* Price Range Badge */}
        <div className="absolute bottom-3 left-3 rounded-lg bg-slate-950/80 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-md shadow-xs">
          {formatPriceRange()}
        </div>
      </div>

      {/* Content Container */}
      <div className="flex flex-1 flex-col p-5">
        <div className="mb-2">
          <h3 className="line-clamp-1 text-lg font-bold text-slate-900 transition-colors group-hover:text-blue-600">
            {project.name}
          </h3>
          <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
            <MapPin className="h-3.5 w-3.5 shrink-0 text-slate-400" />
            <span className="line-clamp-1">
              {[project.ward, project.district, project.city].filter(Boolean).join(", ")}
            </span>
          </div>
        </div>

        {/* Metadata Badges */}
        <div className="my-3 grid grid-cols-2 gap-2 border-y border-slate-100 py-3 text-xs text-slate-600">
          <div className="flex items-center gap-1.5">
            <Building2 className="h-3.5 w-3.5 text-blue-600 shrink-0" />
            <span>{project.total_units ? `${project.total_units.toLocaleString()} căn` : "Đang cập nhật"}</span>
          </div>
          {project.average_price_per_sqm ? (
            <div className="flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
              <span>~ {(project.average_price_per_sqm / 1_000_000).toFixed(1)} tr/m²</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Home className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{project.active_properties_count} tin đăng</span>
            </div>
          )}
        </div>

        {/* Active Units Breakdown */}
        <div className="flex items-center justify-between text-xs text-slate-500 mb-4">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 font-medium text-slate-700">
              <Home className="h-3.5 w-3.5 text-blue-600" />
              {project.for_sale_count} bán
            </span>
            <span className="flex items-center gap-1 font-medium text-slate-700">
              <KeyRound className="h-3.5 w-3.5 text-emerald-600" />
              {project.for_rent_count} thuê
            </span>
          </div>
          {project.handover_year && (
            <span className="text-[11px] text-slate-400">
              BG: {project.handover_year}
            </span>
          )}
        </div>

        {/* Link Button */}
        <div className="mt-auto pt-1">
          <Link
            href={`/projects/${project.slug}`}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl bg-slate-50 py-2.5 text-xs font-semibold text-slate-800 transition-colors group-hover:bg-blue-600 group-hover:text-white"
          >
            <span>Khám phá dự án & bảng hàng</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
