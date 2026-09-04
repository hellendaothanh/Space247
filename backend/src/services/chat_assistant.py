import logging
import re
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.property import Property
from src.schemas.chat import ChatMessage, ChatRole, ExtractedCriteria
from src.schemas.property import (
    ListingType,
    PropertyResponse,
    PropertyStatus,
    PropertyType,
    SearchResultItem,
)
from src.services.embedding import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


def _sanitize_tsquery(query_text: str) -> str:
    clean_tokens = [w for w in re.split(r"[\s,.;:!?()\'\"\\/+\-_]+", query_text) if len(w) >= 2]
    if not clean_tokens:
        return ""
    return " | ".join(clean_tokens)


class ChatAssistantService:
    def __init__(self, embedding_service: EmbeddingService | None = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def parse_intent_and_criteria(self, messages: list[ChatMessage]) -> tuple[bool, ExtractedCriteria]:
        """
        Analyze conversation messages, determine if there is property search intent,
        and extract structured search criteria (price, location, property type, amenities).
        """
        if not messages:
            return False, ExtractedCriteria(raw_query="")

        # Gather user messages (prioritize the last message, but incorporate context)
        latest_user_msg = ""
        combined_user_text = ""
        for msg in reversed(messages):
            if msg.role == ChatRole.USER.value or msg.role == "user":
                if not latest_user_msg:
                    latest_user_msg = msg.content
                combined_user_text = msg.content + " " + combined_user_text

        if not latest_user_msg:
            latest_user_msg = messages[-1].content
            combined_user_text = latest_user_msg

        text = latest_user_msg.strip()
        lower_text = text.lower()
        context_lower = combined_user_text.lower()

        # Common real estate intent keywords
        re_keywords = [
            "tìm", "mua", "bán", "thuê", "căn hộ", "chung cư", "nhà", "biệt thự",
            "villa", "đất", "mặt bằng", "quận", "huyện", "phòng ngủ", "tỷ", "tỉ",
            "triệu", "triệu/tháng", "tr/tháng", "diện tích", "hồ bơi", "ban công",
            "nội thất", "hà nội", "hồ chí minh", "đà nẵng", "quận 1", "bình thạnh",
            "vay", "lãi suất", "trả góp", "mỗi tháng trả", "ngân hàng"
        ]
        has_search_keywords = any(kw in lower_text for kw in re_keywords)

        greeting_terms = [
            "chào", "hello", "hi", "hey", "bạn là ai", "làm được gì", "giúp gì",
            "tính năng", "trợ giúp", "help", "cảm ơn", "tạm biệt", "space247",
        ]
        has_greeting = any(gt in lower_text for gt in greeting_terms)

        # If user message does not contain real estate search keywords, treat as non-search / greeting
        if not has_search_keywords or (has_greeting and not has_search_keywords):
            return False, ExtractedCriteria(raw_query=text)


        # 1. Extract Listing Type (Sale vs Rent)
        listing_type: ListingType | None = None
        if re.search(r"\b(thuê|cho thuê|cần thuê|tìm thuê|mướn|triệu/tháng|tr/tháng)\b", lower_text):
            listing_type = ListingType.RENT
        elif re.search(r"\b(mua|bán|cần mua|tìm mua|mua bán|chuyển nhượng)\b", lower_text):
            listing_type = ListingType.SALE

        # 2. Extract Property Type
        property_type: PropertyType | None = None
        if re.search(r"\b(căn hộ|chung cư|condo|penthouse|studio)\b", lower_text):
            property_type = PropertyType.APARTMENT
        elif re.search(r"\b(nhà phố|nhà riêng|nhà hẻm|nhà mặt tiền|nhà nguyên căn)\b", lower_text):
            property_type = PropertyType.HOUSE
        elif re.search(r"\b(biệt thự|villa)\b", lower_text):
            property_type = PropertyType.VILLA
        elif re.search(r"\b(đất nền|đất thổ cư|lô đất|mảnh đất)\b", lower_text):
            property_type = PropertyType.LAND
        elif re.search(r"\b(mặt bằng|shophouse|văn phòng|thương mại|kios|ki-ốt)\b", lower_text):
            property_type = PropertyType.COMMERCIAL

        # 3. Extract Price Ranges
        min_price: float | None = None
        max_price: float | None = None

        # Case A: Billions (tỷ, tỉ)
        # Match range: "từ 2 đến 4 tỷ", "2 - 4 tỷ", "2-3 tỷ"
        range_billion_match = re.search(
            r"(?:từ\s*)?(\d+(?:[.,]\d+)?)\s*(?:đến|-)\s*(\d+(?:[.,]\d+)?)\s*(?:tỷ|tỉ)",
            lower_text,
        )
        if range_billion_match:
            v1 = float(range_billion_match.group(1).replace(",", ".")) * 1_000_000_000
            v2 = float(range_billion_match.group(2).replace(",", ".")) * 1_000_000_000
            min_price = min(v1, v2)
            max_price = max(v1, v2)
            if listing_type is None:
                listing_type = ListingType.SALE
        else:
            # Match "dưới 3 tỷ", "< 3 tỷ", "tối đa 3 tỷ", "dưới 3 tỉ"
            under_billion_match = re.search(
                r"(?:dưới|nhỏ hơn|<|tối đa|không quá)\s*(\d+(?:[.,]\d+)?)\s*(?:tỷ|tỉ)",
                lower_text,
            )
            if under_billion_match:
                max_price = float(under_billion_match.group(1).replace(",", ".")) * 1_000_000_000
                if listing_type is None:
                    listing_type = ListingType.SALE
            else:
                # Match "trên 2 tỷ", "> 2 tỷ", "từ 2 tỷ trở lên"
                above_billion_match = re.search(
                    r"(?:trên|lớn hơn|>|từ)\s*(\d+(?:[.,]\d+)?)\s*(?:tỷ|tỉ)(?:\s*trở lên)?",
                    lower_text,
                )
                if above_billion_match:
                    min_price = float(above_billion_match.group(1).replace(",", ".")) * 1_000_000_000
                    if listing_type is None:
                        listing_type = ListingType.SALE
                else:
                    # Match "khoảng 3 tỷ", "tầm 3 tỷ", "giá 3 tỷ"
                    approx_billion_match = re.search(
                        r"(?:khoảng|tầm|tầm giá|cỡ|giá)\s*(\d+(?:[.,]\d+)?)\s*(?:tỷ|tỉ)",
                        lower_text,
                    )
                    if approx_billion_match:
                        base = float(approx_billion_match.group(1).replace(",", ".")) * 1_000_000_000
                        min_price = base * 0.8
                        max_price = base * 1.2
                        if listing_type is None:
                            listing_type = ListingType.SALE

        # Case B: Millions (triệu, tr) - often rental or low price
        range_million_match = re.search(
            r"(?:từ\s*)?(\d+(?:[.,]\d+)?)\s*(?:đến|-)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)\b",
            lower_text,
        )
        if range_million_match and max_price is None:
            v1 = float(range_million_match.group(1).replace(",", ".")) * 1_000_000
            v2 = float(range_million_match.group(2).replace(",", ".")) * 1_000_000
            min_price = min(v1, v2)
            max_price = max(v1, v2)
            if listing_type is None:
                listing_type = ListingType.RENT
        elif max_price is None and min_price is None:
            under_million_match = re.search(
                r"(?:dưới|nhỏ hơn|<|tối đa|không quá)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)\b",
                lower_text,
            )
            if under_million_match:
                max_price = float(under_million_match.group(1).replace(",", ".")) * 1_000_000
                if listing_type is None:
                    listing_type = ListingType.RENT
            else:
                above_million_match = re.search(
                    r"(?:trên|lớn hơn|>|từ)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)\b(?:\s*trở lên)?",
                    lower_text,
                )
                if above_million_match:
                    min_price = float(above_million_match.group(1).replace(",", ".")) * 1_000_000
                    if listing_type is None:
                        listing_type = ListingType.RENT
                else:
                    approx_million_match = re.search(
                        r"(?:khoảng|tầm|tầm giá|cỡ|giá)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)\b",
                        lower_text,
                    )
                    if approx_million_match:
                        base = float(approx_million_match.group(1).replace(",", ".")) * 1_000_000
                        min_price = base * 0.85
                        max_price = base * 1.15
                        if listing_type is None:
                            listing_type = ListingType.RENT

        # 4. Extract Location (City & District)
        city: str | None = None
        district: str | None = None

        cities_map = {
            "hồ chí minh": "Hồ Chí Minh",
            "tp.hcm": "Hồ Chí Minh",
            "tphcm": "Hồ Chí Minh",
            "tp hcm": "Hồ Chí Minh",
            "sài gòn": "Hồ Chí Minh",
            "hà nội": "Hà Nội",
            "hn": "Hà Nội",
            "đà nẵng": "Đà Nẵng",
            "bình dương": "Bình Dương",
        }
        for k, v in cities_map.items():
            if re.search(rf"\b{re.escape(k)}\b", lower_text):
                city = v
                break

        districts_list = [
            "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6",
            "Quận 7", "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12",
            "Bình Thạnh", "Thủ Đức", "Gò Vấp", "Phú Nhuận", "Tân Bình",
            "Tân Phú", "Bình Tân", "Nhà Bè", "Hóc Môn", "Củ Chi", "Bình Chánh",
            "Cầu Giấy", "Đống Đa", "Ba Đình", "Hoàn Kiếm", "Tây Hồ",
            "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm",
            "Bắc Từ Liêm", "Hà Đông", "Hải Châu", "Thanh Khê", "Sơn Trà",
        ]
        for dist in districts_list:
            # e.g., match "quận 1" or "q1" or "bình thạnh"
            dist_pattern = rf"\b{re.escape(dist.lower())}\b"
            if re.search(dist_pattern, lower_text):
                district = dist
                if city is None:
                    if dist in ["Cầu Giấy", "Đống Đa", "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hà Đông"]:
                        city = "Hà Nội"
                    elif dist in ["Hải Châu", "Thanh Khê", "Sơn Trà"]:
                        city = "Đà Nẵng"
                    else:
                        city = "Hồ Chí Minh"
                break

        # 5. Extract Bedrooms
        min_bedrooms: int | None = None
        bed_match = re.search(r"(\d+)\s*(?:phòng ngủ|pn|bedroom)", lower_text)
        if bed_match:
            min_bedrooms = int(bed_match.group(1))

        # 6. Extract Amenities
        amenities_keywords = [
            "hồ bơi", "bể bơi", "ban công", "gym", "phòng tập",
            "nội thất", "đầy đủ nội thất", "sân vườn", "thang máy",
            "gara", "đỗ xe", "view sông", "view hồ", "công viên", "sân thượng"
        ]
        found_amenities: list[str] = []
        for am in amenities_keywords:
            if am in lower_text:
                found_amenities.append(am)

        # 7. Formulate clean raw query for hybrid semantic & fulltext search
        raw_query = text
        remove_phrases = [
            r"tôi muốn tìm", r"hãy tìm cho tôi", r"tìm giúp tôi", r"tìm cho mình",
            r"cho tôi hỏi", r"bạn ơi", r"tôi đang tìm", r"có căn nào", r"cần tìm",
        ]
        for rp in remove_phrases:
            raw_query = re.sub(rp, "", raw_query, flags=re.IGNORECASE)
        raw_query = raw_query.strip()
        if not raw_query:
            raw_query = text

        criteria = ExtractedCriteria(
            listing_type=listing_type,
            property_type=property_type,
            city=city,
            district=district,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            amenities=found_amenities,
            raw_query=raw_query,
        )

        return True, criteria

    async def execute_hybrid_search(
        self,
        db: AsyncSession,
        criteria: ExtractedCriteria,
        limit: int = 4,
    ) -> list[PropertyResponse]:
        """
        Execute Hybrid Search (pgvector vector similarity + FTS tsvector ranking)
        combined with structured filter matching for active properties.
        """
        # Formulate query text for embedding
        query_parts: list[str] = []
        if criteria.property_type:
            query_parts.append(criteria.property_type.value)
        if criteria.district:
            query_parts.append(criteria.district)
        if criteria.city:
            query_parts.append(criteria.city)
        if criteria.amenities:
            query_parts.extend(criteria.amenities)
        if criteria.raw_query:
            query_parts.append(criteria.raw_query)

        search_query_text = " ".join(query_parts).strip() or "bất động sản"

        # Generate query vector
        try:
            query_vector = self.embedding_service.generate_embedding(search_query_text, is_query=True)
        except TypeError:
            query_vector = self.embedding_service.generate_embedding(search_query_text)

        # Build filter statement
        def apply_filters(stmt):
            if criteria.listing_type:
                stmt = stmt.where(Property.listing_type == criteria.listing_type.value)
            if criteria.property_type:
                stmt = stmt.where(Property.property_type == criteria.property_type.value)
            if criteria.city:
                stmt = stmt.where(Property.city.ilike(f"%{criteria.city.strip()}%"))
            if criteria.district:
                stmt = stmt.where(Property.district.ilike(f"%{criteria.district.strip()}%"))
            if criteria.min_bedrooms is not None:
                stmt = stmt.where(Property.num_bedrooms >= criteria.min_bedrooms)
            if criteria.min_price is not None:
                stmt = stmt.where(Property.price >= criteria.min_price)
            if criteria.max_price is not None:
                stmt = stmt.where(Property.price <= criteria.max_price)
            return stmt

        # 1. Vector Search
        vector_map: dict[uuid.UUID, tuple[Property, float, int]] = {}
        try:
            cosine_dist = Property.embedding.cosine_distance(query_vector)
            vector_stmt = (
                select(Property, cosine_dist.label("distance"))
                .where(Property.status == PropertyStatus.ACTIVE.value)
                .where(Property.embedding.is_not(None))
            )
            vector_stmt = apply_filters(vector_stmt)
            vector_stmt = vector_stmt.order_by(cosine_dist.asc()).limit(max(limit * 3, 20))

            vector_res = await db.execute(vector_stmt)
            for idx, (prop_rec, dist) in enumerate(vector_res.all(), start=1):
                dist_float = float(dist) if dist is not None else 1.0
                similarity = round(1.0 - dist_float, 4)
                vector_map[prop_rec.id] = (prop_rec, similarity, idx)
        except Exception as vec_exc:
            logger.debug("Vector search execution fallback (e.g. non-pgvector dialect): %s", vec_exc)
            # Fallback for sqlite / non-pgvector test environments
            fallback_stmt = select(Property).where(Property.status == PropertyStatus.ACTIVE.value)
            fallback_stmt = apply_filters(fallback_stmt).limit(limit)
            fallback_res = await db.execute(fallback_stmt)
            return [PropertyResponse.model_validate(p) for p in fallback_res.scalars().all()]

        # 2. Full-Text Search
        fts_map: dict[uuid.UUID, tuple[Property, float, int]] = {}
        tsquery_str = _sanitize_tsquery(search_query_text)
        if tsquery_str:
            try:
                ts_vector_expr = func.to_tsvector(
                    "simple",
                    func.coalesce(Property.title, "")
                    + " "
                    + func.coalesce(Property.address, "")
                    + " "
                    + func.coalesce(Property.district, "")
                    + " "
                    + func.coalesce(Property.city, "")
                    + " "
                    + func.coalesce(Property.description, ""),
                )
                ts_query_expr = func.to_tsquery("simple", tsquery_str)
                fts_rank_expr = func.ts_rank_cd(ts_vector_expr, ts_query_expr)

                fts_stmt = (
                    select(Property, fts_rank_expr.label("fts_score"))
                    .where(Property.status == PropertyStatus.ACTIVE.value)
                    .where(ts_vector_expr.op("@@")(ts_query_expr))
                )
                fts_stmt = apply_filters(fts_stmt)
                fts_stmt = fts_stmt.order_by(fts_rank_expr.desc()).limit(max(limit * 3, 20))

                fts_res = await db.execute(fts_stmt)
                for idx, (prop_rec, score) in enumerate(fts_res.all(), start=1):
                    fts_map[prop_rec.id] = (prop_rec, float(score or 0.0), idx)
            except Exception as fts_exc:
                logger.debug("FTS search execution fallback: %s", fts_exc)

        # 3. Reciprocal Rank Fusion (RRF)
        k = 60
        all_ids = sorted(list(set(vector_map.keys()).union(fts_map.keys())), key=lambda u: str(u))
        fused: list[tuple[float, Property]] = []

        for pid in all_ids:
            prop_obj: Property | None = None
            rrf_score = 0.0

            if pid in vector_map:
                prop_obj, _, v_rank = vector_map[pid]
                rrf_score += 1.0 / (k + v_rank)

            if pid in fts_map:
                p_fts, _, f_rank = fts_map[pid]
                if prop_obj is None:
                    prop_obj = p_fts
                rrf_score += 1.0 / (k + f_rank)

            if prop_obj is not None:
                fused.append((rrf_score, prop_obj))

        fused.sort(key=lambda x: x[0], reverse=True)
        return [PropertyResponse.model_validate(p) for _, p in fused[:limit]]

    def generate_natural_response(
        self,
        criteria: ExtractedCriteria,
        properties: list[PropertyResponse],
        is_search: bool,
    ) -> tuple[str, list[str]]:
        """
        Synthesize natural, friendly Vietnamese response text along with
        contextual prompt suggestions.
        """
        if not is_search:
            welcome_msg = (
                "Xin chào! Tôi là Chuyên viên Tư vấn của Space247 🏡\n\n"
                "Tôi có thể hỗ trợ bạn tìm kiếm và chọn lọc bất động sản phù hợp nhất:\n"
                "• Tìm căn hộ hoặc nhà phố theo khoảng giá ngân sách.\n"
                "• Lọc vị trí theo Quận/Huyện, Thành phố cụ thể.\n"
                "• Tìm kiếm theo tiện ích như có hồ bơi, ban công, đầy đủ nội thất.\n\n"
                "Bạn đang quan tâm đến việc mua hay thuê bất động sản ở khu vực nào ạ?"
            )
            default_suggestions = [
                "Tìm căn hộ 2 phòng ngủ dưới 3 tỷ ở Quận 1",
                "Nhà phố cho thuê Bình Thạnh khoảng 15 triệu",
                "Biệt thự cao cấp có hồ bơi tại TP.HCM",
                "Căn hộ chung cư giá rẻ Hà Nội",
            ]
            return welcome_msg, default_suggestions

        # Search intent with matches
        criteria_tags: list[str] = []
        if criteria.listing_type == ListingType.RENT:
            criteria_tags.append("cho thuê")
        elif criteria.listing_type == ListingType.SALE:
            criteria_tags.append("bán")

        if criteria.property_type:
            type_names = {
                PropertyType.APARTMENT: "căn hộ",
                PropertyType.HOUSE: "nhà phố",
                PropertyType.VILLA: "biệt thự",
                PropertyType.LAND: "đất nền",
                PropertyType.COMMERCIAL: "mặt bằng thương mại",
            }
            criteria_tags.append(type_names.get(criteria.property_type, criteria.property_type.value))

        if criteria.district:
            criteria_tags.append(f"khu vực {criteria.district}")
        elif criteria.city:
            criteria_tags.append(f"khu vực {criteria.city}")

        if criteria.min_bedrooms:
            criteria_tags.append(f"từ {criteria.min_bedrooms} phòng ngủ")

        if criteria.max_price:
            if criteria.max_price >= 1_000_000_000:
                price_str = f"dưới {criteria.max_price / 1_000_000_000:.1f}".rstrip("0").rstrip(".") + " tỷ"
            else:
                price_str = f"dưới {criteria.max_price / 1_000_000:.0f} triệu"
            criteria_tags.append(f"mức giá {price_str}")

        criteria_desc = ", ".join(criteria_tags) if criteria_tags else "yêu cầu của bạn"

        # Check for financial / mortgage advice intent
        query_text = (criteria.raw_query or "").lower()
        financial_indicators = ["vay", "lãi suất", "trả góp", "mỗi tháng trả", "trả bao nhiêu"]
        if any(ind in query_text for ind in financial_indicators):
            loan_percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", query_text)
            loan_percent = float(loan_percent_match.group(1)) if loan_percent_match else 70.0
            down_payment_percent = max(0.0, min(100.0, 100.0 - loan_percent))

            years_match = re.search(r"(\d+)\s*năm", query_text)
            term_years = int(years_match.group(1)) if years_match else 20
            if term_years < 1 or term_years > 35:
                term_years = 20

            property_price = criteria.max_price or criteria.min_price
            if not property_price and properties:
                property_price = properties[0].price
            if not property_price:
                property_price = 3_000_000_000.0

            from src.services.mortgage_service import MortgageService
            from src.schemas.mortgage import MortgageCalcRequest, CalculationMethod

            calc_res = MortgageService.calculate_mortgage(
                MortgageCalcRequest(
                    property_price=property_price,
                    down_payment_percent=down_payment_percent,
                    loan_term_years=term_years,
                    annual_interest_rate=7.5,
                    preferential_period_months=12,
                    post_preferential_rate=10.5,
                    calculation_method=CalculationMethod.DECLINING_BALANCE,
                )
            )

            first_principal = calc_res.schedule[0].principal_payment if calc_res.schedule else 0
            first_interest = calc_res.schedule[0].interest_payment if calc_res.schedule else 0

            fin_lines = [
                "📊 **Tư vấn tài chính & Tính toán gói vay mua nhà Space247:**",
                "",
                f"Với gói vay mua nhà **{loan_percent:.0f}%** trong **{term_years} năm**:",
                f"• **Giá trị bất động sản ước tính:** {calc_res.property_price:,.0f} VND",
                f"• **Vốn tự có (trả trước {down_payment_percent:.0f}%):** {calc_res.down_payment_amount:,.0f} VND",
                f"• **Số tiền vay ngân hàng:** {calc_res.loan_amount:,.0f} VND",
                f"• **Lãi suất:** 7.5%/năm (ưu đãi 12 tháng đầu), sau ưu đãi ~10.5%/năm",
                "",
                "💰 **Ước tính số tiền thanh toán hàng tháng (theo Dư nợ giảm dần):**",
                f"• **Tháng đầu tiên (cao nhất):** **{calc_res.monthly_payment_first_month:,.0f} VND/tháng**",
                f"  (Gốc: {first_principal:,.0f} VND + Lãi: {first_interest:,.0f} VND)",
                f"• **Các tháng tiếp theo:** Số tiền trả giảm dần theo thời gian (tháng cuối chỉ còn ~{calc_res.monthly_payment_min:,.0f} VND).",
                f"• **Tổng tiền lãi cả kỳ hạn:** **{calc_res.total_interest:,.0f} VND**",
                "",
                "💡 Bạn có thể mở công cụ **Bảng tính vay mua nhà** ngay trên trang chi tiết bất động sản để tùy chỉnh các thông số lãi suất và ngân hàng!",
            ]
            fin_suggestions = [
                "🔔 Lưu tìm kiếm & Nhận cảnh báo khi có căn mới",
                "Tính theo phương án niên kim cố định (trả đều)",
                "Xem bất động sản tầm giá 3 - 5 tỷ",
            ]
            return "\n".join(fin_lines), fin_suggestions

        if properties:
            count = len(properties)
            lines = [
                f"Dạ, Space247 đã tìm thấy **{count} bất động sản** phù hợp với {criteria_desc}:",
                "",
            ]
            top = properties[0]
            price_display = f"{top.price / 1_000_000_000:.2f} tỷ" if top.price >= 1_000_000_000 else f"{top.price / 1_000_000:.1f} triệu"
            lines.append(
                f"🌟 Nổi bật có căn **{top.title}** ({top.district or ''}, {top.city}) với giá {price_display} "
                f"và diện tích {top.area_sqm}m²."
            )
            lines.append("Bạn có thể bấm vào thẻ bài đăng bên dưới để xem chi tiết ảnh và vị trí trên bản đồ nhé!")

            suggestions = [
                "🔔 Lưu tìm kiếm & Nhận cảnh báo khi có căn mới",
                "Xem thêm bất động sản cùng khu vực",
                "Lọc căn hộ giá thấp hơn",
                "Chỉ hiển thị nhà có đầy đủ nội thất",
            ]
            return "\n".join(lines), suggestions
        else:
            lines = [
                f"Rất tiếc, Space247 hiện chưa tìm thấy bất động sản nào khớp hoàn toàn với {criteria_desc}.",
                "",
                "💡 **Gợi ý cho bạn:**",
                "• Thử nới rộng khoảng giá hoặc mở rộng sang các quận/huyện lân cận.",
                "• Giảm bớt các yêu cầu về tiện ích hoặc số phòng ngủ để nhận được nhiều lựa chọn hơn.",
            ]
            suggestions = [
                "🔔 Lưu tìm kiếm & Nhận cảnh báo khi có căn mới",
                "Tìm căn hộ tầm giá 3 - 5 tỷ",
                "Xem bất động sản mới đăng gần đây",
                "Tìm nhà cho thuê giá tốt",
            ]
            return "\n".join(lines), suggestions


_chat_service: ChatAssistantService | None = None


def get_chat_assistant_service() -> ChatAssistantService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatAssistantService()
    return _chat_service
