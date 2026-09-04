"use client";

import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

const PropertyDetailMapClient = dynamic(
  () => import("./PropertyDetailMapClient"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[380px] w-full flex-col items-center justify-center rounded-2xl border border-slate-200 bg-slate-100 text-slate-400">
        <Loader2 className="h-7 w-7 animate-spin text-blue-600 mb-2" />
        <span className="text-xs font-medium">Đang tải bản đồ tọa độ bất động sản...</span>
      </div>
    ),
  }
);

interface PropertyDetailMapProps {
  latitude: number;
  longitude: number;
  title: string;
  address?: string;
  price?: number;
  currency?: string;
  propertyType?: string;
}

export default function PropertyDetailMap(props: PropertyDetailMapProps) {
  return <PropertyDetailMapClient {...props} />;
}
