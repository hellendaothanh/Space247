import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AIComparisonService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = genai.Client()
        self.model_name = "gemini-3.5-flash"
    
    async def generate_comparison(self, properties: list[dict]) -> str:
        prompt = self._build_prompt(properties)
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
            properties_text += f"- Loại: {p.get('property_type', 'N/A')} - {p.get('listing_type', 'N/A')}\n"
            properties_text += f"- Mô tả: {p.get('description', '')}\n"

        return f"""Bạn là một chuyên gia bất động sản. Hãy so sánh các bất động sản sau đây dựa trên 4 tiêu chí cốt lõi:
1. Chi phí (Cost) - so sánh giá tổng và giá trên mét vuông.
2. Vị trí (Location) - đánh giá tiện ích và khu vực.
3. Tiềm năng đầu tư (Investment potential) - khả năng sinh lời hoặc thanh khoản.
4. Pháp lý/An toàn (Legal/safety) - các rủi ro có thể có.

Sau khi phân tích 4 tiêu chí, hãy đưa ra khuyến nghị (Recommendation) nên chọn bất động sản nào cho mục đích gì.
Định dạng câu trả lời bằng Markdown. Bắt buộc bằng tiếng Việt.

Thông tin các bất động sản:
{properties_text}
"""

    def _get_fallback_markdown(self, properties: list[dict]) -> str:
        return """## So sánh Bất động sản (Dự phòng)

Hệ thống AI hiện đang bận hoặc không khả dụng. Tuy nhiên, bạn có thể xem các thông số cơ bản ở bảng so sánh.

### Các tiêu chí cần lưu ý:
- **Chi phí**: Xem xét giá tổng và giá/m² để so sánh độ đắt rẻ.
- **Vị trí**: Đánh giá sự thuận tiện giao thông và tiện ích xung quanh.
- **Tiềm năng đầu tư**: Tùy thuộc vào khu vực và khả năng cho thuê hoặc tăng giá.
- **Pháp lý/An toàn**: Luôn kiểm tra sổ đỏ/sổ hồng và quy hoạch trước khi giao dịch.

*Vui lòng thử lại sau để xem phân tích chi tiết từ AI.*"""
