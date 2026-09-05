import base64
import json
import logging
import math
import os
import re
from typing import Any
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import get_cached_json, set_cached_json
from src.models.property import Property
from src.schemas.agent import (
    ComparableProperty,
    ExtractedSpecs,
    GenerateListingRequest,
    GenerateListingResponse,
    ValuationRequest,
    ValuationResponse,
)
from src.services.spatial_service import haversine_distance_km

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        from src.core.config import settings

        self.api_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = (settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client for AgentService: {e}")
                self.client = None
        else:
            logger.info("GEMINI_API_KEY not configured. AgentService listing generator will use structured fallback.")

    async def generate_listing(self, request: GenerateListingRequest) -> GenerateListingResponse:
        """
        Generate SEO listing title, rich Vietnamese Markdown description,
        and extract technical specs using Gemini Multimodal or structured heuristic fallback.
        """
        raw_prompts = request.text_prompts
        if isinstance(raw_prompts, list):
            notes_str = "\n".join(f"- {p}" for p in raw_prompts if p.strip())
        else:
            notes_str = str(raw_prompts).strip()

        if self.client:
            try:
                prompt = self._build_gemini_prompt(
                    notes=notes_str,
                    property_type=request.property_type,
                    target_audience=request.target_audience,
                )
                contents: list[Any] = [prompt]

                if request.image_base64:
                    img_data = request.image_base64
                    mime_type = "image/jpeg"
                    if "," in img_data:
                        prefix, img_data = img_data.split(",", 1)
                        if "image/png" in prefix:
                            mime_type = "image/png"
                        elif "image/webp" in prefix:
                            mime_type = "image/webp"

                    try:
                        raw_bytes = base64.b64decode(img_data)
                        contents.append(
                            types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
                        )
                    except Exception as img_err:
                        logger.warning(f"Could not parse image_base64 for multimodal listing generation: {img_err}")

                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        response_mime_type="application/json",
                    ),
                )

                if response and response.text:
                    parsed = json.loads(response.text)
                    specs_data = parsed.get("extracted_specs", {})
                    extracted = ExtractedSpecs(
                        area_sqm=specs_data.get("area_sqm"),
                        num_bedrooms=specs_data.get("num_bedrooms"),
                        num_bathrooms=specs_data.get("num_bathrooms"),
                        orientation=specs_data.get("orientation"),
                        legal_status=specs_data.get("legal_status"),
                        frontage_meters=specs_data.get("frontage_meters"),
                        suggested_price=specs_data.get("suggested_price"),
                        amenities=specs_data.get("amenities", []),
                    )
                    return GenerateListingResponse(
                        title_seo=parsed.get("title_seo", self._generate_seo_title(extracted, request.property_type)),
                        description_markdown=parsed.get("description_markdown", ""),
                        extracted_specs=extracted,
                    )
            except Exception as e:
                logger.error(f"Gemini API error during listing generation, falling back: {e}")

        # Fallback to local heuristic extractor & generator
        return self._generate_fallback_listing(notes_str, request.property_type, request.target_audience)

    def _build_gemini_prompt(self, notes: str, property_type: str, target_audience: str | None) -> str:
        audience_hint = f"Đối tượng mục tiêu hướng đến: {target_audience}." if target_audience else ""
        return f"""Bạn là chuyên gia Marketing và Môi giới Bất động sản cao cấp tại Việt Nam trên nền tảng Space247.
Dựa vào các thông tin ghi chú nhanh và hình ảnh đính kèm (nếu có), hãy soạn một bài đăng tin BĐS chuyên nghiệp, chuẩn mực doanh nghiệp, tối ưu SEO, phong cách trang nhã, nghiêm túc, đáng tin cậy.

TIÊU CHUẨN TRÌNH BÀY QUAN TRỌNG:
- TUYỆT ĐỐI KHÔNG SỬ DỤNG BẤT KỲ ICON / BIỂU TƯỢNG CẢM XÚC (EMOJI) NÀO (như 🌟, 📍, 📞, ✨, 💎, 📋, ⚖️, 🚀, v.v.). Trình bày văn bản chuyên nghiệp như tài liệu phát hành chính thức của sàn giao dịch bất động sản cao cấp.
- Các tiêu đề mục phải dùng đề mục Markdown rõ ràng (ví dụ: "## Tiêu đề bài đăng", "### Thông số tổng quan", "### Ưu điểm nổi bật & Vị trí", "### Tiện ích", "### Pháp lý & Giao dịch", "### Thông tin liên hệ").
- Không lạm dụng từ ngữ sáo rỗng hoặc quá đậm chất AI. Câu cú gãy gọn, tập trung vào thông tin thực tế, giá trị thương mại và pháp lý.

Loại hình BĐS: {property_type}
{audience_hint}

Ghi chú từ môi giới:
{notes}

YÊU CẦU ĐẦU RA:
Trả về định dạng JSON thuần túy (không bọc trong markdown codeblock nếu có thể, hoặc đảm bảo parse được JSON) với cấu trúc:
{{
  "title_seo": "Tiêu đề tin đăng ngắn gọn, hấp dẫn, chuẩn SEO (dưới 80 ký tự), chứa từ khóa chính, diện tích/số phòng (không kèm emoji)",
  "description_markdown": "Bài viết mô tả chi tiết bằng tiếng Việt định dạng Markdown chuẩn mực doanh nghiệp: KHÔNG CÓ EMOJI, gồm các phần tiêu đề lôi cuốn, thông số tổng quan, vị trí kết nối giao thông, tiện ích, tình trạng pháp lý, thông tin liên hệ xem nhà",
  "extracted_specs": {{
    "area_sqm": float hoặc null,
    "num_bedrooms": int hoặc null,
    "num_bathrooms": int hoặc null,
    "orientation": string hoặc null (ví dụ: Đông Nam, Tây Bắc),
    "legal_status": string hoặc null (ví dụ: Sổ hồng chính chủ, Đã có sổ đỏ, HĐMB),
    "frontage_meters": float hoặc null,
    "suggested_price": float hoặc null (VNĐ, tính tổng giá),
    "amenities": ["danh sách", "tiện ích", "nhận diện"]
  }}
}}
"""

    def _generate_fallback_listing(
        self,
        notes: str,
        property_type: str,
        target_audience: str | None,
    ) -> GenerateListingResponse:
        """Rule-based heuristic fallback when Gemini LLM is unavailable."""
        extracted = self._extract_specs_heuristic(notes)
        title = self._generate_seo_title(extracted, property_type)

        type_map = {
            "apartment": "Căn hộ chung cư",
            "house": "Nhà riêng / Biệt thự",
            "land": "Đất nền",
            "commercial": "Mặt bằng thương mại",
            "villa": "Biệt thự cao cấp",
        }
        type_vi = type_map.get(property_type, "Bất động sản")

        specs_lines = []
        if extracted.area_sqm:
            specs_lines.append(f"- **Diện tích:** {extracted.area_sqm} m²")
        if extracted.num_bedrooms:
            specs_lines.append(f"- **Số phòng ngủ:** {extracted.num_bedrooms} PN")
        if extracted.num_bathrooms:
            specs_lines.append(f"- **Số phòng tắm:** {extracted.num_bathrooms} WC")
        if extracted.orientation:
            specs_lines.append(f"- **Hướng:** {extracted.orientation}")
        if extracted.legal_status:
            specs_lines.append(f"- **Pháp lý:** {extracted.legal_status}")
        if extracted.frontage_meters:
            specs_lines.append(f"- **Mặt tiền:** {extracted.frontage_meters} m")
        if extracted.suggested_price:
            specs_lines.append(f"- **Mức giá dự kiến:** {extracted.suggested_price:,.0f} VNĐ")

        specs_md = "\n".join(specs_lines) if specs_lines else "- Đang cập nhật thông số chi tiết."

        amenities_md = ""
        if extracted.amenities:
            amenities_md = "\n### Tiện ích nổi bật\n" + "\n".join(f"- {a}" for a in extracted.amenities)

        audience_note = f"Không gian sống lý tưởng phù hợp cho {target_audience}." if target_audience else "Lựa chọn phù hợp cho nhu cầu an cư hoặc khai thác kinh doanh sinh lời bền vững."

        description_markdown = f"""## {title}

Space247 trân trọng giới thiệu thông tin {type_vi.lower()} tại vị trí chiến lược, đáp ứng trọn vẹn tiêu chí an cư và tiềm năng phát triển.

### Thông số tổng quan
{specs_md}

### Ưu điểm nổi bật & Vị trí
{notes if notes else "Vị trí kết nối giao thông thuận tiện, khu dân cư hiện hữu, an ninh và văn minh."}

{audience_note}
{amenities_md}

### Pháp lý & Giao dịch
- Tình trạng pháp lý: {extracted.legal_status or "Sổ đỏ/Sổ hồng hoàn chỉnh, sẵn sàng công chứng sang tên"}.
- Hỗ trợ thủ tục chuyển nhượng minh bạch, chuẩn xác và đúng quy định pháp luật.

---
### Thông tin liên hệ
Quý khách hàng quan tâm vui lòng liên hệ trực tiếp để nhận hồ sơ chi tiết và đặt lịch khảo sát thực tế!
"""

        return GenerateListingResponse(
            title_seo=title,
            description_markdown=description_markdown,
            extracted_specs=extracted,
        )

    def _extract_specs_heuristic(self, text: str) -> ExtractedSpecs:
        low = text.lower()

        area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²|mét vuông)", low)
        area = float(area_match.group(1).replace(",", ".")) if area_match else None

        bed_match = re.search(r"(\d+)\s*(?:pn|phòng ngủ|ngủ|bed)", low)
        bedrooms = int(bed_match.group(1)) if bed_match else None

        bath_match = re.search(r"(\d+)\s*(?:wc|phòng tắm|vệ sinh|vs|bath)", low)
        bathrooms = int(bath_match.group(1)) if bath_match else None

        front_match = re.search(r"(?:mặt tiền|mt)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:m|mét)?", low)
        frontage = float(front_match.group(1).replace(",", ".")) if front_match else None

        orientation = None
        for direct in [
            "đông nam", "đông bắc", "tây nam", "tây bắc",
            "đông", "tây", "nam", "bắc",
        ]:
            if f"hướng {direct}" in low or f"hướng: {direct}" in low or direct in low:
                orientation = direct.title()
                break

        legal = None
        if "sổ đỏ" in low:
            legal = "Sổ đỏ chính chủ"
        elif "sổ hồng" in low:
            legal = "Sổ hồng lâu dài"
        elif "hđmb" in low or "hợp đồng mua bán" in low:
            legal = "Hợp đồng mua bán (HĐMB)"
        elif "chờ sổ" in low:
            legal = "Đang chờ cấp sổ"

        suggested_price = None
        price_billion = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:tỷ|ty|b)", low)
        if price_billion:
            suggested_price = float(price_billion.group(1).replace(",", ".")) * 1_000_000_000
        else:
            price_million = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)", low)
            if price_million:
                suggested_price = float(price_million.group(1).replace(",", ".")) * 1_000_000

        amenities = []
        amenity_keywords = [
            ("hồ bơi", "Hồ bơi tràn bờ"),
            ("gym", "Phòng Gym & Yoga"),
            ("thang máy", "Thang máy tốc độ cao"),
            ("ban công", "Ban công thoáng mát"),
            ("view hồ", "Tầm nhìn view hồ điều hòa"),
            ("view sông", "View sông thoáng đãng"),
            ("nội thất", "Nội thất cao cấp đầy đủ"),
            ("đậu xe", "Chỗ đậu ô tô định danh"),
            ("bảo vệ", "An ninh 24/7"),
            ("gần metro", "Gần ga Metro"),
        ]
        for kw, label in amenity_keywords:
            if kw in low:
                amenities.append(label)

        return ExtractedSpecs(
            area_sqm=area,
            num_bedrooms=bedrooms,
            num_bathrooms=bathrooms,
            orientation=orientation,
            legal_status=legal,
            frontage_meters=frontage,
            suggested_price=suggested_price,
            amenities=amenities,
        )

    def _generate_seo_title(self, specs: ExtractedSpecs, property_type: str) -> str:
        type_prefix = {
            "apartment": "Bán Căn Hộ",
            "house": "Bán Nhà Đẹp",
            "land": "Bán Đất Nền",
            "commercial": "Cho Thuê Mặt Bằng",
            "villa": "Bán Biệt Thự",
        }.get(property_type, "Bán Bất Động Sản")

        parts = [type_prefix]
        if specs.num_bedrooms:
            parts.append(f"{specs.num_bedrooms}PN")
        if specs.area_sqm:
            parts.append(f"{int(specs.area_sqm)}m²")
        if specs.legal_status:
            parts.append(specs.legal_status)
        elif specs.orientation:
            parts.append(f"Hướng {specs.orientation}")
        else:
            parts.append("Vị Trí Đắc Địa")

        return " - ".join(parts)

    async def estimate_valuation(self, db: AsyncSession, request: ValuationRequest) -> ValuationResponse:
        """
        Smart AVM Pricing Advisor using PostGIS/Haversine search, Weighted KNN,
        dynamic radius expansion (Option A: 2.5km up to 8.0km), and Redis caching.
        """
        cache_key = (
            f"cache:avm:{request.property_type}:{request.area_sqm:.1f}:"
            f"{request.latitude:.4f}:{request.longitude:.4f}:{request.radius_km:.1f}:"
            f"{request.num_bedrooms}:{request.num_bathrooms}:{request.user_proposed_price}"
        )

        cached_data = await get_cached_json(cache_key)
        if cached_data:
            logger.info("AVM Valuation retrieved from Redis cache")
            return ValuationResponse(**cached_data)

        # 1. Fetch active properties from DB
        stmt = (
            select(Property)
            .where(Property.status == "active")
            .where(Property.latitude.is_not(None))
            .where(Property.longitude.is_not(None))
            .where(Property.price > 0)
            .where(Property.area_sqm > 0)
        )
        result = await db.execute(stmt)
        all_active_props = result.scalars().all()

        matching_type_props = [
            p for p in all_active_props if p.property_type == request.property_type
        ]
        pool = matching_type_props if len(matching_type_props) >= 2 else all_active_props

        # 2. Dynamic Radius Expansion (Option A: Start at request.radius_km, expand up to 8.0km)
        current_radius = max(0.5, request.radius_km)
        max_radius = 8.0
        expansion_steps = [current_radius, 4.5, 6.5, max_radius]
        search_radii = sorted(list(set([r for r in expansion_steps if r >= current_radius])))
        if max_radius not in search_radii:
            search_radii.append(max_radius)

        radius_used = current_radius
        comps: list[tuple[Property, float]] = []

        for r in search_radii:
            radius_used = r
            comps = []
            for p in pool:
                d = haversine_distance_km(
                    request.latitude, request.longitude, float(p.latitude), float(p.longitude)
                )
                if d <= r:
                    comps.append((p, d))
            if len(comps) >= 2:
                break

        if len(comps) < 2 and pool != all_active_props:
            for r in search_radii:
                radius_used = r
                comps = []
                for p in all_active_props:
                    d = haversine_distance_km(
                        request.latitude, request.longitude, float(p.latitude), float(p.longitude)
                    )
                    if d <= r:
                        comps.append((p, d))
                if len(comps) >= 2:
                    break

        comps.sort(key=lambda item: item[1])
        top_comps = comps[:8]

        # 3. Weighted KNN Calculation
        if top_comps:
            total_weight = 0.0
            weighted_price_sqm = 0.0
            comparable_dto_list: list[ComparableProperty] = []

            for prop, dist in top_comps:
                p_price = float(prop.price)
                p_area = float(prop.area_sqm)
                unit_price = p_price / p_area

                w_dist = 1.0 / (1.0 + (dist ** 1.5))
                area_ratio = min(p_area, request.area_sqm) / max(p_area, request.area_sqm)
                w_area = area_ratio ** 2
                w_bed = 1.0
                if request.num_bedrooms is not None and prop.num_bedrooms is not None:
                    diff = abs(request.num_bedrooms - prop.num_bedrooms)
                    w_bed = max(0.6, 1.0 - diff * 0.2)

                weight = w_dist * w_area * w_bed
                total_weight += weight
                weighted_price_sqm += unit_price * weight

                comparable_dto_list.append(
                    ComparableProperty(
                        id=str(prop.id),
                        title=prop.title,
                        price=p_price,
                        area_sqm=p_area,
                        price_per_sqm=round(unit_price, 0),
                        distance_km=round(dist, 2),
                        address=prop.address,
                        property_type=prop.property_type,
                    )
                )

            estimated_price_per_sqm = round(weighted_price_sqm / max(total_weight, 1e-6), -4)
            base_conf = 0.88 if len(top_comps) >= 3 else 0.72
            if radius_used > 2.5:
                penalty = min(0.35, ((radius_used - 2.5) / 5.5) * 0.30)
                base_conf -= penalty
            if len(top_comps) < 2:
                base_conf -= 0.25
            confidence_score = round(max(0.30, min(0.95, base_conf)), 2)
        else:
            baseline_prices = {
                "apartment": 55_000_000.0,
                "house": 95_000_000.0,
                "land": 60_000_000.0,
                "commercial": 80_000_000.0,
                "villa": 130_000_000.0,
            }
            estimated_price_per_sqm = baseline_prices.get(request.property_type, 50_000_000.0)
            confidence_score = 0.25
            comparable_dto_list = []

        estimated_total_price = round(estimated_price_per_sqm * request.area_sqm, -5)
        price_range_low = round(estimated_total_price * 0.92, -5)
        price_range_high = round(estimated_total_price * 1.08, -5)

        # 4. Pricing Deviation Analysis & Advice
        deviation_percentage = None
        pricing_advice = None

        if request.user_proposed_price and request.user_proposed_price > 0:
            diff = request.user_proposed_price - estimated_total_price
            deviation_percentage = round((diff / estimated_total_price) * 100.0, 1)

            if deviation_percentage > 10.0:
                pricing_advice = (
                    f"⚠️ Mức giá bạn dự kiến đang cao hơn {deviation_percentage:.1f}% so với mặt bằng thị trường "
                    f"(Định giá đề xuất: {estimated_total_price:,.0f} đ). Khuyến nghị điều chỉnh để tối ưu hóa thanh khoản."
                )
            elif deviation_percentage < -10.0:
                pricing_advice = (
                    f"🔥 Mức giá bạn dự kiến đang thấp hơn {abs(deviation_percentage):.1f}% so với mặt bằng thị trường "
                    f"(Định giá đề xuất: {estimated_total_price:,.0f} đ). Bất động sản có tính cạnh tranh rất cao, kỳ vọng thanh khoản nhanh."
                )
            else:
                pricing_advice = (
                    f"✅ Mức giá đề xuất rất hợp lý ({deviation_percentage:+.1f}% so với định giá AVM {estimated_total_price:,.0f} đ). "
                    f"Phù hợp với biên độ giao dịch thực tế khu vực."
                )
        else:
            if radius_used > request.radius_km:
                pricing_advice = (
                    f"Đã mở rộng bán kính tìm kiếm lên {radius_used:.1f} km để thu thập đủ mẫu tham chiếu. "
                    f"Độ tin cậy được điều chỉnh về {int(confidence_score * 100)}%."
                )
            else:
                pricing_advice = (
                    f"Mức định giá được tính toán dựa trên {len(comparable_dto_list)} bất động sản tương đồng "
                    f"trong bán kính {radius_used:.1f} km."
                )

        response = ValuationResponse(
            estimated_price_per_sqm=estimated_price_per_sqm,
            estimated_total_price=estimated_total_price,
            price_range_low=price_range_low,
            price_range_high=price_range_high,
            confidence_score=confidence_score,
            market_trend="stable",
            radius_used_km=round(radius_used, 1),
            comparable_properties=comparable_dto_list,
            deviation_percentage=deviation_percentage,
            pricing_advice=pricing_advice,
        )

        await set_cached_json(cache_key, response.model_dump(), ttl=900)
        return response


_agent_service_instance: AgentService | None = None


def get_agent_service() -> AgentService:
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance
