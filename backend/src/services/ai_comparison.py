import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class AIComparisonService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client with provided key: {e}")
                self.client = None
        else:
            logger.info("GEMINI_API_KEY not configured. AIComparisonService will use structured fallback mode.")

    async def generate_comparison(self, properties: list[dict]) -> str:
        if not self.client:
            return self._get_fallback_markdown(properties)

        prompt = self._build_prompt(properties)
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                ),
            )
            if response and response.text:
                return response.text
            return self._get_fallback_markdown(properties)
        except Exception as e:
            logger.error(f"Gemini API error during property comparison: {e}")
            return self._get_fallback_markdown(properties)

    def _build_prompt(self, properties: list[dict]) -> str:
        properties_text = ""
        for i, p in enumerate(properties, 1):
            properties_text += f"\nBất động sản {i}:\n"
            properties_text += f"- Tên: {p.get('title', 'N/A')}\n"
            properties_text += f"- Giá: {p.get('price', 0):,.0f} VND\n"
            properties_text += f"- Diện tích: {p.get('area_sqm', 0)} m²\n"
            properties_text += f"- Giá/m²: {p.get('price_per_sqm', 0):,.0f} VND/m²\n"
            properties_text += f"- Vị trí: {p.get('address', 'N/A')}\n"
            properties_text += f"- Loại hình: {p.get('property_type', 'N/A')} - {p.get('listing_type', 'N/A')}\n"
            properties_text += f"- Mô tả: {p.get('description', '')}\n"

        return f"""Bạn là một chuyên gia tư vấn đầu tư bất động sản cao cấp của Space247. Hãy so sánh các bất động sản sau đây một cách khách quan, chuyên sâu theo đúng 4 tiêu chí cốt lõi:

1. **Đơn giá & Hiệu quả chi phí**: So sánh giá tổng, đơn giá trên từng mét vuông (VNĐ/m²), tính tương xứng giữa giá bán và diện tích.
2. **Vị trí & Tiện ích xung quanh**: Đánh giá vị trí địa lý, khả năng kết nối giao thông, hạ tầng và tiện ích khu vực lân cận.
3. **Tiềm năng đầu tư & Tăng giá**: Phân tích tiềm năng tăng giá trị trong tương lai, khả năng khai thác cho thuê và tính thanh khoản.
4. **Tính pháp lý & Mức độ an toàn**: Đánh giá mức độ an toàn giao dịch, hồ sơ pháp lý cần lưu ý.

Sau cùng, hãy đưa ra **Bảng đối chiếu tóm tắt** và **Khuyến nghị chuyên gia (Recommendation)**: Từng căn phù hợp với đối tượng nào (đầu tư dài hạn, lướt sóng, khai thác dòng tiền hay an cư thực tế).

Định dạng kết quả bằng Markdown chuyên nghiệp, rõ ràng, gạch đầu dòng mạch lạc. Bắt buộc bằng tiếng Việt.

Thông tin các bất động sản cần so sánh:
{properties_text}
"""

    def _get_fallback_markdown(self, properties: list[dict]) -> str:
        prop_summaries = []
        for i, p in enumerate(properties, 1):
            title = p.get('title', f'Bất động sản #{i}')
            price = p.get('price', 0)
            area = p.get('area_sqm', 0)
            price_m2 = p.get('price_per_sqm', 0)
            addr = p.get('address', 'Chưa cập nhật')
            prop_summaries.append(
                f"- **{title}**: Giá {price:,.0f} đ ({area} m² - {price_m2:,.0f} đ/m²), tọa lạc tại {addr}."
            )

        props_list_md = "\n".join(prop_summaries)

        return f"""### 📊 Báo cáo Nhận định So sánh Bất động sản (Chế độ Dự phòng)

Hệ thống AI hiện đang xử lý ở chế độ an toàn cục bộ (thiếu `GEMINI_API_KEY` hoặc phản hồi từ Google AI bị gián đoạn). Dưới đây là tóm lược phân tích kỹ thuật dựa trên dữ liệu hệ thống:

#### 1. Tổng hợp các bất động sản đối chiếu:
{props_list_md}

#### 2. Phân tích 4 tiêu chí cốt lõi:
- **Đơn giá & Hiệu quả chi phí**: Căn có đơn giá/m² thấp hơn thường mang lại hiệu quả chi phí trên diện tích sử dụng tốt hơn. Hãy cân nhắc tỷ trọng ngân sách đầu tư ban đầu so với diện tích thực tế.
- **Vị trí & Tiện ích**: Các vị trí gần trục đường lớn, trường học, bệnh viện và khu dân cư hiện hữu luôn giữ được thanh khoản cao hơn.
- **Tiềm năng đầu tư**: Xem xét quy hoạch tương lai xung quanh từng khu vực (cầu, đường vành đai, tuyến metro).
- **Pháp lý & An toàn**: Đảm bảo kiểm tra kỹ sổ hồng/sổ đỏ, quy hoạch phân khu và hiện trạng tài sản trước khi tiến hành đặt cọc.

💡 *Gợi ý: Cấu hình biến môi trường `GEMINI_API_KEY` trong tệp `.env` để kích hoạt phân tích chuyên sâu chi tiết từ Gemini 3.5 Flash.*
"""
