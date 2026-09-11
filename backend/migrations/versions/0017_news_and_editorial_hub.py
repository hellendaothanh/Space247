"""Create news_categories and articles tables with seed data.

Revision ID: 0017
Revises: 0016
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create news_categories table
    op.create_table(
        "news_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_news_categories_slug", "news_categories", ["slug"], unique=True)

    # 2. Create articles table
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=True)
    op.create_index("ix_articles_category_id", "articles", ["category_id"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])

    # 3. Create full-text GIN search index on articles
    try:
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_articles_fts ON articles
            USING gin(to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')));
        """)
    except Exception:
        pass

    # 4. Seed categories
    cat_market_id = str(uuid.uuid4())
    cat_project_id = str(uuid.uuid4())
    cat_finance_id = str(uuid.uuid4())
    cat_fengshui_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc).isoformat()

    op.execute(f"""
        INSERT INTO news_categories (id, name, slug, description, icon, display_order, created_at, updated_at)
        VALUES
        ('{cat_market_id}', 'Thị trường BĐS', 'thi-truong-bds', 'Báo cáo thị trường, xu hướng đơn giá, biến động thanh khoản và chính sách vĩ mô.', 'TrendingUp', 1, '{now}', '{now}'),
        ('{cat_project_id}', 'Dự án & Quy hoạch', 'du-an-quy-hoach', 'Tiến độ đại đô thị, tuyến hạ tầng giao thông trọng điểm và quy hoạch đô thị.', 'Building2', 2, '{now}', '{now}'),
        ('{cat_finance_id}', 'Tài chính & Ngân hàng', 'tai-chinh-ngan-hang', 'Cẩm nang lãi suất vay mua nhà, giải pháp đòn bẩy tài chính và tính toán dòng tiền.', 'Landmark', 3, '{now}', '{now}'),
        ('{cat_fengshui_id}', 'Phong thủy & Không gian sống', 'phong-thuy-nha-o', 'Kiến thức phong thủy vượng khí, cẩm nang bài trí hướng nhà và thiết kế sống xanh.', 'Compass', 4, '{now}', '{now}')
        ON CONFLICT (slug) DO NOTHING;
    """)

    # 5. Seed Articles (7 realistic articles)
    articles_seed = [
        (
            str(uuid.uuid4()),
            "Xu hướng giá căn hộ chung cư Hà Nội và TP.HCM quý 3/2026: Phân khúc nào dẫn sóng?",
            "xu-huong-gia-can-ho-chung-cu-ha-noi-va-tphcm-quy-3-2026",
            "Phân tích chuyên sâu từ Space247 Intelligence về biến động đơn giá trung bình căn hộ cao cấp và dòng sản phẩm phục vụ nhu cầu ở thực.",
            """## Toàn cảnh thị trường căn hộ 2026

Thị trường bất động sản quý 3/2026 ghi nhận bước chuyển mình mạnh mẽ về thanh khoản tại cả hai đầu tàu kinh tế là Hà Nội và Thành phố Hồ Chí Minh. Các dự án sở hữu pháp lý minh bạch và hạ tầng kết nối trực tiếp vào tuyến đường sắt đô thị (Metro) tiếp tục giữ vị thế dẫn sóng tăng trưởng.

### 1. Phân khúc căn hộ cao cấp tại khu Đông TP.HCM
Tại TP. Thủ Đức, mặt bằng giá thứ cấp căn hộ The River Thủ Thiêm, Metropole và Masteri Centre Point duy trì đà tăng trưởng bền vững 8-12% so với cùng kỳ năm trước. Lực cầu chủ yếu đến từ cộng đồng chuyên gia công nghệ và các nhà đầu tư dài hạn ưu tiên dòng tiền cho thuê ổn định.

### 2. Sức hút bất động sản ven trục Metro số 1 & số 2
Hạ tầng giao thông vận hành trơn tru đã rút ngắn đáng kể thời gian di chuyển từ các quận vệ tinh vào trung tâm. Điều này mở ra cơ hội vàng cho các gia đình trẻ an cư với tầm tài chính từ 3 đến 5 tỷ đồng.

> **Khuyến nghị từ chuyên gia Space247:** Người mua ở thực nên ưu tiên các dự án đã bàn giao có ban quản lý chuyên nghiệp, tỷ lệ lấp đầy cư dân trên 70% để đảm bảo giá trị thanh khoản cao nhất.
""",
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
            cat_market_id,
            ["thị trường", "giá căn hộ", "metro", "đầu tư 2026"],
            1420,
        ),
        (
            str(uuid.uuid4()),
            "Tuyến Metro Bến Thành - Suối Tiên tạo động lực tăng giá khu Đông Sài Gòn ra sao?",
            "tuyen-metro-ben-thanh-suoi-tien-tao-dong-luc-tang-gia-khu-dong",
            "Đánh giá tác động hạ tầng giao thông đường sắt đô thị tới tiềm năng tăng giá bất động sản dọc tuyến Xa Lộ Hà Nội và TP. Thủ Đức.",
            """## Cú hích hạ tầng đường sắt đô thị Metro số 1

Việc đưa vào khai thác thương mại toàn tuyến Metro số 1 Bến Thành - Suối Tiên không chỉ giải quyết bài toán ùn tắc giao thông mà còn tái định hình bản đồ giá trị bất động sản khu vực phía Đông TP. Hồ Chí Minh.

### Khoảng cách đi bộ (Transit-Oriented Development - TOD)
Các dự án bất động sản nằm trong bán kính đi bộ 500m - 800m từ các nhà ga như Ga Thảo Điền, Ga An Phú, Ga Bình Thái ghi nhận mức chênh lệch giá bán từ 15% đến 25% so với các dự án ở vị trí xa hơn.

- **Ga Thảo Điền:** Trung tâm F&B quốc tế, cộng đồng expat sầm uất.
- **Ga Bình Thái & Thủ Đức:** Điểm đến an cư lý tưởng cho kỹ sư khu công nghệ cao.

Hạ tầng đồng bộ chính là bảo chứng an toàn nhất cho dòng tiền của nhà đầu tư qua các chu kỳ thị trường.
""",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            cat_project_id,
            ["quy hoạch", "metro thủ đức", "hạ tầng giao thông"],
            2180,
        ),
        (
            str(uuid.uuid4()),
            "Cẩm nang gói vay mua nhà năm 2026: So sánh lãi suất ưu đãi giữa các ngân hàng lớn",
            "cam-nang-goi-vay-mua-nha-nam-2026-so-sanh-lai-suat-ngan-hang",
            "Tổng hợp chi tiết lãi suất vay thế chấp từ Big 4 và các ngân hàng thương mại cổ phần, hướng dẫn cân đối đòn bẩy tài chính không quá 50% thu nhập.",
            """## Chiến lược vay mua nhà an toàn năm 2026

Lãi suất cho vay mua nhà năm 2026 duy trì ở mức ổn định, tạo điều kiện thuận lợi cho các gia đình trẻ tiếp cận nguồn vốn ưu đãi để sở hữu tổ ấm đầu tiên.

### So sánh các gói lãi suất vay tiêu biểu
1. **Khối ngân hàng quốc doanh (Vietcombank, BIDV, VietinBank):**
   - Lãi suất cố định 2 năm đầu từ 6.0% - 6.8%/năm.
   - Biên độ thả nổi sau ưu đãi: LSCS + 3.0% - 3.5%.
2. **Khối ngân hàng TMCP (Techcombank, MB, VPBank):**
   - Thời gian ân hạn nợ gốc linh hoạt lên tới 36 tháng.
   - Thời gian vay kéo dài tối đa 35 năm giúp giảm tải áp lực trả góp hàng tháng.

### Công thức an toàn tài chính 50/30/20
Chuyên gia khuyến nghị: Tổng khoản trả góp lãi và gốc hàng tháng không nên vượt quá **40% - 50% tổng thu nhập khả dụng** của gia đình. Bạn có thể sử dụng công cụ *Bảng tính vay mua nhà* tích hợp sẵn trên Space247 để mô phỏng lịch trả nợ chi tiết trước khi đặt cọc.
""",
            "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80",
            cat_finance_id,
            ["vay mua nhà", "lãi suất ngân hàng", "tài chính cá nhân"],
            3540,
        ),
        (
            str(uuid.uuid4()),
            "Phong thủy căn hộ chung cư: Cách chọn hướng ban công đón tài lộc và tránh phạm kỵ",
            "phong-thuy-can-ho-chung-cu-cach-chon-huong-ban-cong-tai-loc",
            "Hướng dẫn xem hướng nhà chung cư chuẩn phong thủy hiện đại, xử lý xung sát cửa chính đối diện thang máy và tối ưu ánh sáng tự nhiên.",
            """## Xem phong thủy căn hộ chung cư đúng cách

Trong kiến trúc đô thị cao tầng, cách xác định hướng nhà cho căn hộ chung cư có sự khác biệt rõ rệt so với nhà mặt đất truyền thống.

### 1. Hướng cửa chính hay hướng ban công?
Theo quan điểm phong thủy năng lượng hiện đại, ban công và phòng khách là nơi tiếp nhận nguồn năng lượng dương (khí, gió trời, ánh sáng mặt trời) nhiều nhất cho toàn bộ không gian sống. Vì vậy, hướng view ban công chính đóng vai trò cốt lõi trong việc điều hòa sinh khí.

### 2. Các hướng ban công vượng khí
- **Ban công hướng Nam / Đông Nam:** Đón gió mát mùa hè, tránh nắng gắt buổi chiều, mang lại sự ôn hòa, sức khỏe dồi dào.
- **Xử lý ban công hướng Tây:** Trồng các tầng cây xanh lọc nhiệt hoặc lắp đặt hệ lam chắn nắng thông minh để hóa giải hỏa khí.

### 3. Tránh các thế phạm kỵ thường gặp
- Cửa chính đâm thẳng vào cửa thang máy hoặc hành lang chung kéo dài.
- Cửa nhà vệ sinh đối diện trực diện với khu vực nấu bếp.
""",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            cat_fengshui_id,
            ["phong thủy", "hướng nhà", "không gian sống"],
            1890,
        ),
        (
            str(uuid.uuid4()),
            "Đại đô thị sinh thái thông minh: Xu hướng định hình phong cách sống thế hệ mới",
            "dai-do-thi-sinh-thai-thong-minh-xu-huong-dinh-hinh-phong-cach-song",
            "Vì sao các khu đô thị tích hợp đa tiện ích all-in-one kề cận sông hồ tự nhiên đang trở thành lựa chọn số một của giới chuyên gia và trí thức.",
            """## Mô hình khu đô thị All-in-one

Mô hình khu đô thị tích hợp đa tầng tiện ích \"City-within-a-City\" đang là xu hướng chủ đạo trong chiến lược phát triển của các chủ đầu tư hàng đầu tại Việt Nam.

### Tiêu chuẩn sống xanh và bền vững
Không chỉ dừng lại ở mật độ cây xanh, các đại đô thị mới áp dụng tiêu chuẩn năng lượng xanh, hệ thống hồ điều hòa tự nhiên hàng chục hecta và công nghệ quản lý vận hành IoT 24/7.

- **Tiện ích trường học - bệnh viện - trung tâm thương mại** chỉ cách ngưỡng cửa vài bước chân.
- **Hệ sinh thái thể thao ngoài trời:** Đường chạy bộ ven sông, sân pickleball, bể bơi muối khoáng.
""",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            cat_market_id,
            ["sống xanh", "đại đô thị", "wellness", "xu hướng 2026"],
            1650,
        ),
        (
            str(uuid.uuid4()),
            "Đầu tư Shophouse khối đế và Nhà phố kinh doanh: Bí quyết tính tỷ suất hoàn vốn ROI",
            "dau-tu-shophouse-khoi-de-va-nha-pho-kinh-doanh-tinh-ty-suat-roi",
            "Phương pháp thẩm định lưu lượng khách bộ hành, chi phí cải tạo mặt bằng và bài toán dòng tiền cho thuê đạt trên 6%/năm.",
            """## Bài toán đầu tư bất động sản dòng tiền

Bất động sản thương mại như Shophouse chân đế chung cư và nhà phố mặt tiền thương mại luôn đòi hỏi khả năng thẩm định khắt khe hơn bất động sản để ở thuần túy.

### 1. Đánh giá lưu lượng cư dân nội khu
Một căn Shophouse thành công phụ thuộc 80% vào số lượng cư dân sinh sống ổn định ngay tại tòa tháp và lưu lượng khách vãng lai di chuyển qua trục đường chính.

### 2. Công thức tính tỷ suất sinh lời thực tế (Cap Rate)
$$\\text{ROI (\\%)} = \\frac{\\text{Doanh thu cho thuê thuần 1 năm}}{\\text{Tổng vốn đầu tư}} \\times 100$$

Một mặt bằng được đánh giá là sinh lời hấp dẫn khi đạt tỷ suất cho thuê thuần từ 5.5% đến 7.5%/năm kèm biên độ tăng giá vốn 8-10%/năm của tài sản đất nền.
""",
            "https://images.unsplash.com/photo-1582407947304-fd86f028f716?auto=format&fit=crop&w=1200&q=80",
            cat_finance_id,
            ["shophouse", "dòng tiền", "đầu tư", "roi"],
            2890,
        ),
        (
            str(uuid.uuid4()),
            "Bản đồ quy hoạch giao thông Hà Nội đến năm 2030: Những trục mở rộng chiến lược",
            "ban-do-quy-hoach-giao-thong-ha-noi-den-nam-2030",
            "Cập nhật tiến độ đường Vành đai 4 Vùng Thủ đô, các cây cầu mới qua sông Hồng và tiềm năng bứt phá của bất động sản vùng phụ cận.",
            """## Tầm nhìn quy hoạch giao thông Thủ đô

Hà Nội đang đẩy nhanh tốc độ giải phóng mặt bằng và thi công các dự án giao thông động lực, đưa mô hình chùm đô thị đa cực vào thực tế.

### Các trục hạ tầng then chốt
- **Đường Vành đai 4:** Tạo hành lang kinh tế liên kết Hà Nội - Hưng Yên - Bắc Ninh.
- **Hệ thống cầu vượt sông Hồng:** Cầu Tứ Liên, Cầu Trần Hưng Đạo mở toang cánh cửa kết nối khu Đông và khu Bắc sông Hồng vào lõi trung tâm Hoàn Kiếm.
""",
            "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
            cat_project_id,
            ["quy hoạch hà nội", "vành đai 4", "cầu tứ liên"],
            1980,
        )
    ]

    for art_id, title, slug, summary, content, thumbnail_url, cat_id, tags_list, views in articles_seed:
        tags_sql = "{" + ",".join(f'"{t}"' for t in tags_list) + "}"
        # Escape single quotes in strings
        title_esc = title.replace("'", "''")
        slug_esc = slug.replace("'", "''")
        summary_esc = summary.replace("'", "''")
        content_esc = content.replace("'", "''")
        op.execute(f"""
            INSERT INTO articles (
                id, title, slug, summary, content, thumbnail_url,
                category_id, author_id, tags, view_count, is_published,
                published_at, created_at, updated_at
            )
            VALUES (
                '{art_id}', '{title_esc}', '{slug_esc}', '{summary_esc}', '{content_esc}',
                '{thumbnail_url}',
                '{cat_id}', NULL, '{tags_sql}', {views}, true,
                '{now}', '{now}', '{now}'
            )
            ON CONFLICT (slug) DO NOTHING;
        """)


def downgrade() -> None:
    op.drop_table("articles")
    op.drop_table("news_categories")
