import pytest

from src.schemas.property import PropertyCreate
from src.services.media import parse_video_embed, parse_video_metadata


@pytest.mark.parametrize(("url", "provider", "ratio"), [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube", "16 / 9"),
    ("https://youtu.be/dQw4w9WgXcQ", "youtube", "16 / 9"),
    ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "youtube", "9 / 16"),
    ("https://www.tiktok.com/@space/video/1234567890123456789", "tiktok", "9 / 16"),
])
def test_parse_recognized_public_video_urls(url, provider, ratio):
    embed = parse_video_embed(url)
    assert embed is not None
    assert (embed.provider, embed.aspect_ratio) == (provider, ratio)


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://evil.example/embed/dQw4w9WgXcQ", "https://youtube.com/watch?v=bad"])
def test_parser_never_embeds_unknown_or_unsafe_urls(url):
    assert parse_video_embed(url) is None


def test_video_metadata_contains_safe_platform_id_and_embed_url():
    metadata = parse_video_metadata("https://www.youtube.com/shorts/dQw4w9WgXcQ")
    assert metadata == {
        "platform": "youtube",
        "video_id": "dQw4w9WgXcQ",
        "embed_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
    }


def test_unknown_media_url_is_retained_by_property_schema():
    property_in = PropertyCreate(
        title="Căn hộ có video riêng", description="Mô tả đủ dài cho bất động sản thử nghiệm.", property_type="apartment", listing_type="sale", price=1, area_sqm=1, address="1 Test Street", city="Hà Nội", video_url="https://example.org/custom-video"
    )
    assert property_in.video_url == "https://example.org/custom-video"
