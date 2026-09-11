import type { Metadata } from "next";
import Link from "next/link";
import {
  Calculator,
  Landmark,
  ShieldCheck,
  TrendingUp,
  Percent,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  Sparkles,
  Building,
  PiggyBank,
  Info,
} from "lucide-react";
import MortgageCalculator from "@/components/MortgageCalculator";

export const metadata: Metadata = {
  title: "Bảng Tính Lãi Suất Vay Mua Nhà & Lịch Trả Nợ Chi Tiết | Space247",
  description:
    "Công cụ tính lãi vay mua nhà trả góp ngân hàng thông minh 2026. Hỗ trợ phương thức dư nợ giảm dần và niên kim cố định, so sánh bảng lãi suất tham khảo 15+ ngân hàng.",
};

interface BankRate {
  name: string;
  code: string;
  preferentialRate: string;
  period: string;
  postRate: string;
  maxLoanPercent: string;
  maxTerm: string;
  badge?: string;
}

const BANK_RATES: BankRate[] = [
  {
    name: "Ngân hàng Ngoại Thương (Vietcombank)",
    code: "VCB",
    preferentialRate: "6.0%",
    period: "12 tháng đầu",
    postRate: "9.5%",
    maxLoanPercent: "70%",
    maxTerm: "30 năm",
    badge: "Lãi suất tốt nhất",
  },
  {
    name: "Ngân hàng Đầu tư & Phát triển (BIDV)",
    code: "BIDV",
    preferentialRate: "6.2%",
    period: "12 tháng đầu",
    postRate: "9.6%",
    maxLoanPercent: "80%",
    maxTerm: "30 năm",
    badge: "Duyệt nhanh",
  },
  {
    name: "Ngân hàng Công Thương (VietinBank)",
    code: "CTG",
    preferentialRate: "6.4%",
    period: "12 tháng đầu",
    postRate: "9.8%",
    maxLoanPercent: "80%",
    maxTerm: "35 năm",
    badge: "Kỳ hạn dài",
  },
  {
    name: "Ngân hàng Kỹ Thương (Techcombank)",
    code: "TCB",
    preferentialRate: "6.8%",
    period: "12 tháng đầu",
    postRate: "10.2%",
    maxLoanPercent: "85%",
    maxTerm: "35 năm",
    badge: "Thủ tục số hóa",
  },
  {
    name: "Ngân hàng Quân Đội (MBBank)",
    code: "MBB",
    preferentialRate: "6.5%",
    period: "12 tháng đầu",
    postRate: "10.0%",
    maxLoanPercent: "80%",
    maxTerm: "30 năm",
  },
  {
    name: "Ngân hàng Shinhan Việt Nam (Shinhan Bank)",
    code: "SHB",
    preferentialRate: "5.9%",
    period: "12 tháng đầu",
    postRate: "9.2%",
    maxLoanPercent: "70%",
    maxTerm: "30 năm",
    badge: "Khối Ngoại ưu đãi",
  },
  {
    name: "Ngân hàng Á Châu (ACB)",
    code: "ACB",
    preferentialRate: "6.5%",
    period: "12 tháng đầu",
    postRate: "9.9%",
    maxLoanPercent: "75%",
    maxTerm: "25 năm",
  },
  {
    name: "Ngân hàng Việt Nam Thịnh Vượng (VPBank)",
    code: "VPB",
    preferentialRate: "6.9%",
    period: "12 tháng đầu",
    postRate: "10.5%",
    maxLoanPercent: "85%",
    maxTerm: "35 năm",
    badge: "Tối đa 85% giá trị",
  },
];

