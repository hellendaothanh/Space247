"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  DollarSign,
  ShieldCheck,
  Plus,
  Trash2,
  Layers,
  Sparkles,
} from "lucide-react";
import type {
  RentalPropertyCreate,
  RentalPropertyModel,
  RentalUnitCreate,
} from "@shared/types";
import { apiClient } from "@/lib/api";

export default function NewRentalPropertyWizardPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Step 1: General Info
  const [name, setName] = useState("");
  const [propertyModel, setPropertyModel] = useState<RentalPropertyModel>("boarding_house");
  const [address, setAddress] = useState("");
  const [ward, setWard] = useState("");
  const [district, setDistrict] = useState("");
  const [city, setCity] = useState("Hà Nội");
  const [description, setDescription] = useState("");

  // Step 2: Shared Costs & Rules
  const [electricityPerKwh, setElectricityPerKwh] = useState<number>(3500);
  const [electricityBilling, setElectricityBilling] = useState<"fixed" | "state_rate">("fixed");
  const [waterCost, setWaterCost] = useState<number>(30000);
  const [waterUnit, setWaterUnit] = useState<"per_m3" | "per_person">("per_m3");
  const [wifiFee, setWifiFee] = useState<number>(50000);
  const [parkingFee, setParkingFee] = useState<number>(100000);

  const [curfew, setCurfew] = useState(false);
  const [allowPets, setAllowPets] = useState(true);
  const [fingerprintLock, setFingerprintLock] = useState(true);
  const [liveWithOwner, setLiveWithOwner] = useState(false);

  // Step 3: Initial Rooms / Units
  const [units, setUnits] = useState<RentalUnitCreate[]>([
    {
      unit_number: "P.101",
      floor: 1,
      area_sqm: 25,
      price: 3500000,
      deposit: 3500000,
      status: "available",
      furnishing: "basic",
      has_mezzanine: true,
      has_private_bathroom: true,
      max_occupants: 2,
    },
  ]);

  const addEmptyUnit = () => {
    const nextNum = units.length + 1;
    setUnits([
      ...units,
      {
        unit_number: `P.10${nextNum}`,
        floor: 1,
        area_sqm: 22,
        price: 3000000,
        deposit: 3000000,
        status: "available",
        furnishing: "basic",
        has_mezzanine: false,
        has_private_bathroom: true,
        max_occupants: 2,
      },
    ]);
  };

  const removeUnit = (index: number) => {
    setUnits(units.filter((_, i) => i !== index));
  };

  const handleFinishWizard = async () => {
    setSubmitting(true);
    setError("");
    try {
      const payload: RentalPropertyCreate = {
        name,
        property_model: propertyModel,
        address,
        ward: ward || undefined,
        district: district || undefined,
        city,
        description,
        shared_costs: {
          electricity_per_kwh: electricityPerKwh,
          electricity_billing: electricityBilling,
          water_cost: waterCost,
          water_unit: waterUnit,
          wifi_fee: wifiFee,
          parking_fee_monthly: parkingFee,
        },
        shared_rules: {
          curfew,
          allow_pets: allowPets,
          fingerprint_lock: fingerprintLock,
          live_with_owner: liveWithOwner,
        },
        initial_units: units,
      };

      await apiClient.createRentalProperty(payload);
      router.push("/host/rentals");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi khi đăng ký khu trọ");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/host/rentals"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" /> Quay lại kênh chủ nhà
        </Link>
        <span className="text-xs font-semibold text-slate-400">Bước {step} / 3</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Đăng ký khu trọ / Tòa nhà mới</h1>
        <p className="text-slate-500 text-sm mt-1">
          Quy trình đa bước trực quan giúp thiết lập biểu phí và tạo danh sách phòng nhanh chóng
        </p>
      </div>

      {/* Wizard Progress Bar */}
      <div className="grid grid-cols-3 gap-2">
        <div className={`h-2 rounded-full ${step >= 1 ? "bg-blue-600" : "bg-slate-200"}`} />
        <div className={`h-2 rounded-full ${step >= 2 ? "bg-blue-600" : "bg-slate-200"}`} />
        <div className={`h-2 rounded-full ${step >= 3 ? "bg-blue-600" : "bg-slate-200"}`} />
      </div>

      {error && (
        <div className="rounded-2xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: General Info */}
      {step === 1 && (
        <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <h2 className="text-lg font-bold text-slate-900">Bước 1: Thông tin cơ bản tòa nhà</h2>

          <div className="space-y-4 text-sm">
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Tên khu trọ / Tòa nhà *</label>
              <input
                type="text"
                required
                placeholder="VD: Nhà Trọ Xanh Bách Khoa, Tòa Căn Hộ Dịch Vụ Cầu Giấy..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-slate-200 p-3"
              />
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-700">Mô hình cho thuê *</label>
              <select
                value={propertyModel}
                onChange={(e) => setPropertyModel(e.target.value as RentalPropertyModel)}
                className="w-full rounded-xl border border-slate-200 p-3 bg-white"
              >
                <option value="boarding_house">Nhà trọ / Phòng trọ sinh viên, người đi làm</option>
                <option value="serviced_apartment">Căn hộ dịch vụ (Studio / 1-2PN full tiện nghi)</option>
                <option value="homestay">Homestay (Thuê ngắn hạn theo ngày)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-700">Địa chỉ cụ thể *</label>
              <input
                type="text"
                required
                placeholder="Số 123 Đường ABC..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full rounded-xl border border-slate-200 p-3"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Tỉnh/Thành phố *</label>
                <input
                  type="text"
                  required
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-3"
                />
              </div>
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Quận/Huyện</label>
                <input
                  type="text"
                  placeholder="Hai Bà Trưng..."
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-3"
                />
              </div>
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Phường/Xã</label>
                <input
                  type="text"
                  placeholder="Bách Khoa..."
                  value={ward}
                  onChange={(e) => setWard(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-3"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-700">Mô tả tổng thể</label>
              <textarea
                rows={3}
                placeholder="Mô tả tiện ích xung quanh, an ninh, giao thông..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-xl border border-slate-200 p-3"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              type="button"
              disabled={!name || !address}
              onClick={() => setStep(2)}
              className="rounded-xl bg-blue-600 px-6 py-3 font-bold text-white shadow-xs hover:bg-blue-700 disabled:opacity-50"
            >
              Tiếp tục: Biểu phí & Nội quy
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Fees & Rules */}
      {step === 2 && (
        <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <h2 className="text-lg font-bold text-slate-900">Bước 2: Biểu phí chung & Nội quy tòa nhà</h2>

          <div className="space-y-6 text-sm">
            {/* Fees */}
            <div className="space-y-3">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-xs">Biểu phí sinh hoạt</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-slate-600">Đơn giá điện (đ/kWh)</label>
                  <input
                    type="number"
                    value={electricityPerKwh}
                    onChange={(e) => setElectricityPerKwh(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-200 p-2.5"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-600">Đơn giá nước</label>
                  <input
                    type="number"
                    value={waterCost}
                    onChange={(e) => setWaterCost(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-200 p-2.5"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-600">Phí gửi xe (đ/tháng)</label>
                  <input
                    type="number"
                    value={parkingFee}
                    onChange={(e) => setParkingFee(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-200 p-2.5"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-600">Wifi / mạng (đ/tháng)</label>
                  <input
                    type="number"
                    value={wifiFee}
                    onChange={(e) => setWifiFee(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-200 p-2.5"
                  />
                </div>
              </div>
            </div>

            {/* Rules */}
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h3 className="font-bold text-slate-800 uppercase tracking-wider text-xs">Nội quy tòa nhà</h3>
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!curfew}
                    onChange={(e) => setCurfew(!e.target.checked)}
                    className="rounded text-blue-600 h-4 w-4"
                  />
                  <span>Giờ giấc tự do (Không giới nghiêm)</span>
                </label>

                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowPets}
                    onChange={(e) => setAllowPets(e.target.checked)}
                    className="rounded text-blue-600 h-4 w-4"
                  />
                  <span>Cho phép nuôi thú cưng</span>
                </label>

                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={fingerprintLock}
                    onChange={(e) => setFingerprintLock(e.target.checked)}
                    className="rounded text-blue-600 h-4 w-4"
                  />
                  <span>Cửa cổng khóa vân tay</span>
                </label>

                <label className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!liveWithOwner}
                    onChange={(e) => setLiveWithOwner(!e.target.checked)}
                    className="rounded text-blue-600 h-4 w-4"
                  />
                  <span>Không chung chủ</span>
                </label>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-between">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-600 hover:bg-slate-50"
            >
              Quay lại
            </button>
            <button
              type="button"
              onClick={() => setStep(3)}
              className="rounded-xl bg-blue-600 px-6 py-3 font-bold text-white shadow-xs hover:bg-blue-700"
            >
              Tiếp tục: Thêm danh sách phòng
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Units Setup */}
      {step === 3 && (
        <div className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Bước 3: Danh sách phòng ban đầu</h2>
            <button
              type="button"
              onClick={addEmptyUnit}
              className="inline-flex items-center gap-1.5 rounded-xl bg-blue-50 px-3.5 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100"
            >
              <Plus className="h-4 w-4" /> Thêm phòng
            </button>
          </div>

          <div className="space-y-4">
            {units.map((unit, idx) => (
              <div key={idx} className="rounded-2xl border border-slate-200 p-4 space-y-3 bg-slate-50/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-700 uppercase">Phòng #{idx + 1}</span>
                  {units.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeUnit(idx)}
                      className="text-slate-400 hover:text-red-600"
                      title="Xóa phòng"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <label className="text-slate-600 block mb-1">Mã/Số phòng *</label>
                    <input
                      type="text"
                      value={unit.unit_number}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].unit_number = e.target.value;
                        setUnits(next);
                      }}
                      className="w-full rounded-xl border border-slate-200 p-2 bg-white"
                    />
                  </div>

                  <div>
                    <label className="text-slate-600 block mb-1">Diện tích (m²) *</label>
                    <input
                      type="number"
                      value={unit.area_sqm}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].area_sqm = Number(e.target.value);
                        setUnits(next);
                      }}
                      className="w-full rounded-xl border border-slate-200 p-2 bg-white"
                    />
                  </div>

                  <div>
                    <label className="text-slate-600 block mb-1">Giá thuê (VND) *</label>
                    <input
                      type="number"
                      value={unit.price}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].price = Number(e.target.value);
                        setUnits(next);
                      }}
                      className="w-full rounded-xl border border-slate-200 p-2 bg-white font-bold"
                    />
                  </div>

                  <div>
                    <label className="text-slate-600 block mb-1">Nội thất</label>
                    <select
                      value={unit.furnishing}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].furnishing = e.target.value as any;
                        setUnits(next);
                      }}
                      className="w-full rounded-xl border border-slate-200 p-2 bg-white"
                    >
                      <option value="empty">Phòng trống</option>
                      <option value="basic">Cơ bản</option>
                      <option value="full">Full nội thất</option>
                    </select>
                  </div>
                </div>

                <div className="flex gap-4 text-xs">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={unit.has_mezzanine}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].has_mezzanine = e.target.checked;
                        setUnits(next);
                      }}
                      className="rounded text-blue-600 h-3.5 w-3.5"
                    />
                    <span>Có gác lửng</span>
                  </label>

                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={unit.has_private_bathroom}
                      onChange={(e) => {
                        const next = [...units];
                        next[idx].has_private_bathroom = e.target.checked;
                        setUnits(next);
                      }}
                      className="rounded text-blue-600 h-3.5 w-3.5"
                    />
                    <span>Vệ sinh khép kín</span>
                  </label>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-between">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-600 hover:bg-slate-50"
            >
              Quay lại
            </button>
            <button
              type="button"
              disabled={submitting || units.length === 0}
              onClick={handleFinishWizard}
              className="rounded-xl bg-emerald-600 px-7 py-3 font-bold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50 inline-flex items-center gap-2"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{submitting ? "Đang tạo khu trọ..." : "Hoàn tất & Đăng ký"}</span>
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
