import type { PropertyResponse, RentalType } from "@shared/types";
import { Bath, Clock, DoorOpen, Fingerprint, Layers, PawPrint, WashingMachine, Building2 } from "lucide-react";
export const rentalLabels: Record<RentalType, string> = { room: "Phòng trọ", serviced_apartment: "Căn hộ dịch vụ", house_share: "Ở ghép", entire_house: "Nhà nguyên căn" };
export const ruleLabels = { curfew: "Có giờ đóng cửa", private_bathroom: "Phòng tắm riêng", allow_pets: "Cho nuôi thú cưng", has_mezzanine: "Có gác lửng", has_washing_machine: "Máy giặt", live_with_owner: "Ở cùng chủ", has_elevator: "Thang máy", fingerprint_lock: "Khóa vân tay" };
export const costLabels = { electricity_per_kwh: "Điện (đ/kWh)", water_cost: "Nước", parking_fee_monthly: "Gửi xe (đ/tháng)", service_fee_monthly: "Dịch vụ (đ/tháng)", deposit_months: "Đặt cọc (tháng)" };
export function RentalBadges({ property }: { property: PropertyResponse }) {
  if (property.listing_type !== "rent") return null;
  return <div className="flex flex-wrap gap-2 text-xs text-blue-800">{property.rental_type && <span>{rentalLabels[property.rental_type]}</span>}{property.rental_rules?.has_mezzanine === true && <span>• Có gác lửng</span>}{property.rental_rules?.allow_pets === true && <span>• Cho nuôi thú cưng</span>}</div>;
}
export default function RentalDetails({ property }: { property: PropertyResponse }) {
  if (property.listing_type !== "rent") return null;
  const c = property.rental_costs;
  const r = property.rental_rules;
  const unknown = "Chưa cung cấp";
  const icons = { curfew: Clock, private_bathroom: Bath, allow_pets: PawPrint, has_mezzanine: Layers, has_washing_machine: WashingMachine, live_with_owner: DoorOpen, has_elevator: Building2, fingerprint_lock: Fingerprint };
  return <div className="space-y-5"><section className="rounded-2xl border bg-white p-6 space-y-4"><h2 className="text-xl font-bold">Biểu phí sinh hoạt & Đặt cọc</h2><RentalBadges property={property} /><p>Giá thuê: {property.price.toLocaleString("vi-VN")} đ/tháng</p><dl className="grid gap-3 sm:grid-cols-2">{Object.entries(costLabels).map(([key, label]) => {
    const value = c?.[key as keyof typeof costLabels];
    const waterUnit = c?.water_unit === "per_person" ? "đ/người/tháng" : c?.water_unit === "per_m3" ? "đ/m³" : "(chưa rõ đơn vị)";
    return <div key={key}><dt className="text-slate-500">{label}{key === "water_cost" ? ` (${waterUnit})` : ""}</dt><dd>{value == null ? unknown : value.toLocaleString("vi-VN")}</dd></div>;
  })}<div><dt>Tiền đặt cọc</dt><dd>{c?.deposit_months == null ? unknown : `${(property.price * c.deposit_months).toLocaleString("vi-VN")} đ`}</dd></div><div><dt>Cách tính điện</dt><dd>{c?.electricity_billing === "state_rate" ? "Giá nhà nước" : c?.electricity_billing === "fixed" ? "Đơn giá cố định" : unknown}</dd></div></dl><p className="text-sm text-slate-500">Điện, nước phụ thuộc lượng sử dụng hoặc số người; chưa thể cộng vào tổng chi phí tháng. Mục chưa cung cấp không có nghĩa là miễn phí.</p></section><section className="rounded-2xl border bg-white p-6 space-y-4"><h2 className="text-xl font-bold">Quy định & Tiện nghi phòng trọ</h2><dl className="grid gap-4 sm:grid-cols-2">{Object.entries(ruleLabels).map(([key, label]) => {
    const value = r?.[key as keyof typeof ruleLabels];
    const Icon = icons[key as keyof typeof icons];
    return <div key={key}><dt className="flex items-center gap-2 text-slate-500"><Icon size={18} aria-hidden="true" />{label}</dt><dd>{value == null ? unknown : key === "curfew" && !value ? "Giờ giấc tự do" : key === "live_with_owner" && !value ? "Không chung chủ" : value ? "Có" : "Không"}</dd></div>;
  })}{r?.curfew !== false && <div><dt>Giờ đóng cửa</dt><dd>{r?.curfew_time ?? unknown}</dd></div>}<div><dt>Số người tối đa</dt><dd>{r?.max_occupants ?? unknown}</dd></div></dl></section></div>;
}
