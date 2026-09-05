"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  MessageSquareText,
  Headphones,
  Building2,
  MapPin,
  Bed,
  ExternalLink,
  ChevronRight,
  Maximize2,
  Minimize2,
  Minus,
  X,
  Send,
  RefreshCw,
  Compass,
  Home,
  CheckCircle2,
  Bell,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useComparison } from "@/lib/comparison";
import { formatPrice, formatPropertyType, getPlaceholderImage } from "@/lib/utils";
import { sanitizeUrl } from "@/utils/security";
import type { ChatMessage, PropertyResponse, ExtractedCriteria } from "@shared/types";

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  properties?: PropertyResponse[];
  criteria?: ExtractedCriteria | null;
  alertSaved?: boolean;
  suggestions?: string[];
  timestamp: Date;
}

const DEFAULT_SUGGESTIONS = [
  "Căn hộ 2 phòng ngủ dưới 3 tỷ ở Quận 1",
  "Nhà phố cho thuê Bình Thạnh giá 15 triệu",
  "Biệt thự cao cấp có hồ bơi tại TP.HCM",
  "Căn hộ chung cư giá tốt tại Hà Nội",
];

/**
 * Format markdown-like text nicely (convert **bold** to <strong>, list items to structured bullets)
 */
function FormattedMessageText({ content, isUser }: { content: string; isUser: boolean }) {
  const lines = useMemo(() => content.split("\n"), [content]);

  const renderInlineStyles = (text: string) => {
    // Match **bold**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        const cleanBold = part.slice(2, -2);
        return (
          <strong
            key={index}
            className={`font-semibold ${isUser ? "text-white" : "text-blue-900"}`}
          >
            {cleanBold}
          </strong>
        );
      }
      return <React.Fragment key={index}>{part}</React.Fragment>;
    });
  };

  return (
    <div className="space-y-1.5 leading-relaxed text-sm">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Handle bullet items (•, -, *)
        if (trimmed.startsWith("•") || trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const bulletText = trimmed.replace(/^[•\-*]\s*/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-1 py-0.5">
              <span
                className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${
                  isUser ? "bg-white/80" : "bg-blue-600"
                }`}
              />
              <span className="flex-1">{renderInlineStyles(bulletText)}</span>
            </div>
          );
        }

        return <div key={idx}>{renderInlineStyles(line)}</div>;
      })}
    </div>
  );
}

export default function ChatAssistantWidget() {
  const { selectedProperties } = useComparison();
  const hasComparisonBar = selectedProperties.length > 0;

  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Xin chào! Tôi là Chuyên viên Tư vấn của Space247.\n\nTôi có thể hỗ trợ bạn tìm kiếm và chọn lọc bất động sản phù hợp nhất:\n• Tìm căn hộ hoặc nhà phố theo khoảng giá ngân sách.\n• Lọc vị trí theo Quận/Huyện, Thành phố cụ thể.\n• Tìm kiếm theo tiện ích như có hồ bơi, ban công, đầy đủ nội thất.\n\nBạn đang quan tâm đến việc mua hay thuê bất động sản ở khu vực nào ạ?",
      suggestions: DEFAULT_SUGGESTIONS,
      timestamp: new Date(),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized, isExpanded, messages]);

  const [savingAlertId, setSavingAlertId] = useState<string | null>(null);

  const handleSaveAlert = async (msg: DisplayMessage) => {
    setSavingAlertId(msg.id);
    try {
      const criteria = msg.criteria || {};
      const title =
        criteria.raw_query ||
        `Cảnh báo tìm kiếm ${criteria.district || criteria.city || "bất động sản"}`;
      await apiClient.createAlert({
        title: title.slice(0, 250),
        criteria: criteria as Record<string, any>,
        frequency: "instant",
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === msg.id ? { ...m, alertSaved: true } : m))
      );
    } catch {
      alert("Vui lòng đăng nhập để lưu cảnh báo tìm kiếm mới!");
    } finally {
      setSavingAlertId(null);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || isLoading) return;

    if (query.includes("Lưu tìm kiếm") || query.includes("cảnh báo")) {
      const lastMsgWithCriteria = [...messages].reverse().find(
        (m) => m.role === "assistant" && (m.criteria || (m.properties && m.properties.length > 0))
      );
      if (lastMsgWithCriteria) {
        await handleSaveAlert(lastMsgWithCriteria);
        return;
      }
    }

    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const historyPayload: ChatMessage[] = [
        ...messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        {
          role: "user",
          content: query,
        },
      ];

      const response = await apiClient.chatAssistant({
        messages: historyPayload,
        limit: 4,
      });

      const assistantMsg: DisplayMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message,
        properties: response.properties,
        criteria: response.criteria,
        suggestions: response.suggestions,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error: any) {
      const errorMsg: DisplayMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content:
          "Hệ thống tư vấn hiện đang bận hoặc gặp gián đoạn kết nối. Bạn vui lòng thử lại sau ít giây nhé!",
        suggestions: DEFAULT_SUGGESTIONS,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content:
          "Lịch sử tư vấn đã được làm mới. Bạn đang quan tâm đến bất động sản mua bán hay cho thuê tại khu vực nào?",
        suggestions: DEFAULT_SUGGESTIONS,
        timestamp: new Date(),
      },
    ]);
  };

  const latestSuggestions =
    messages[messages.length - 1]?.role === "assistant" &&
    messages[messages.length - 1]?.suggestions?.length
      ? messages[messages.length - 1].suggestions!
      : DEFAULT_SUGGESTIONS;

  return (
    <div
      className={`fixed ${
        hasComparisonBar ? "bottom-20 sm:bottom-24" : "bottom-5 sm:bottom-6"
      } right-3 sm:right-6 z-50 flex flex-col items-end transition-all duration-300`}
    >
      {/* Floating Chat Modal */}
      {isOpen && (
        <div
          className={`bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden transition-all duration-300 mb-3 ${
            isMinimized
              ? "w-72 sm:w-80 h-14"
              : isExpanded
              ? "w-[95vw] sm:w-[820px] lg:w-[980px] h-[85vh] max-h-[860px]"
              : "w-[calc(100vw-1.5rem)] sm:w-[440px] h-[540px] sm:h-[600px] max-h-[calc(100vh-8rem)]"
          }`}
        >
          {/* Header */}
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between shadow-sm select-none border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="relative flex items-center justify-center w-9 h-9 rounded-full bg-blue-600/30 border border-blue-500/40">
                <Headphones className="w-5 h-5 text-blue-400" />
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-slate-900"></span>
              </div>
              <div>
                <h3 className="font-semibold text-sm leading-tight text-white flex items-center gap-1.5">
                  Tư vấn viên Space247
                </h3>
                <p className="text-xs text-slate-400 font-medium">Hỗ trợ tìm kiếm bđs 24/7</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {!isMinimized && (
                <>
                  <button
                    type="button"
                    onClick={handleClearHistory}
                    title="Xoá lịch sử hội thoại"
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>

                  {/* Expand / Restore Window Toggle */}
                  <button
                    type="button"
                    onClick={() => setIsExpanded(!isExpanded)}
                    title={isExpanded ? "Thu về kích thước chuẩn" : "Mở rộng toàn màn hình"}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  >
                    {isExpanded ? (
                      <Minimize2 className="w-4 h-4" />
                    ) : (
                      <Maximize2 className="w-4 h-4" />
                    )}
                  </button>
                </>
              )}

              {/* Minimize down to bottom bar */}
              <button
                type="button"
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? "Mở lại cửa sổ" : "Thu nhỏ thanh chat"}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <Minus className="w-4 h-4" />
              </button>

              {/* Close chat completely */}
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  setIsMinimized(false);
                  setIsExpanded(false);
                }}
                title="Đóng chat"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Body Content when not Minimized */}
          {!isMinimized && (
            <>
              {/* Messages Scroll Area */}
              <div className="flex-1 p-4 sm:p-5 overflow-y-auto space-y-4 bg-slate-50/70">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div
                      className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white rounded-br-none shadow-sm"
                          : "bg-white text-slate-800 rounded-bl-none border border-slate-200/80 shadow-xs"
                      }`}
                    >
                      <FormattedMessageText content={msg.content} isUser={msg.role === "user"} />
                    </div>

                    {/* Attached Mini Property Cards */}
                    {msg.properties && msg.properties.length > 0 && (
                      <div className={`mt-3 w-full ${isExpanded ? "max-w-full" : "max-w-[96%]"}`}>
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-1 flex items-center gap-1.5">
                          <Home className="w-3.5 h-3.5 text-blue-600" />
                          <span>Gợi ý bất động sản phù hợp ({msg.properties.length}):</span>
                        </div>

                        {/* 1-column on compact, 2-column on expanded */}
                        <div
                          className={`grid gap-2.5 ${
                            isExpanded ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1"
                          }`}
                        >
                          {msg.properties.map((prop, idx) => {
                            const detailUrl = sanitizeUrl(`/properties/${prop.id}`);
                            const placeholderImg = getPlaceholderImage(prop.property_type, idx);
                            const imgUrl = sanitizeUrl(placeholderImg);

                            return (
                              <Link
                                key={prop.id}
                                href={detailUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group block bg-white hover:bg-blue-50/30 p-3 rounded-xl border border-slate-200 hover:border-blue-400 transition-all shadow-xs"
                              >
                                <div className="flex gap-3">
                                  {/* Thumbnail */}
                                  <div className="relative w-22 h-22 rounded-lg overflow-hidden shrink-0 bg-slate-100 border border-slate-100">
                                    {imgUrl ? (
                                      <img
                                        src={imgUrl}
                                        alt={prop.title}
                                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                        loading="lazy"
                                      />
                                    ) : (
                                      <div className="w-full h-full flex items-center justify-center text-slate-400">
                                        <Building2 className="w-6 h-6" />
                                      </div>
                                    )}
                                    <span
                                      className={`absolute top-1 left-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider shadow-xs ${
                                        prop.listing_type === "rent"
                                          ? "bg-amber-600 text-white"
                                          : "bg-blue-600 text-white"
                                      }`}
                                    >
                                      {prop.listing_type === "rent" ? "Thuê" : "Bán"}
                                    </span>
                                  </div>

                                  {/* Info */}
                                  <div className="flex-1 min-w-0 flex flex-col justify-between">
                                    <div>
                                      <h4 className="font-semibold text-xs text-slate-900 group-hover:text-blue-600 line-clamp-2 transition-colors">
                                        {prop.title}
                                      </h4>
                                      <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-1">
                                        <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                                        <span className="truncate">
                                          {prop.district ? `${prop.district}, ` : ""}
                                          {prop.city}
                                        </span>
                                      </div>
                                    </div>

                                    <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-100">
                                      <span className="font-bold text-xs text-rose-600">
                                        {formatPrice(prop.price, prop.currency, prop.listing_type)}
                                      </span>
                                      <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                                        <span>{prop.area_sqm} m²</span>
                                        {prop.num_bedrooms ? (
                                          <span className="flex items-center gap-0.5">
                                            <Bed className="w-3 h-3" />
                                            {prop.num_bedrooms}
                                          </span>
                                        ) : null}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </Link>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Save Search Alert CTA */}
                    {msg.role === "assistant" && (msg.criteria || (msg.properties && msg.properties.length > 0)) && (
                      <div className="mt-2.5 pt-2 flex items-center">
                        {msg.alertSaved ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Đã lưu cảnh báo thành công!
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleSaveAlert(msg)}
                            disabled={savingAlertId === msg.id}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 px-3 py-1.5 text-xs font-bold transition cursor-pointer shadow-2xs"
                          >
                            <Bell className="w-3.5 h-3.5 text-blue-600" />
                            <span>Lưu tìm kiếm & Nhận cảnh báo khi có căn mới</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {/* Loading Typing Indicator */}
                {isLoading && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-200 flex items-center justify-center shrink-0">
                      <Headphones className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="bg-white text-slate-500 px-4 py-3 rounded-2xl rounded-bl-none border border-slate-200 shadow-xs flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-500">Đang tìm kiếm bđs</span>
                      <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce"></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Sample Prompt Suggestion Chips */}
              {!isLoading && latestSuggestions.length > 0 && (
                <div className="px-3 py-2 bg-white border-t border-slate-100 overflow-x-auto flex gap-1.5 no-scrollbar">
                  {latestSuggestions.slice(0, 4).map((sug, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendMessage(sug)}
                      className="shrink-0 text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 px-3 py-1.5 rounded-full border border-slate-200 hover:border-blue-300 transition-colors cursor-pointer flex items-center gap-1.5"
                    >
                      <Compass className="w-3 h-3 text-blue-600 shrink-0" />
                      <span className="truncate max-w-[240px]">{sug}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Input Form */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Nhập nhu cầu tìm kiếm (vd: Căn hộ 2PN Quận 1 dưới 3 tỷ)..."
                  disabled={isLoading}
                  className="flex-1 text-sm px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isLoading}
                  className="bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 cursor-pointer shadow-sm"
                  title="Gửi tin nhắn"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </>
          )}
        </div>
      )}

      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center gap-2.5 bg-slate-900 hover:bg-slate-800 text-white pl-3.5 pr-4 py-2.5 sm:pl-4 sm:pr-5 sm:py-3 rounded-full shadow-2xl hover:shadow-blue-500/20 active:scale-95 transition-all duration-200 cursor-pointer border border-slate-700/80 backdrop-blur-md ring-1 ring-white/10"
          aria-label="Tư vấn bất động sản trực tuyến"
        >
          <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-blue-600/30 border border-blue-500/30 text-blue-400 group-hover:text-blue-300 transition shrink-0">
            <Headphones className="w-4 h-4 text-blue-400" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-slate-900 animate-pulse" />
          </div>
          <div className="flex flex-col text-left">
            <span className="font-bold text-xs sm:text-sm tracking-tight text-white leading-tight whitespace-nowrap">
              <span className="hidden sm:inline">Tư vấn Bất động sản</span>
              <span className="sm:hidden">Tư vấn BĐS</span>
            </span>
            <span className="text-[10px] text-emerald-400 font-medium leading-none mt-0.5 hidden xs:inline-block">
              Trực tuyến 24/7
            </span>
          </div>
        </button>
      )}
    </div>
  );
}