export default function MortgageToolPage() {
  return (
    <div className="min-h-screen bg-slate-50/60 pb-20 dark:bg-slate-950">
      {/* Header & Breadcrumb */}
      <div className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <nav className="mb-4 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <Link href="/" className="hover:text-blue-600 transition">
              Trang chủ
            </Link>
            <span>/</span>
            <span className="text-slate-700 dark:text-slate-300 font-medium">Công cụ tài chính</span>
            <span>/</span>
            <span className="font-semibold text-blue-600">Bảng tính lãi vay</span>
          </nav>

          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/40 dark:text-blue-300">
                <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                <span>Công cụ tài chính bất động sản số Space247</span>
              </div>
              <h1 className="mt-2 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl lg:text-4xl dark:text-white">
                Bảng Tính Lãi Suất Vay Mua Nhà
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                Dự toán chi tiết số tiền gốc & lãi phải trả hàng tháng, so sánh phương thức trả nợ dư nợ giảm dần và niên kim cố định, đồng thời cập nhật lãi suất từ các ngân hàng uy tín hàng đầu.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-2 md:pt-0">
              <Link
                href="/?listing_type=sale"
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-xs transition hover:bg-blue-700 active:scale-95"
              >
                <Building className="h-4 w-4" />
                <span>Tìm BĐS phù hợp</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-10">
        {/* Core Interactive Calculator Component */}
        <section>
          <MortgageCalculator
            propertyPrice={3_500_000_000}
            propertyTitle="Căn hộ / Bất động sản mua bán tiêu chuẩn"
            currency="VND"
          />
        </section>

        {/* Bank Rates Reference Table */}
        <section className="rounded-3xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-xs dark:bg-emerald-950/40 dark:text-emerald-400">
                <Landmark className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  Lãi Suất Vay Mua Nhà Các Ngân Hàng (T9/2026)
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Tổng hợp gói vay mua nhà thương mại và căn hộ dự án từ các ngân hàng đối tác liên kết
                </p>
              </div>
            </div>

            <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl self-start sm:self-auto">
              <Info className="h-3.5 w-3.5 text-blue-600" />
              Cập nhật định kỳ 24/7
            </span>
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs dark:divide-slate-800">
              <thead className="bg-slate-50 text-slate-700 font-semibold dark:bg-slate-800/60 dark:text-slate-300">
                <tr>
                  <th className="px-4 py-3 text-left">Ngân hàng</th>
                  <th className="px-4 py-3 text-right">Lãi suất ưu đãi</th>
                  <th className="px-4 py-3 text-left">Thời hạn ưu đãi</th>
                  <th className="px-4 py-3 text-right">Lãi thả nổi sau ưu đãi</th>
                  <th className="px-4 py-3 text-right">Hạn mức vay</th>
                  <th className="px-4 py-3 text-right">Thời hạn tối đa</th>
                  <th className="px-4 py-3 text-center">Đặc điểm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white font-medium text-slate-600 dark:divide-slate-800/60 dark:bg-slate-900 dark:text-slate-400">
                {BANK_RATES.map((bank) => (
                  <tr key={bank.code} className="hover:bg-blue-50/40 dark:hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-extrabold text-blue-600">
                          {bank.code}
                        </span>
                        <span>{bank.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-extrabold text-emerald-600 dark:text-emerald-400 text-sm">
                      {bank.preferentialRate}
                    </td>
                    <td className="px-4 py-3 text-left">{bank.period}</td>
                    <td className="px-4 py-3 text-right font-semibold text-amber-600 dark:text-amber-400">
                      {bank.postRate}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-slate-800 dark:text-slate-200">
                      {bank.maxLoanPercent}
                    </td>
                    <td className="px-4 py-3 text-right">{bank.maxTerm}</td>
                    <td className="px-4 py-3 text-center">
                      {bank.badge ? (
                        <span className="inline-block rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                          {bank.badge}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-[11px] leading-relaxed text-slate-400 dark:text-slate-500 italic">
            * Lưu ý: Lãi suất trên là mức tham khảo trung bình trên thị trường tại thời điểm hiện tại. Lãi suất thực tế và điều kiện cho vay cụ thể phụ thuộc vào xếp hạng tín nhiệm của từng khách hàng và gói sản phẩm tài trợ của ngân hàng đối tác.
          </p>
        </section>

        {/* Educational Guide: Mortgage Planning & Tips */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400 mb-4">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              1. Nguyên Tắc An Toàn Tài Chính
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Tổng số tiền trả nợ ngân hàng (cả gốc và lãi) hàng tháng <strong className="text-slate-700 dark:text-slate-300">không nên vượt quá 40% - 50%</strong> tổng thu nhập ổn định của gia đình, đảm bảo ngân sách sinh hoạt và quỹ dự phòng rủi ro luôn an toàn.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400 mb-4">
              <TrendingUp className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              2. Lựa Chọn Phương Thức Trả Nợ
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              <strong className="text-slate-700 dark:text-slate-300">Dư nợ giảm dần:</strong> Tiết kiệm tổng tiền lãi cả kỳ tốt nhất vì tiền gốc giảm sau mỗi tháng. <br />
              <strong className="text-slate-700 dark:text-slate-300">Niên kim cố định:</strong> Số tiền trả đều mỗi tháng, phù hợp người trẻ có mức thu nhập tăng trưởng theo thời gian.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400 mb-4">
              <AlertCircle className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              3. Phí Trả Nợ Trước Hạn
            </h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              Hầu hết các ngân hàng áp dụng phí trả trước hạn từ <strong className="text-slate-700 dark:text-slate-300">1% - 3%</strong> trên dư nợ tất toán trong 3 - 5 năm đầu và miễn phí sau năm thứ 5. Hãy tính toán lộ trình tích lũy để trả nợ đúng thời điểm tối ưu chi phí.
            </p>
          </div>
        </section>

        {/* Bottom CTA Banner */}
        <section className="rounded-3xl bg-linear-to-r from-blue-600 to-indigo-700 p-8 text-white shadow-lg flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-xl font-bold">Bạn Đã Tính Toán Xong Ngân Sách?</h3>
            <p className="mt-1 text-xs text-blue-100 max-w-xl">
              Khám phá ngay hàng ngàn bất động sản đã được thẩm định pháp lý và hỗ trợ gói vay ưu đãi từ ngân hàng trên nền tảng Space247.
            </p>
          </div>
          <Link
            href="/?listing_type=sale"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-xs font-bold text-blue-700 shadow-md transition hover:bg-blue-50 active:scale-95 shrink-0"
          >
            <span>Khám phá nhà đất mở bán</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </main>
    </div>
  );
}
