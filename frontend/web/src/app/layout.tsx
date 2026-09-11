import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/Footer";
import ChatAssistantWidget from "@/components/ChatAssistantWidget";
import { AuthProvider } from "@/lib/auth";
import { FavoritesProvider } from "@/lib/favorites";
import { ComparisonProvider } from "@/lib/comparison";
import StickyComparisonBar from "@/components/StickyComparisonBar";
import ScrollToTopButton from "@/components/ScrollToTopButton";

const inter = Inter({ subsets: ["latin", "vietnamese"] });

export const metadata: Metadata = {
  title: "Space247 - Nền tảng Bất động sản thông minh",
  description:
    "Khám phá, mua bán và thuê bất động sản phù hợp với nhu cầu của bạn trên Space247.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="scroll-smooth">
      <body className={`${inter.className} min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased`}>
        <AuthProvider>
          <FavoritesProvider>
            <ComparisonProvider>
              <Header />
              <main className="flex-1 mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 py-8 pb-24">
                {children}
              </main>
              <Footer />
              <ChatAssistantWidget />
              <StickyComparisonBar />
              <ScrollToTopButton />
            </ComparisonProvider>
          </FavoritesProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

