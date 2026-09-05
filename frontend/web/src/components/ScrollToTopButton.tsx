"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";
import { useComparison } from "@/lib/comparison";

export default function ScrollToTopButton() {
  const [isVisible, setIsVisible] = useState(false);
  const { selectedProperties } = useComparison();
  const hasComparisonBar = selectedProperties.length > 0;

  useEffect(() => {
    const toggleVisibility = () => {
      // Show button after scrolling down 300px
      if (window.scrollY > 300) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener("scroll", toggleVisibility, { passive: true });
    return () => window.removeEventListener("scroll", toggleVisibility);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  if (!isVisible) return null;

  return (
    <button
      type="button"
      onClick={scrollToTop}
      className={`no-print fixed z-40 right-3 sm:right-6 ${
        hasComparisonBar ? "bottom-36 sm:bottom-40" : "bottom-20 sm:bottom-24"
      } p-3 sm:p-3.5 bg-white/90 hover:bg-white text-slate-700 hover:text-blue-600 rounded-full shadow-lg hover:shadow-xl border border-slate-200 backdrop-blur-md transition-all duration-300 cursor-pointer flex items-center justify-center group focus:outline-hidden focus:ring-2 focus:ring-blue-500 active:scale-95 animate-fade-in`}
      title="Cuộn lên đầu trang"
      aria-label="Cuộn lên đầu trang"
    >
      <ArrowUp className="w-5 h-5 transition-transform duration-200 group-hover:-translate-y-0.5" />
    </button>
  );
}
