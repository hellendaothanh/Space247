import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number, currency: string = "VND", listingType?: string): string {
  if (listingType === "rent") {
    if (price >= 1_000_000) {
      return `${(price / 1_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} triệu/tháng`;
    }
    return `${price.toLocaleString("vi-VN")} ${currency}/tháng`;
  }

  // Sale
  if (price >= 1_000_000_000) {
    return `${(price / 1_000_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 2 })} tỷ`;
  }
  if (price >= 1_000_000) {
    return `${(price / 1_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} triệu`;
  }
  return `${price.toLocaleString("vi-VN")} ${currency}`;
}

export function formatPropertyType(type: string): string {
  const map: Record<string, string> = {
    apartment: "Căn hộ chung cư",
    house: "Nhà phố",
    villa: "Biệt thự",
    land: "Đất nền",
    commercial: "Mặt bằng thương mại",
  };
  return map[type] || type;
}

export function getPlaceholderImage(propertyType: string, index: number = 0): string {
  const images: Record<string, string[]> = {
    apartment: [
      "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80",
      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1000&q=80",
      "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80",
    ],
    house: [
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
      "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1000&q=80",
    ],
    villa: [
      "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=1000&q=80",
      "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1000&q=80",
    ],
    commercial: [
      "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80",
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=80",
    ],
    land: [
      "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=80",
    ],
  };

  const list = images[propertyType] || images.apartment;
  return list[index % list.length];
}

export function sanitizeUrl(url?: string | null): string {
  if (!url) return "";
  const trimmed = url.trim();
  if (trimmed.startsWith("/") || trimmed.startsWith("#")) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return trimmed;
    }
  } catch {
    return "";
  }
  return "";
}

export function formatProjectStatus(status: string): { label: string; color: string } {
  const map: Record<string, { label: string; color: string }> = {
    upcoming: { label: "Sắp mở bán", color: "bg-amber-500/90 text-white" },
    under_construction: { label: "Đang thi công", color: "bg-blue-600/90 text-white" },
    handing_over: { label: "Đang bàn giao", color: "bg-purple-600/90 text-white" },
    completed: { label: "Đã bàn giao", color: "bg-emerald-600/90 text-white" },
  };
  return map[status] || { label: status, color: "bg-slate-700/90 text-white" };
}

/**
 * Automatically parses coordinate strings (e.g. copied from Google Maps or search bars)
 * Supports:
 * - "10.76169819301489, 106.69584455406623"
 * - "10.76169819301489,106.69584455406623"
 * - "10.76169819301489 106.69584455406623"
 * - "https://www.google.com/maps/@10.761698,106.695844,17z"
 * - "https://maps.google.com/?q=10.761698,106.695844"
 * - "!3d10.761698!4d106.695844"
 */
export function parseCoordinates(input: string): { latitude: string; longitude: string } | null {
  if (!input) return null;
  const trimmed = input.trim();

  // Check URL patterns
  const atMatch = trimmed.match(/@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)/);
  if (atMatch) {
    return { latitude: atMatch[1], longitude: atMatch[2] };
  }

  const qMatch = trimmed.match(/[?&]q=(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)/);
  if (qMatch) {
    return { latitude: qMatch[1], longitude: qMatch[2] };
  }

  const dMatch = trimmed.match(/!3d(-?\d+(?:\.\d+)?)[^!]*!4d(-?\d+(?:\.\d+)?)/);
  if (dMatch) {
    return { latitude: dMatch[1], longitude: dMatch[2] };
  }

  // Check direct latitude, longitude format separated by comma, semicolon, or space
  const parts = trimmed.split(/[,;\s]+/).filter(Boolean);
  if (parts.length >= 2) {
    const lat = parseFloat(parts[0]);
    const lng = parseFloat(parts[1]);
    if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      return { latitude: parts[0], longitude: parts[1] };
    }
  }

  return null;
}


