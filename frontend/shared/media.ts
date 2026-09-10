export type VideoEmbed = { provider: "youtube" | "tiktok"; embedUrl: string; aspectRatio: "16 / 9" | "9 / 16" };

export function getVideoEmbedInfo(value?: string | null): VideoEmbed | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (!/^https?:$/.test(url.protocol)) return null;
    const host = url.hostname.toLowerCase();
    const path = url.pathname.split("/").filter(Boolean);
    const youtube = ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"];
    if (youtube.includes(host)) {
      const short = path[0] === "shorts";
      const id = host === "youtu.be" ? path[0] : short ? path[1] : url.searchParams.get("v");
      if (id && /^[A-Za-z0-9_-]{11}$/.test(id)) return { provider: "youtube", embedUrl: `https://www.youtube.com/embed/${id}`, aspectRatio: short ? "9 / 16" : "16 / 9" };
    }
    const videoId = path[path.length - 1];
    if (["tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com"].includes(host) && path[path.length - 2] === "video" && /^\d+$/.test(videoId ?? "")) return { provider: "tiktok", embedUrl: `https://www.tiktok.com/embed/v2/${videoId}`, aspectRatio: "9 / 16" };
  } catch {}
  return null;
}

export function getVirtualTourEmbed(value?: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || !["my.matterport.com", "matterport.com", "www.matterport.com"].includes(url.hostname.toLowerCase())) return null;
    return url.toString();
  } catch { return null; }
}
