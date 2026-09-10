"use client";

import { useEffect, useRef, useState } from "react";
import { BedDouble, ChevronRight, CircleGauge, MapPin, Refrigerator, ShieldCheck, Snowflake, Users, X } from "lucide-react";
import type { MonthlyCostEstimate, RentalProperty, RentalUnit } from "@shared/types";
import { apiClient } from "@/lib/api";
import MediaSuite from "@/components/common/MediaSuite";

const amenityLabels: Record<string, string> = { ac_inverter: "Điều hòa Inverter", fridge: "Tủ lạnh", water_heater: "Nóng lạnh", bed_mattress: "Giường nệm", study_desk: "Bàn học", wardrobe: "Tủ quần áo", balcony: "Ban công", washing_machine: "Máy giặt", kitchen: "Bếp" };
const format = (amount: number) => `${amount.toLocaleString("vi-VN")} đ`;

export function RentalExperience({ property, onBook }: { property: RentalProperty; onBook: (unit: RentalUnit) => void }) {
  const [unit, setUnit] = useState<RentalUnit | null>(property.units.find((item) => item.status === "available") ?? property.units[0] ?? null);
  const [detail, setDetail] = useState<RentalUnit | null>(null);
  const [occupants, setOccupants] = useState(1);
  const [hasAc, setHasAc] = useState(true);
  const [hasFridge, setHasFridge] = useState(true);
  const [estimate, setEstimate] = useState<MonthlyCostEstimate | null>(null);
  const [error, setError] = useState("");
  const request = useRef(0);

  useEffect(() => { setOccupants(1); }, [unit?.id]);
  useEffect(() => {
    if (!unit) return;
    const current = ++request.current;
    setError("");
    apiClient.calculateRentalLivingCost(unit.id, { property_id: property.id, occupants, has_ac: hasAc, has_fridge: hasFridge })
      .then((value) => { if (current === request.current) setEstimate(value); })
      .catch((cause) => { if (current === request.current) { setEstimate(null); setError(cause instanceof Error ? cause.message : "Không thể tính chi phí"); } });
  }, [property.id, unit?.id, occupants, hasAc, hasFridge]);

  const galleryImages = [...property.images, ...property.units.flatMap((item) => item.images)].filter(Boolean);
  const maxOccupants = Math.min(3, Math.max(1, unit?.max_occupants ?? 3));
  return <>
    <MediaSuite images={galleryImages} videoUrl={property.video_url} title={property.name} propertyType="apartment" latitude={property.latitude} longitude={property.longitude} />
    <section className="grid gap-6 lg:grid-cols-[1.2fr_.8fr]">
      <div className="space-y-4">
        <div><h2 className="text-xl font-extrabold text-slate-900">Phòng đang cho thuê</h2><p className="text-sm text-slate-500">Chọn phòng để xem ảnh thật, bố trí và chi phí riêng.</p></div>
        <div className="grid gap-4 sm:grid-cols-2">{property.units.map((item) => <article key={item.id} className={`overflow-hidden rounded-2xl border bg-white ${item.status === "available" ? "border-slate-200" : "opacity-60"}`}>
          {item.images[0] && <img src={item.images[0]} alt={`Phòng ${item.unit_number}`} className="h-36 w-full object-cover" />}
          <div className="space-y-3 p-4"><div className="flex justify-between"><b>{item.unit_number}</b><span className="text-xs">{item.status === "available" ? "Còn trống" : item.status === "occupied" ? "Đã thuê" : "Đang giữ"}</span></div><p className="font-bold text-blue-600">{format(item.price)}/tháng</p><div className="flex flex-wrap gap-1">{item.room_amenities.slice(0, 3).map((value) => <span className="rounded bg-slate-100 px-2 py-1 text-xs" key={value}>{amenityLabels[value] ?? value}</span>)}<span className="rounded bg-slate-100 px-2 py-1 text-xs"><Users className="mr-1 inline h-3 w-3" />Tối đa {item.max_occupants ?? "?"}</span></div><div className="flex gap-2"><button type="button" onClick={() => setDetail(item)} className="text-xs font-bold text-slate-700">Xem phòng <ChevronRight className="inline h-3 w-3" /></button>{item.status === "available" && <button type="button" onClick={() => { setUnit(item); onBook(item); }} className="ml-auto rounded-lg bg-blue-600 px-3 py-2 text-xs font-bold text-white">Đặt lịch</button>}</div></div>
        </article>)}</div>
      </div>
      {unit && <aside className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center gap-2"><CircleGauge className="text-blue-600" /><h2 className="font-extrabold">Dự tính chi phí hàng tháng</h2></div><label className="text-sm font-medium">Phòng</label><select value={unit.id} onChange={(event) => setUnit(property.units.find((item) => item.id === event.target.value) ?? unit)} className="mt-1 w-full rounded-lg border p-2">{property.units.filter((item) => item.status === "available").map((item) => <option value={item.id} key={item.id}>{item.unit_number} · {format(item.price)}</option>)}</select><label className="mt-4 block text-sm font-medium">Số người ở</label><div className="mt-2 flex gap-2">{Array.from({ length: maxOccupants }, (_, index) => index + 1).map((value) => <button key={value} type="button" onClick={() => setOccupants(value)} className={`rounded-lg px-4 py-2 text-sm font-bold ${occupants === value ? "bg-blue-600 text-white" : "bg-slate-100"}`}>{value}</button>)}</div><div className="mt-4 space-y-2 text-sm"><label className="flex items-center gap-2"><input checked={hasAc} onChange={(event) => setHasAc(event.target.checked)} type="checkbox" /><Snowflake className="h-4 w-4" />Có dùng máy lạnh</label><label className="flex items-center gap-2"><input checked={hasFridge} onChange={(event) => setHasFridge(event.target.checked)} type="checkbox" /><Refrigerator className="h-4 w-4" />Có dùng tủ lạnh</label></div>{error ? <p className="mt-4 text-sm text-red-600">{error}</p> : estimate ? <div className="mt-5 space-y-2 border-t pt-4 text-sm">{[...estimate.fixed_costs, ...estimate.variable_costs].map((line) => <div key={line.key} className="flex justify-between gap-3"><span>{line.label}</span><b>{format(line.amount)}</b></div>)}<div className="mt-3 border-t pt-3 text-base font-extrabold text-blue-700">TỔNG DỰ TÍNH / THÁNG <span className="float-right">{format(estimate.estimated_total_monthly)}</span></div><div className="font-bold text-slate-700">BÌNH QUÂN / NGƯỜI <span className="float-right">{format(estimate.per_person_monthly)}</span></div><p className="text-xs text-slate-500">Điện ước tính theo thiết bị và nước theo biểu phí đã công bố.</p></div> : <p className="mt-4 text-sm text-slate-500">Đang tính chi phí...</p>}</aside>}
    </section>
    {(property.surroundings.length > 0 || property.security_features.length > 0) && <section className="grid gap-5 md:grid-cols-2"><div className="rounded-2xl border bg-white p-5"><h2 className="mb-4 font-extrabold">Tiện ích & môi trường xung quanh</h2><div className="space-y-3">{property.surroundings.map((place) => <div key={place.label} className="flex gap-3 rounded-xl bg-slate-50 p-3"><MapPin className="h-5 w-5 text-blue-600" /><div><b className="text-sm">{place.label}</b><p className="text-xs text-slate-600">{place.distance_meters ? `${place.distance_meters}m` : ""}{place.walk_minutes ? ` · ${place.walk_minutes} phút đi bộ` : ""}{place.note ? ` · ${place.note}` : ""}</p></div></div>)}</div></div><div className="rounded-2xl border bg-white p-5"><h2 className="mb-4 font-extrabold">An ninh & PCCC</h2><div className="space-y-3">{property.security_features.map((feature) => <div key={feature} className="flex gap-3 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-900"><ShieldCheck className="h-5 w-5 shrink-0" />{feature}</div>)}</div></div></section>}
    {detail && <div role="dialog" aria-modal="true" aria-label={`Chi tiết phòng ${detail.unit_number}`} className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4"><div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-5"><button onClick={() => setDetail(null)} type="button" className="float-right"><X /></button><h2 className="text-xl font-extrabold">Phòng {detail.unit_number}</h2><div className="mt-4 grid gap-3 sm:grid-cols-2">{detail.images.map((image, index) => <img key={image} src={image} alt={`Phòng ${detail.unit_number} góc ${index + 1}`} className="h-48 w-full rounded-xl object-cover" />)}</div>{detail.floor_plan_url && <a href={detail.floor_plan_url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-blue-600"><BedDouble className="h-4 w-4" />Xem sơ đồ bố trí phòng</a>}<div className="mt-4 flex flex-wrap gap-2">{detail.room_amenities.map((value) => <span key={value} className="rounded-full bg-slate-100 px-3 py-1 text-sm">{amenityLabels[value] ?? value}</span>)}</div></div></div>}
  </>;
}
