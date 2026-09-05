"use client";

import { useState } from "react";
import {
  FileEdit,
  X,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  Copy,
  Check,
  Layers,
  Loader2,
  Image as ImageIcon,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { apiClient } from "@/lib/api";
import { GenerateListingResponse, ExtractedSpecs } from "@shared/types";

interface AiListingGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialPropertyType?: string;
  onApply: (data: {
    title: string;
    description: string;
    specs: ExtractedSpecs;
  }) => void;
}

export default function AiListingGeneratorModal({
  isOpen,
  onClose,
  initialPropertyType = "apartment",
  onApply,
}: AiListingGeneratorModalProps) {
  const [propertyType, setPropertyType] = useState(initialPropertyType);
  const [notes, setNotes] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [imageFileName, setImageFileName] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateListingResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"markdown" | "specs">("markdown");
  const [isCopied, setIsCopied] = useState(false);

  if (!isOpen) return null;

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Vui lòng chọn tệp hình ảnh hợp lệ (PNG, JPG, WEBP).");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("Dung lượng ảnh không được vượt quá 8MB.");
      return;
    }

    setImageFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      setImageBase64(reader.result as string);
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    if (!notes.trim() && !imageBase64) {
      setError("Vui lòng nhập ít nhất vài gạch đầu dòng ghi chú hoặc tải lên ảnh sổ đỏ/mặt bằng.");
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      const bulletList = notes
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);

      const resp = await apiClient.generateAgentListing({
        text_prompts: bulletList.length > 0 ? bulletList : [notes],
        image_base64: imageBase64,
        property_type: propertyType,
        target_audience: targetAudience.trim() || undefined,
      });

      setResult(resp);
    } catch (err: any) {
      setError(err.message || "Không thể tạo bài đăng bằng AI. Vui lòng thử lại.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplyToForm = () => {
    if (!result) return;
    onApply({
      title: result.title_seo,
      description: result.description_markdown,
      specs: result.extracted_specs,
    });
    onClose();
  };

  const handleCopyMarkdown = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.description_markdown);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-3 sm:p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[92vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600 text-white rounded-xl shadow-md shadow-blue-500/20">
              <FileEdit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg sm:text-xl font-bold text-slate-900">
                  Hỗ Trợ Soạn Thảo Tin Đăng
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full">
                  Tiện ích thông minh
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Tự động chuẩn hóa tiêu đề, nội dung và trích xuất thông số từ ghi chú hoặc ảnh pháp lý
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200/60 rounded-full text-slate-400 hover:text-slate-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Inputs */}
            <div className="lg:col-span-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Loại hình BĐS
                </label>
                <select
                  value={propertyType}
                  onChange={(e) => setPropertyType(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="apartment">Căn hộ chung cư</option>
                  <option value="house">Nhà riêng / Nhà phố</option>
                  <option value="villa">Biệt thự cao cấp</option>
                  <option value="land">Đất nền dự án / Thổ cư</option>
                  <option value="commercial">Mặt bằng thương mại</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Ghi chú nhanh từ môi giới (Bullet notes)
                </label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder={`Ví dụ:\n- Căn góc 3PN 95m2 D'Capitale\n- Tầng 18 view hồ điều hòa cực đẹp\n- Đầy đủ nội thất nhập khẩu cao cấp\n- Sổ hồng chính chủ, cần bán gấp 6.8 tỷ`}
                  className="w-full px-3 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none font-sans"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Khách hàng mục tiêu (Tùy chọn)
                </label>
                <input
                  type="text"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  placeholder="VD: Gia đình trẻ, Chuyên gia nước ngoài, Nhà đầu tư dòng tiền"
                  className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Ảnh sổ đỏ / Mặt bằng phân lô (AI Vision OCR)
                </label>
                <div className="relative border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-xl p-3 bg-slate-50 hover:bg-blue-50/30 transition text-center cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />
                  <div className="flex flex-col items-center justify-center py-1">
                    <Upload className="w-5 h-5 text-slate-400 mb-1" />
                    <span className="text-xs font-medium text-slate-600">
                      {imageFileName ? (
                        <span className="text-blue-600 font-semibold truncate max-w-[200px] inline-block">
                          {imageFileName}
                        </span>
                      ) : (
                        "Tải ảnh sổ đỏ, bản vẽ hoặc hiện trạng (PNG, JPG)"
                      )}
                    </span>
                  </div>
                </div>
                {imageBase64 && (
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                    <span className="flex items-center gap-1 text-emerald-600 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Đã nạp ảnh thành công
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setImageBase64(null);
                        setImageFileName(null);
                      }}
                      className="text-red-500 hover:underline"
                    >
                      Gỡ ảnh
                    </button>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 transition disabled:opacity-50 cursor-pointer"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Đang xử lý & soạn thảo tin...</span>
                  </>
                ) : (
                  <>
                    <FileEdit className="w-4 h-4" />
                    <span>Tự động soạn bài đăng</span>
                  </>
                )}
              </button>
            </div>

            {/* Right Column: AI Output Preview */}
            <div className="lg:col-span-7 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col min-h-[380px] overflow-hidden">
              {result ? (
                <>
                  <div className="p-3 bg-white border-b border-slate-200 flex items-center justify-between">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setActiveTab("markdown")}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                          activeTab === "markdown"
                            ? "bg-blue-100 text-blue-700"
                            : "text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        Bài viết Markdown
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveTab("specs")}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                          activeTab === "specs"
                            ? "bg-blue-100 text-blue-700"
                            : "text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        Thông số trích xuất
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={handleCopyMarkdown}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-blue-600 px-2.5 py-1 rounded hover:bg-slate-100 transition"
                      title="Sao chép bài viết"
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-600 font-medium">Đã sao chép</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Sao chép</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="flex-1 p-4 overflow-y-auto bg-white text-slate-800 text-sm">
                    {activeTab === "markdown" ? (
                      <div className="space-y-4">
                        <div className="p-3 bg-blue-50/70 border border-blue-100 rounded-xl">
                          <span className="text-xs font-bold text-blue-800 uppercase tracking-wider block mb-1">
                            Tiêu đề SEO đề xuất:
                          </span>
                          <p className="font-semibold text-slate-900 text-sm">
                            {result.title_seo}
                          </p>
                        </div>
                        <div className="prose prose-sm max-w-none text-slate-700">
                          <ReactMarkdown>{result.description_markdown}</ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold text-slate-500 uppercase">
                          Thông số kỹ thuật AI tự trích xuất:
                        </h4>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-slate-500 block">Diện tích</span>
                            <span className="font-bold text-slate-800">
                              {result.extracted_specs.area_sqm
                                ? `${result.extracted_specs.area_sqm} m²`
                                : "Chưa xác định"}
                            </span>
                          </div>
                          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-slate-500 block">Phòng ngủ / WC</span>
                            <span className="font-bold text-slate-800">
                              {result.extracted_specs.num_bedrooms ?? "-"} PN /{" "}
                              {result.extracted_specs.num_bathrooms ?? "-"} WC
                            </span>
                          </div>
                          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-slate-500 block">Hướng nhà</span>
                            <span className="font-bold text-slate-800">
                              {result.extracted_specs.orientation || "Chưa xác định"}
                            </span>
                          </div>
                          <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                            <span className="text-slate-500 block">Pháp lý</span>
                            <span className="font-bold text-slate-800">
                              {result.extracted_specs.legal_status || "Chưa xác định"}
                            </span>
                          </div>
                          {result.extracted_specs.frontage_meters && (
                            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                              <span className="text-slate-500 block">Mặt tiền</span>
                              <span className="font-bold text-slate-800">
                                {result.extracted_specs.frontage_meters} m
                              </span>
                            </div>
                          )}
                          {result.extracted_specs.suggested_price && (
                            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                              <span className="text-slate-500 block">Giá gợi ý</span>
                              <span className="font-bold text-slate-800">
                                {result.extracted_specs.suggested_price.toLocaleString("vi-VN")} đ
                              </span>
                            </div>
                          )}
                        </div>

                        {result.extracted_specs.amenities.length > 0 && (
                          <div className="mt-3">
                            <span className="text-slate-500 text-xs block mb-1.5">
                              Tiện ích phát hiện:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {result.extracted_specs.amenities.map((a, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md text-xs font-medium"
                                >
                                  ✓ {a}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400">
                  <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                    <FileEdit className="w-6 h-6" />
                  </div>
                  <h4 className="font-semibold text-slate-700 mb-1">
                    Bản xem trước nội dung tin đăng
                  </h4>
                  <p className="text-xs max-w-sm text-slate-500">
                    Nhập ghi chú nhanh hoặc đính kèm tài liệu pháp lý bên trái và chọn &ldquo;Tự động soạn bài đăng&rdquo; để hoàn tất thông tin.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Dữ liệu sẽ được tự động điền vào tiêu đề, mô tả và các trường thông số của form đăng tin.
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200/60 rounded-xl transition"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleApplyToForm}
              disabled={!result}
              className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-xl shadow-md shadow-blue-500/20 transition flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Áp dụng vào Form</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
