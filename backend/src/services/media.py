"""Safe, allow-listed video embed parsing."""
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class VideoEmbed:
    provider: str
    embed_url: str
    aspect_ratio: str


def parse_video_metadata(value: str | None) -> dict[str, str] | None:
    embed = parse_video_embed(value)
    if embed is None:
        return None
    return {"platform": embed.provider, "video_id": embed.embed_url.rsplit("/", 1)[-1], "embed_url": embed.embed_url}


def parse_video_embed(value: str | None) -> VideoEmbed | None:
    """Return an embed only for public YouTube or TikTok URLs."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.hostname.lower() if parsed.hostname else ""
    path = [part for part in parsed.path.split("/") if part]
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        video_id = parse_qs(parsed.query).get("v", [None])[0] if host != "youtu.be" else (path[0] if path else None)
        is_short = bool(path and path[0] == "shorts")
        if is_short:
            video_id = path[1] if len(path) > 1 else None
        if video_id and video_id.replace("-", "").replace("_", "").isalnum() and len(video_id) == 11:
            return VideoEmbed("youtube", f"https://www.youtube.com/embed/{video_id}", "9 / 16" if is_short else "16 / 9")
    if host in {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com"} and len(path) >= 3 and path[-2] == "video":
        video_id = path[-1]
        if video_id.isdigit():
            return VideoEmbed("tiktok", f"https://www.tiktok.com/embed/v2/{video_id}", "9 / 16")
    return None
