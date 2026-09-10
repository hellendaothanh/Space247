import logging
import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.property import Property
from src.schemas.chat import (
    ChatMessage,
    ChatRole,
    ExtractedCriteria,
    LivingCostBreakdown,
    LivingCostItem,
)
from src.schemas.property import (
    ListingType,
    PropertyResponse,
    PropertyStatus,
    PropertyType,
)
from src.services.embedding import EmbeddingService, get_embedding_service

from src.services.rental import apply_rental_filters, resolve_landmark

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
            "phòng trọ", "ở ghép", "gác", "loft", "pet", "tìm", "mua", "bán", "thuê", "căn hộ", "chung cư", "nhà", "biệt thự",
            "villa", "đất", "mặt bằng", "quận", "huyện", "phòng ngủ", "tỷ", "tỉ",
            "triệu", "triệu/tháng", "tr/tháng", "diện tích", "hồ bơi", "ban công",
            "nội thất", "hà nội", "hồ chí minh", "đà nẵng", "quận 1", "bình thạnh",
            "vay", "lãi suất", "trả góp", "mỗi tháng trả", "ngân hàng",
            "dự án", "chủ đầu tư", "master plan", "khu đô thị", "tiện ích dự án",
            "chi phí", "sinh hoạt", "tiền điện", "tiền nước", "mỗi tháng hết", "mỗi tháng tốn",
            "tổng chi phí", "người ở", "kwh", "bao nhiêu tiền",
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
        explicit_listing_type = listing_type

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

        # 6.5 Extract Project Name
        project_name: str | None = None
        proj_match = re.search(r"(?:dự án|khu đô thị|khu dân cư)\s+([a-zA-Z0-9À-ỹ\s]+?)(?=\s+(?:ở|tại|quận|huyện|thành phố|giá|có|diện tích|khoảng|tầm|$))", text, re.IGNORECASE)
        if proj_match:
            project_name = proj_match.group(1).strip()

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
            project_name=project_name,
            raw_query=raw_query,
        )

        rental_types = {"phòng trọ": "room", "căn hộ dịch vụ": "serviced_apartment", "ở ghép": "house_share", "nguyên căn": "entire_house"}
        for phrase, subtype in rental_types.items():
            if phrase in lower_text:
                criteria.rental_type = subtype
                criteria.listing_type = ListingType.RENT
        if "gác" in lower_text or "mezzanine" in lower_text or "loft" in lower_text:
            criteria.has_mezzanine = not bool(re.search(r"(?:không|cấm)\s+(?:có\s+|cần\s+)?(?:gác|mezzanine|loft)", lower_text))
            criteria.listing_type = ListingType.RENT
        if any(x in lower_text for x in ("thú cưng", "nuôi mèo", "nuôi chó", "pet")):
            criteria.allow_pets = not bool(re.search(r"(?:không|cấm)\s+(?:cho\s+)?(?:phép\s+)?(?:nuôi\s+)?(?:thú cưng|chó|mèo|pets?)", lower_text))
            criteria.listing_type = ListingType.RENT
        if "điện" in lower_text and any(x in lower_text for x in ("nhà nước", "giá dân", "bậc thang")):
            criteria.electricity_billing = "state_rate"
            criteria.listing_type = ListingType.RENT
        deposit = re.search(r"cọc\s*(?:tối đa|không quá|dưới)?\s*(\d+(?:[.,]\d+)?)\s*tháng", lower_text)
        if deposit:
            criteria.max_deposit = float(deposit.group(1).replace(",", "."))
        if any(phrase in lower_text for phrase in ("giờ tự do", "giờ giấc tự do", "không giới nghiêm")):
            criteria.curfew = False
        if "máy giặt" in lower_text:
            criteria.has_washing_machine = not bool(re.search(r"không\s+(?:có\s+|cần\s+)?máy giặt", lower_text))
        if "không chung chủ" in lower_text:
            criteria.live_with_owner = False
        landmark = re.search(r"(?:gần|quanh|xung quanh)\s+(.+?)(?=\s+(?:giá|dưới|có|không|cho|tầm|khoảng)|[,.;]|$)", text, re.I)
        if landmark:
            criteria.near_landmark = landmark.group(1).strip()
        if explicit_listing_type == ListingType.SALE:
            # Rental-only metadata must not turn a purchase into contradictory filters.
            criteria.listing_type = ListingType.SALE
            for key in ("rental_type", "allow_pets", "has_mezzanine", "has_washing_machine", "live_with_owner", "curfew", "electricity_billing", "max_deposit"):
                setattr(criteria, key, None)
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
        if criteria.near_landmark:
            query_parts.append(criteria.near_landmark)

        search_query_text = " ".join(query_parts).strip() or "bất động sản"

        # Generate query vector
        try:
            query_vector = self.embedding_service.generate_embedding(search_query_text, is_query=True)
        except TypeError:
            query_vector = self.embedding_service.generate_embedding(search_query_text)

        coordinates = await resolve_landmark(criteria)

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
            return apply_rental_filters(stmt, criteria, coordinates)

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

    @classmethod
    def calculate_total_living_cost(
        cls,
        occupants: int = 2,
        room_price: float = 3_500_000.0,
        electricity_kwh: float = 150.0,
        water_usage: float = 2.0,
        property_costs: dict | None = None,
    ) -> LivingCostBreakdown:
        """
        Calculate complete monthly living expense breakdown for prospective tenants.
        Incorporates property specific shared_costs or falls back to standard city rates.
        """
        costs = property_costs or {}

        # 1. Room fee
        room_item = LivingCostItem(
            category="Tiền phòng",
            unit_price=room_price,
            quantity=1.0,
            unit_label="tháng",
            subtotal=room_price,
            note="Giá thuê cơ sở",
        )

        # 2. Electricity
        elec_rate = float(costs.get("electricity_per_kwh") or 3500.0)
        elec_subtotal = electricity_kwh * elec_rate
        elec_item = LivingCostItem(
            category="Tiền điện",
            unit_price=elec_rate,
            quantity=electricity_kwh,
            unit_label="kWh",
            subtotal=elec_subtotal,
            note=f"Định mức ước tính {electricity_kwh:.0f} kWh/tháng",
        )

        # 3. Water
        water_unit = str(costs.get("water_unit") or "m3")
        water_cost_rate = float(costs.get("water_cost") or (25000.0 if water_unit == "m3" else 100000.0))
        if water_unit == "per_person":
            water_qty = float(occupants)
            water_subtotal = water_qty * water_cost_rate
            water_label = "người"
        else:
            water_qty = water_usage
            water_subtotal = water_qty * water_cost_rate
            water_label = "m³"

        water_item = LivingCostItem(
            category="Tiền nước",
            unit_price=water_cost_rate,
            quantity=water_qty,
            unit_label=water_label,
            subtotal=water_subtotal,
            note=f"Tính theo {water_label}",
        )

        # 4. Service / Internet / Sanitation
        service_fee = float(costs.get("service_fee_monthly") or costs.get("wifi_fee") or 150000.0)
        service_item = LivingCostItem(
            category="Phí dịch vụ & Internet",
            unit_price=service_fee,
            quantity=1.0,
            unit_label="tháng",
            subtotal=service_fee,
            note="Wifi, vệ sinh, bảo trì chung",
        )

        # 5. Parking (optional estimate)
        parking_per_bike = float(costs.get("parking_fee_monthly") or 120000.0)
        parking_bikes = float(occupants)
        parking_subtotal = parking_bikes * parking_per_bike
        parking_item = LivingCostItem(
            category="Gửi xe",
            unit_price=parking_per_bike,
            quantity=parking_bikes,
            unit_label="xe",
            subtotal=parking_subtotal,
            note=f"{occupants} xe máy",
        )

        items = [room_item, elec_item, water_item, service_item, parking_item]
        total_monthly_cost = sum(it.subtotal for it in items)
        cost_per_person = total_monthly_cost / occupants if occupants > 0 else total_monthly_cost

        summary_lines = [
            f"| Khoản mục | Đơn giá | Số lượng | Thành tiền |",
            f"| :--- | :--- | :--- | :--- |",
            f"| 🏠 Tiền phòng | {room_price:,.0f} đ/tháng | 1 tháng | **{room_price:,.0f} đ** |",
            f"| ⚡ Tiền điện | {elec_rate:,.0f} đ/kWh | {electricity_kwh:.0f} kWh | **{elec_subtotal:,.0f} đ** |",
            f"| 💧 Tiền nước | {water_cost_rate:,.0f} đ/{water_label} | {water_qty:.1f} {water_label} | **{water_subtotal:,.0f} đ** |",
            f"| 📶 Dịch vụ & Wifi | {service_fee:,.0f} đ/tháng | 1 gói | **{service_fee:,.0f} đ** |",
            f"| 🛵 Gửi xe | {parking_per_bike:,.0f} đ/xe | {parking_bikes:.0f} xe | **{parking_subtotal:,.0f} đ** |",
            f"| **TỔNG CỘNG** | | | **{total_monthly_cost:,.0f} đ/tháng** |",
            f"| **BÌNH QUÂN** | Cho {occupants} người | | **{cost_per_person:,.0f} đ/người/tháng** |",
        ]

        return LivingCostBreakdown(
            room_price=room_price,
            occupants=occupants,
            electricity_kwh=electricity_kwh,
            water_usage=water_qty,
            water_unit=water_unit,
            items=items,
            total_monthly_cost=total_monthly_cost,
            cost_per_person=cost_per_person,
            summary="\n".join(summary_lines),
        )

    @classmethod
    def detect_and_calculate_living_cost(
        cls,
        messages: list[ChatMessage],
        properties: list[PropertyResponse] | None = None,
    ) -> LivingCostBreakdown | None:
        """
        Scan messages for living cost queries and extract parameters (occupants, kWh, price).
        """
        if not messages:
            return None

        combined_text = " ".join([m.content for m in messages if m.role in ("user", ChatRole.USER.value)]).lower()
        living_indicators = ["chi phí", "sinh hoạt", "mỗi tháng hết", "mỗi tháng tốn", "tổng chi phí", "tiền điện", "tiền nước", "người ở", "hết bao nhiêu tiền", "hết bao nhiêu"]
        if not any(ind in combined_text for ind in living_indicators):
            return None

        # 1. Extract occupants
        occupants = 2
        occ_match = re.search(r"(\d+)\s*(?:người|bạn|thành viên|khách|ng)", combined_text)
        if occ_match:
            try:
                val = int(occ_match.group(1))
                if 1 <= val <= 20:
                    occupants = val
            except (ValueError, TypeError):
                pass

        # 2. Extract electricity usage
        electricity_kwh = 150.0
        elec_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kwh|kw|số điện|ký điện)", combined_text)
        if elec_match:
            try:
                electricity_kwh = float(elec_match.group(1).replace(",", "."))
            except (ValueError, TypeError):
                pass

        # 3. Extract water usage
        water_usage = 2.0 * occupants
        water_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m3|khối|khối nước)", combined_text)
        if water_match:
            try:
                water_usage = float(water_match.group(1).replace(",", "."))
            except (ValueError, TypeError):
                pass

        # 4. Extract room price
        room_price = 3_500_000.0
        if properties and len(properties) > 0:
            room_price = float(properties[0].price)
        else:
            # Check price in query e.g. "phòng 4 triệu", "giá 3.5 tr"
            price_match = re.search(r"(?:phòng|giá|thuê)\s*(\d+(?:[.,]\d+)?)\s*(?:triệu|tr)", combined_text)
            if price_match:
                try:
                    room_price = float(price_match.group(1).replace(",", ".")) * 1_000_000
                except (ValueError, TypeError):
                    pass

        prop_costs = None
        if properties and len(properties) > 0:
            top_prop = properties[0]
            if top_prop.rental_costs:
                prop_costs = top_prop.rental_costs.model_dump()

        return cls.calculate_total_living_cost(
            occupants=occupants,
            room_price=room_price,
            electricity_kwh=electricity_kwh,
            water_usage=water_usage,
            property_costs=prop_costs,
        )

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

        # Check for living cost calculation intent
        query_text = (criteria.raw_query or "").lower()
        living_indicators = ["chi phí", "sinh hoạt", "mỗi tháng hết", "mỗi tháng tốn", "tổng chi phí", "tiền điện", "tiền nước", "người ở", "hết bao nhiêu tiền", "hết bao nhiêu"]
        if any(ind in query_text for ind in living_indicators) and any(w in query_text for w in ["bao nhiêu", "chi phí", "mỗi tháng", "tính", "hết"]):
            breakdown = self.detect_and_calculate_living_cost([ChatMessage(role="user", content=criteria.raw_query)], properties)
            if breakdown:
                cost_lines = [
                    f"📊 **Bảng dự toán chi phí sinh hoạt hàng tháng ({breakdown.occupants} người ở):**",
                    "",
                    breakdown.summary,
                    "",
                    f"💡 **Tổng chi phí ước tính:** **{breakdown.total_monthly_cost:,.0f} VND/tháng** (bình quân **{breakdown.cost_per_person:,.0f} VND/người/tháng**).",
                    "Chi phí thực tế sẽ phụ thuộc vào số ký điện và khối nước sử dụng thực tế của bạn trong tháng.",
                ]
                cost_suggestions = [
                    "Tính chi phí cho 1 người ở",
                    "Tính chi phí cho 3 người ở",
                    "Xem chi tiết nội quy và giờ giấc khu trọ",
                    "Đặt lịch hẹn xem phòng trực tiếp",
                ]
                return "\n".join(cost_lines), cost_suggestions

        # Check for financial / mortgage advice intent
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
