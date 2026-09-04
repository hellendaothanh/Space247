"use client";

import dynamic from "next/dynamic";
import { PropertyResponse, SearchResultItem } from "@shared/types";
import { Loader2 } from "lucide-react";

const PropertyMapClient = dynamic(() => import("./PropertyMapClient"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[650px] w-full flex-col items-center justify-center rounded-3xl border border-slate-200 bg-slate-100 text-slate-400">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-2" />
      <span className="text-sm font-medium">Đang tải bản đồ tương tác Space247...</span>
    </div>
  ),
});

interface PropertyMapProps {
  items: (SearchResultItem | PropertyResponse)[];
  selectedId?: string | null;
  onSelectProperty?: (id: string) => void;
}

export default function PropertyMap(props: PropertyMapProps) {
  return <PropertyMapClient {...props} />;
}
