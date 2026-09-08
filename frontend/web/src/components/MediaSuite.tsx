"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Images, Play, Box, X, MapPin } from "lucide-react";
import { getVideoEmbedInfo, getVirtualTourEmbed } from "@shared/media";
import { getPlaceholderImage } from "@/lib/utils";

type Props = { images?: string[]; videoUrl?: string | null; virtualTourUrl?: string | null; title: string; propertyType?: string; latitude?: number | null; longitude?: number | null };

export default function MediaSuite({ images, videoUrl, virtualTourUrl, title, propertyType = "apartment", latitude, longitude }: Props) {
  const [tab, setTab] = useState<"photos" | "video" | "tour" | "map">("photos");
  const [selected, setSelected] = useState<number | null>(null);
  const photos = images?.filter(Boolean).length ? images.filter(Boolean) : [getPlaceholderImage(propertyType, 0)];
  const video = getVideoEmbedInfo(videoUrl);
  const tour = getVirtualTourEmbed(virtualTourUrl);
  const map = latitude != null && longitude != null ? `https://www.openstreetmap.org/export/embed.html?bbox=${longitude - 0.005}%2C${latitude - 0.005}%2C${longitude + 0.005}%2C${latitude + 0.005}&layer=mapnik&marker=${latitude}%2C${longitude}` : null;
  const tabs = [{ id: "photos", label: `Ảnh thực tế (${photos.length})`, icon: Images }, ...(video ? [{ id: "video", label: "Video Review", icon: Play }] : []), ...(tour ? [{ id: "tour", label: "Tour 360°", icon: Box }] : []), ...(map ? [{ id: "map", label: "Vị trí bản đồ", icon: MapPin }] : [])] as const;
  const embed = tab === "video" ? video?.embedUrl : tab === "tour" ? tour : tab === "map" ? map : null;
  return <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xs">
    <div className="flex gap-1 border-b border-slate-100 p-2">{tabs.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setTab(id as typeof tab)} className={`inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold ${tab === id ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}><Icon className="h-4 w-4" />{label}</button>)}</div>
    {embed ? <div className="mx-auto max-w-4xl bg-slate-950 p-3"><iframe loading="lazy" title={`${title} ${tab}`} src={embed} className="mx-auto w-full max-w-2xl rounded-xl" style={{ aspectRatio: tab === "video" ? video?.aspectRatio : "16 / 9" }} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen /></div> : <div className="relative grid h-[280px] grid-cols-2 grid-rows-2 gap-1 sm:h-[430px] sm:grid-cols-5">{Array.from({ length: Math.min(5, photos.length === 1 ? 1 : 5) }, (_, index) => photos[index % photos.length]).map((image, index) => <button type="button" key={`${image}-${index}`} onClick={() => setSelected(index % photos.length)} className={`overflow-hidden ${index === 0 ? "col-span-2 row-span-2 sm:col-span-3" : ""}`}><img src={image} alt={`${title} - ảnh ${(index % photos.length) + 1}`} onError={(event) => { event.currentTarget.src = getPlaceholderImage(propertyType, 0); }} className="h-full w-full object-cover transition hover:scale-105" /></button>)}<button type="button" onClick={() => setSelected(0)} className="absolute bottom-4 right-4 rounded-xl bg-white/95 px-4 py-2 text-xs font-bold text-slate-900 shadow">Xem tất cả ảnh ({photos.length})</button></div>}
    {selected !== null && <div role="dialog" aria-modal="true" aria-label="Bộ sưu tập ảnh" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/95 p-4"><button type="button" aria-label="Đóng" onClick={() => setSelected(null)} className="absolute right-5 top-5 rounded-full bg-white/10 p-3 text-white"><X /></button><button type="button" aria-label="Ảnh trước" onClick={() => setSelected((selected + photos.length - 1) % photos.length)} className="absolute left-5 rounded-full bg-white/10 p-3 text-white"><ChevronLeft /></button><button type="button" aria-label="Ảnh tiếp theo" onClick={() => setSelected((selected + 1) % photos.length)} className="absolute right-5 rounded-full bg-white/10 p-3 text-white"><ChevronRight /></button><div className="max-h-full max-w-6xl"><img src={photos[selected]} alt={`${title} - ảnh ${selected + 1}`} className="max-h-[78vh] max-w-full rounded-xl object-contain" /><div className="mt-3 flex gap-2 overflow-x-auto">{photos.map((image, index) => <button type="button" key={`${image}-${index}`} onClick={() => setSelected(index)} className={`h-14 w-20 shrink-0 overflow-hidden rounded-lg border-2 ${selected === index ? "border-white" : "border-transparent opacity-60"}`}><img src={image} alt="" className="h-full w-full object-cover" /></button>)}</div></div></div>}
  </section>;
}
