"""
Seed script for Space247 Real Estate Platform.
Populates realistic properties across Hanoi and Ho Chi Minh City with generated 768-dim embeddings.
Can be executed via:
    uv run python -m scripts.seed_properties
"""

import asyncio
import logging
import sys
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, engine
from src.core.security import hash_password
from src.models.project import Project
from src.models.property import Property
from src.models.user import User, UserRole
from src.services.embedding import get_embedding_service

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("scripts.seed_properties")

SAMPLE_PROJECTS: list[dict[str, Any]] = [
    {
        "name": "Vinhomes Central Park",
        "slug": "vinhomes-central-park",
        "developer": "Vinhomes (Tập đoàn Vingroup)",
        "description": (
            "Đại đô thị sinh thái ven sông Sài Gòn quy mô 43.91 ha gồm 18 tòa tháp căn hộ cao cấp, "
            "quần thể biệt thự The Villas và tòa tháp Landmark 81 cao nhất Việt Nam. "
            "Dự án sở hữu công viên ven sông 14ha với hơn 40 tiện ích thể thao, hồ bơi và bến thuyền quốc tế."
        ),
        "status": "completed",
        "total_units": 10000,
        "launch_year": 2014,
        "handover_year": 2018,
        "address": "208 Nguyễn Hữu Cảnh, Phường 22",
        "ward": "Phường 22",
        "district": "Quận Bình Thạnh",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7954,
        "longitude": 106.7218,
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 5500000000.0,
        "price_range_max": 85000000000.0,
        "amenities": [
            "Công viên ven sông 14ha",
            "Tòa tháp Landmark 81",
            "Bệnh viện Đa khoa Quốc tế Vinmec",
            "Trường liên cấp quốc tế Vinschool",
            "Bến thuyền The Marina tiêu chuẩn 5 sao",
            "Hồ bơi vô cực ngoài trời",
            "TTTM Vincom Center Landmark 81",
        ],
    },
    {
        "name": "The Metropole Thủ Thiêm",
        "slug": "the-metropole-thu-thiem",
        "developer": "SonKim Land & Quốc Lộc Phát",
        "description": (
            "Khu phức hợp căn hộ, thương mại cao cấp tọa lạc tại Khu chức năng số 1 bán đảo Thủ Thiêm. "
            "Kết nối trực tiếp trung tâm Quận 1 qua cầu Ba Son. Dự án quy tụ 4 phân khu sang trọng: "
            "The Galleria, The Crest, The Opera và The Amethyst Residence cùng tầm nhìn panorama hướng sông Sài Gòn."
        ),
        "status": "handing_over",
        "total_units": 1534,
        "launch_year": 2018,
        "handover_year": 2024,
        "address": "Khu đô thị mới Thủ Thiêm, Phường An Khánh",
        "ward": "Phường An Khánh",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7725,
        "longitude": 106.7112,
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sở hữu lâu dài đối với người Việt Nam, 50 năm người nước ngoài",
        "price_range_min": 11500000000.0,
        "price_range_max": 95000000000.0,
        "amenities": [
            "Hồ bơi nước mặn 50m vô cực view trọn Quận 1",
            "Phòng gym Technogym cao cấp",
            "Sân golf giả lập 3D trong nhà",
            "Nhà hát ca vũ kịch Opera House tương lai",
            "Sảnh đón lounge sang trọng 5 sao",
            "Khu BBQ sân vườn cảnh quan",
        ],
    },
    {
        "name": "Vinhomes Grand Park",
        "slug": "vinhomes-grand-park",
        "developer": "Vinhomes (Tập đoàn Vingroup)",
        "description": (
            "Thành phố thông minh - công viên quy mô 271 ha tại TP. Thủ Đức, tích hợp đại công viên 36ha "
            "với 15 công viên chủ đề đa dạng hàng đầu Đông Nam Á, bãi biển nhân tạo cát trắng, hồ bơi resort, "
            "Vincom Mega Mall và hệ thống xe buýt điện VinBus kết nối toàn thành phố."
        ),
        "status": "completed",
        "total_units": 44000,
        "launch_year": 2019,
        "handover_year": 2022,
        "address": "Đường Nguyễn Xiển và Phước Thiện, Phường Long Bình",
        "ward": "Phường Long Bình",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8415,
        "longitude": 106.8428,
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 2100000000.0,
        "price_range_max": 38000000000.0,
        "amenities": [
            "Đại công viên ven sông 36ha với biển cát trắng",
            "Vincom Mega Mall quy mô lớn nhất miền Nam",
            "Bệnh viện Vinmec & Trường học Vinschool",
            "Khu liên hợp thể thao hơn 100 sân bãi",
            "Hệ thống xe buýt điện VinBus xanh",
            "Bến du thuyền The Manhattan Glory",
        ],
    },
    {
        "name": "Masteri Centre Point",
        "slug": "masteri-centre-point",
        "developer": "Masterise Homes",
        "description": (
            "Khu căn hộ compound cao cấp khép kín tọa lạc tại vị trí trái tim của đại đô thị Vinhomes Grand Park. "
            "Hợp tác phát triển cùng các đối tác kiến trúc và cảnh quan hàng đầu thế giới (Tange Associates, Studio HBA, Land Sculptor). "
            "Trải nghiệm sống đẳng cấp quốc tế với hệ thống an ninh 24/7 và tiện ích đặc quyền chuẩn 5 sao."
        ),
        "status": "handing_over",
        "total_units": 5099,
        "launch_year": 2020,
        "handover_year": 2023,
        "address": "Khu đô thị Vinhomes Grand Park, Phường Long Bình",
        "ward": "Phường Long Bình",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8442,
        "longitude": 106.8395,
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 3200000000.0,
        "price_range_max": 9500000000.0,
        "amenities": [
            "Hồ bơi phi thuyền Spaceship 2 tầng độc đáo",
            "Khu vui chơi trẻ em liên hoàn Play Academy",
            "Sảnh đón tiếp sang trọng chuẩn khách sạn 5 sao có Concierge",
            "Phòng gym & yoga hiện đại chuẩn quốc tế",
            "Vườn trên không Sky Garden",
            "Thác nước cảnh quan check-in nghệ thuật",
        ],
    },
    {
        "name": "Vinhomes Smart City",
        "slug": "vinhomes-smart-city",
        "developer": "Vinhomes (Tập đoàn Vingroup)",
        "description": (
            "Thành phố thông minh đẳng cấp quốc tế quy mô 280 ha tại trung tâm hành chính mới phía Tây Hà Nội. "
            "Dự án vận hành trên nền tảng 4 trục cốt lõi thông minh: An ninh thông minh, Vận hành thông minh, "
            "Cộng đồng thông minh và Căn hộ thông minh (Smart R&D). Sở hữu bộ 3 công viên liên hoàn 16.3ha cùng vườn Nhật Zen Park lớn nhất Việt Nam."
        ),
        "status": "completed",
        "total_units": 38000,
        "launch_year": 2018,
        "handover_year": 2021,
        "address": "Đại lộ Thăng Long, Phường Tây Mỗ",
        "ward": "Phường Tây Mỗ",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9998,
        "longitude": 105.7483,
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 1950000000.0,
        "price_range_max": 8800000000.0,
        "amenities": [
            "Vườn Nhật truyền thống Zen Park 6.1ha",
            "Công viên trung tâm Central Park với hồ điều hòa",
            "Công viên thể thao Sportia Park hơn 1000 máy tập",
            "Bệnh viện Vinmec & Trường học Vinschool",
            "Trung tâm thương mại Vincom Mega Mall nổi",
            "Hệ thống nhận diện khuôn mặt và an ninh AI",
        ],
    },
    {
        "name": "Vinhomes Ocean Park 1",
        "slug": "vinhomes-ocean-park",
        "developer": "Vinhomes (Tập đoàn Vingroup)",
        "description": (
            "Thành phố biển hồ quy mô 420 ha tại Gia Lâm, Hà Nội. Tái hiện không gian nghỉ dưỡng biển nhiệt đới "
            "với biển hồ nước mặn nhân tạo 6.1ha và hồ nước ngọt trung tâm 24.5ha trải cát trắng mịn. "
            "Tập trung hệ sinh thái đẳng cấp gồm Đại học VinUni, TechnoPark Tower và Vincom Mega Mall."
        ),
        "status": "completed",
        "total_units": 42000,
        "launch_year": 2018,
        "handover_year": 2020,
        "address": "Xã Đa Tốn, Huyện Gia Lâm",
        "ward": "Xã Đa Tốn",
        "district": "Huyện Gia Lâm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9926,
        "longitude": 105.9429,
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ đỏ/Sổ hồng lâu dài",
        "price_range_min": 1850000000.0,
        "price_range_max": 52000000000.0,
        "amenities": [
            "Biển hồ nước mặn 6.1ha cát trắng tự nhiên",
            "Hồ lớn trung tâm Ngọc Trai 24.5ha",
            "Tòa tháp văn phòng thông minh TechnoPark Tower",
            "Trường Đại học Quốc tế VinUni",
            "Bệnh viện Vinmec & Trường liên cấp Vinschool",
            "TTTM Vincom Mega Mall Ocean Park",
        ],
    },
]

SAMPLE_PROPERTIES: list[dict[str, Any]] = [
    # --- TP. HỒ CHÍ MINH - BÁN (SALE) ---
    {
        "title": "Căn hộ Vinhomes Central Park 2PN view trực diện sông Sài Gòn",
        "description": "Bán gấp căn hộ cao cấp 2 phòng ngủ tòa Landmark 4, full nội thất hiện đại nhập khẩu Châu Âu, view công viên và sông Sài Gòn thoáng mát. Tiện ích hồ bơi vô cực, gym, TTTM Vincom.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 6800000000.0,
        "currency": "VND",
        "area_sqm": 82.5,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "208 Nguyễn Hữu Cảnh",
        "ward": "Phường 22",
        "district": "Quận Bình Thạnh",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7954,
        "longitude": 106.7218,
        "status": "active",
        "project_slug": "vinhomes-central-park",
    },
    {
        "title": "Penthouse The Metropole Thủ Thiêm 4PN đẳng cấp giới thượng lưu",
        "description": "Tuyệt tác Penthouse The Opera Residence bán đảo Thủ Thiêm. Diện tích siêu rộng, sân vườn riêng, bể bơi panorama view trọn vẹn quận 1 và sông Sài Gòn. Bàn giao thô chuẩn quốc tế.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 65000000000.0,
        "currency": "VND",
        "area_sqm": 320.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Khu đô thị mới Thủ Thiêm",
        "ward": "Phường An Khánh",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7725,
        "longitude": 106.7112,
        "status": "active",
        "project_slug": "the-metropole-thu-thiem",
    },
    {
        "title": "Căn hộ Masteri Centre Point 2PN view trực diện đại công viên 36ha",
        "description": "Bán căn hộ Masteri Centre Point tháp Rivera trung tâm Vinhomes Grand Park. Ban công kính tràn viền view trọn vẹn công viên ánh sáng và hồ bơi phi thuyền. Bàn giao thiết bị Hafele, Kohler cao cấp.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 4500000000.0,
        "currency": "VND",
        "area_sqm": 72.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Khu đô thị Vinhomes Grand Park, Phường Long Bình",
        "ward": "Phường Long Bình",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8442,
        "longitude": 106.8395,
        "status": "active",
        "project_slug": "masteri-centre-point",
    },
    {
        "title": "Căn hộ Vinhomes Grand Park 2PN The Origami vườn Nhật độc đáo",
        "description": "Bán nhanh căn 2 phòng ngủ tòa S7 phân khu The Origami. Thiết kế cảnh quan chuẩn phong cách Nhật Bản với hồ cá Koi, vườn tùng La Hán. Đầy đủ nội thất chỉ việc xách vali vào ở.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 2850000000.0,
        "currency": "VND",
        "area_sqm": 69.5,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Phân khu The Origami, Đường Nguyễn Xiển, Phường Long Bình",
        "ward": "Phường Long Bình",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8415,
        "longitude": 106.8428,
        "status": "active",
        "project_slug": "vinhomes-grand-park",
    },
    {
        "title": "Nhà phố mặt tiền đường Phan Xích Long Phú Nhuận tiện kinh doanh",
        "description": "Nhà phố 1 trệt 4 lầu sân thượng mặt tiền phố ẩm thực Phan Xích Long sầm uất. Đang cho thuê kinh doanh chuỗi nhà hàng cao cấp với dòng tiền 90 triệu/tháng. Sổ hồng vuông vắn hoàn công đủ.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 32500000000.0,
        "currency": "VND",
        "area_sqm": 110.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "152 Phan Xích Long",
        "ward": "Phường 2",
        "district": "Quận Phú Nhuận",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7981,
        "longitude": 106.6892,
        "status": "active",
    },
    {
        "title": "Biệt thự đơn lập Chateau Phú Mỹ Hưng ven sông yên tĩnh",
        "description": "Biệt thự lâu đài đơn lập khu Chateau đẳng cấp bậc nhất Nam Sài Gòn. Kiến trúc cổ điển bán cổ điển châu Âu, hồ bơi sân vườn cảnh quan riêng biệt, an ninh 3 lớp tuyệt đối 24/7.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 115000000000.0,
        "currency": "VND",
        "area_sqm": 580.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "Khu biệt thự lâu đài Chateau, Nguyễn Lương Bằng",
        "ward": "Phường Tân Phú",
        "district": "Quận 7",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7186,
        "longitude": 106.7259,
        "status": "active",
    },
    {
        "title": "Căn hộ Masteri Thảo Điền 3PN view hồ bơi và xa lộ Hà Nội",
        "description": "Bán căn góc 3 phòng ngủ Masteri Thảo Điền lầu cao thoáng mát, liền kề ga Metro số 1 Bến Thành - Suối Tiên, siêu thị Mega Market, trường quốc tế BIS. Pháp lý rõ ràng, sẵn sàng công chứng.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 7200000000.0,
        "currency": "VND",
        "area_sqm": 94.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "159 Xa lộ Hà Nội",
        "ward": "Phường Thảo Điền",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8032,
        "longitude": 106.7412,
        "status": "active",
    },
    {
        "title": "Nhà phố liền kề Lakeview City Nam Rạch Chiếc Thủ Đức",
        "description": "Nhà phố thương mại 1 trệt 3 lầu hoàn thiện cao cấp tại KĐT sinh thái Lakeview City. Hồ cảnh quan rộng 3.6ha, không gian sống xanh trong lành, bảo vệ nghiêm ngặt 24/7.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 16800000000.0,
        "currency": "VND",
        "area_sqm": 125.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Khu đô thị Lakeview City, Song Hành Cao Tốc",
        "ward": "Phường An Phú",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7923,
        "longitude": 106.7721,
        "status": "active",
    },
    {
        "title": "Tòa nhà mặt tiền văn phòng đường Pasteur Quận 3 vị trí đắc địa",
        "description": "Bán tòa nhà văn phòng 1 hầm 8 tầng thang máy mặt tiền Pasteur trung tâm Quận 3. Diện tích sàn sử dụng 850m2, đầy đủ PCCC chuẩn nghiệm thu mới nhất, giấy phép xây dựng hoàn chỉnh.",
        "property_type": "commercial",
        "listing_type": "sale",
        "price": 88000000000.0,
        "currency": "VND",
        "area_sqm": 180.0,
        "num_bedrooms": None,
        "num_bathrooms": 8,
        "address": "214 Pasteur",
        "ward": "Phường Võ Thị Sáu",
        "district": "Quận 3",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7845,
        "longitude": 106.6914,
        "status": "active",
    },

    # --- TP. HỒ CHÍ MINH - CHO THUÊ (RENT) ---
    {
        "title": "Căn hộ Vinhomes Central Park 1PN Landmark Plus đầy đủ tiện nghi",
        "description": "Cho thuê căn hộ dịch vụ 1 phòng ngủ tháp Landmark Plus Vinhomes Central Park. Trang bị đầy đủ máy giặt, sấy, lò vi sóng, dịch vụ dọn phòng theo tiêu chuẩn khách sạn 5 sao. Miễn phí gym và hồ bơi.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 18500000.0,
        "currency": "VND",
        "area_sqm": 54.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Tòa Landmark Plus, 208 Nguyễn Hữu Cảnh",
        "ward": "Phường 22",
        "district": "Quận Bình Thạnh",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7954,
        "longitude": 106.7218,
        "status": "active",
        "project_slug": "vinhomes-central-park",
    },
    {
        "title": "Căn hộ The Metropole Thủ Thiêm 2PN The Galleria view sông Sài Gòn",
        "description": "Cho thuê căn hộ cao cấp 2 phòng ngủ phân khu The Galleria Residence. Ban công rộng view trực diện cầu Ba Son và sông Sài Gòn. Nội thất bàn giao chuẩn Châu Âu sang trọng.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 42000000.0,
        "currency": "VND",
        "area_sqm": 85.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "The Galleria, Khu đô thị mới Thủ Thiêm",
        "ward": "Phường An Khánh",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7725,
        "longitude": 106.7112,
        "status": "active",
        "project_slug": "the-metropole-thu-thiem",
    },
    {
        "title": "Căn hộ Studio Vinhomes Grand Park The Rainbow đầy đủ tiện nghi",
        "description": "Cho thuê căn hộ Studio phân khu The Rainbow Vinhomes Grand Park. Nội thất decor trẻ trung hiện đại, máy lạnh Inverter, tủ lạnh, máy giặt. Tiện ích công viên cầu vồng, hồ bơi ngoài trời.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 6500000.0,
        "currency": "VND",
        "area_sqm": 33.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Phân khu The Rainbow, Vinhomes Grand Park",
        "ward": "Phường Long Bình",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8415,
        "longitude": 106.8428,
        "status": "active",
        "project_slug": "vinhomes-grand-park",
    },
    {
        "title": "Cho thuê căn hộ dịch vụ 1PN đường Lê Thánh Tôn Quận 1 khu phố Nhật",
        "description": "Studio/căn hộ dịch vụ 1 phòng ngủ đầy đủ nội thất cao cấp ngay trung tâm phố Nhật Little Tokyo Lê Thánh Tôn. Đã bao gồm dịch vụ dọn phòng, giặt ủi, internet tốc độ cao.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 18000000.0,
        "currency": "VND",
        "area_sqm": 45.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "15B Lê Thánh Tôn",
        "ward": "Phường Bến Nghé",
        "district": "Quận 1",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7812,
        "longitude": 106.7045,
        "status": "active",
    },
    {
        "title": "Căn hộ The Sun Avenue 2PN Mai Chí Thọ nội thất đẹp giá tốt",
        "description": "Cho thuê chung cư The Sun Avenue 2 phòng ngủ 2WC đầy đủ sofa, giường tủ, máy lạnh, tủ lạnh, bếp từ. Tiện ích hồ bơi tràn bờ, siêu thị, trường học, di chuyển sang quận 1 chỉ 10 phút.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 15000000.0,
        "currency": "VND",
        "area_sqm": 76.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "28 Mai Chí Thọ",
        "ward": "Phường An Phú",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7863,
        "longitude": 106.7554,
        "status": "active",
    },
    {
        "title": "Biệt thự sân vườn Thảo Điền Quận 2 có hồ bơi riêng biệt lập",
        "description": "Cho thuê biệt thự nghỉ dưỡng cao cấp tại Thảo Điền diện tích khuôn viên 450m2. Thiết kế hiện đại mở, 4 phòng ngủ ensuite, sân vườn rộng nhiều cây xanh, gara ô tô rộng rãi.",
        "property_type": "villa",
        "listing_type": "rent",
        "price": 95000000.0,
        "currency": "VND",
        "area_sqm": 450.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "42 Nguyễn Văn Hưởng",
        "ward": "Phường Thảo Điền",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8124,
        "longitude": 106.7328,
        "status": "active",
    },
    {
        "title": "Mặt bằng kinh doanh tầng trệt mặt tiền đường Nguyễn Huệ Quận 1",
        "description": "Cho thuê mặt bằng thương mại phố đi bộ Nguyễn Huệ, vị trí vàng lưu lượng khách du lịch đông đúc. Thích hợp mở showroom thương hiệu thời trang, cà phê hoặc nhà hàng cao cấp.",
        "property_type": "commercial",
        "listing_type": "rent",
        "price": 180000000.0,
        "currency": "VND",
        "area_sqm": 160.0,
        "num_bedrooms": None,
        "num_bathrooms": 2,
        "address": "68 Nguyễn Huệ",
        "ward": "Phường Bến Nghé",
        "district": "Quận 1",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7742,
        "longitude": 106.7031,
        "status": "active",
    },
    {
        "title": "Căn hộ Sunrise City 3PN Quận 7 view Nguyễn Hữu Thọ",
        "description": "Cho thuê dài hạn căn hộ Sunrise City South Towers 3 phòng ngủ đầy đủ nội thất sang trọng. Đối diện Lotte Mart Quận 7, liền kề trường RMIT, Tôn Đức Thắng.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 26000000.0,
        "currency": "VND",
        "area_sqm": 120.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "23 Nguyễn Hữu Thọ",
        "ward": "Phường Tân Hưng",
        "district": "Quận 7",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7431,
        "longitude": 106.7011,
        "status": "active",
    },
    {
        "title": "Nhà nguyên căn hẻm xe hơi đường Cách Mạng Tháng 8 Quận 10",
        "description": "Cho thuê nhà 1 trệt 2 lầu đúc kiên cố hẻm xe hơi thông thoáng gần ngã sáu Dân Chủ. Phù hợp làm văn phòng công ty nhỏ, kinh doanh online kết hợp ở gia đình.",
        "property_type": "house",
        "listing_type": "rent",
        "price": 28000000.0,
        "currency": "VND",
        "area_sqm": 85.0,
        "num_bedrooms": 3,
        "num_bathrooms": 3,
        "address": "382 Cách Mạng Tháng 8",
        "ward": "Phường 11",
        "district": "Quận 10",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7788,
        "longitude": 106.6781,
        "status": "active",
    },

    # --- HÀ NỘI - BÁN (SALE) ---
    {
        "title": "Căn hộ Vinhomes Metropolis Liễu Giai 2PN view hồ Tây tuyệt đẹp",
        "description": "Bán căn hộ cao cấp Vinhomes Metropolis 29 Liễu Giai, tầng trung thoáng mát, tầm nhìn trực diện Hồ Tây lộng gió. Nội thất ngoại nhập cao cấp, cạnh đại sứ quán Nhật và TTTM Lotte.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 9800000000.0,
        "currency": "VND",
        "area_sqm": 78.5,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "29 Liễu Giai",
        "ward": "Phường Ngọc Khánh",
        "district": "Quận Ba Đình",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0331,
        "longitude": 105.8152,
        "status": "active",
    },
    {
        "title": "Nhà phố cổ Hàng Bông Hoàn Kiếm mặt tiền kinh doanh du lịch",
        "description": "Bán nhà mặt phố Hàng Bông vị trí kim cương phố cổ Hà Nội. Diện tích 75m2 xây 5 tầng có thang máy, đang kinh doanh khách sạn boutique mini và đồ lưu niệm lưu lượng khách Tây sầm uất.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 62000000000.0,
        "currency": "VND",
        "area_sqm": 75.0,
        "num_bedrooms": 6,
        "num_bathrooms": 6,
        "address": "118 Hàng Bông",
        "ward": "Phường Hàng Bông",
        "district": "Quận Hoàn Kiếm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0308,
        "longitude": 105.8457,
        "status": "active",
    },
    {
        "title": "Biệt thự Vinhomes Riverside Long Biên hoa hồng phong cách Venice",
        "description": "Biệt thự đơn lập khu Hoa Hồng Vinhomes Riverside, sông đào nhân tạo bao quanh nhà, sân vườn tiểu cảnh cá Koi tuyệt đẹp. Hệ sinh thái tiện ích chuẩn 5 sao quốc tế.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 78000000000.0,
        "currency": "VND",
        "area_sqm": 410.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "Khu đô thị Vinhomes Riverside, Chu Huy Mân",
        "ward": "Phường Phúc Đồng",
        "district": "Quận Long Biên",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0452,
        "longitude": 105.9084,
        "status": "active",
    },
    {
        "title": "Căn hộ chung cư D'Capitale Trần Duy Hưng 3PN nội thất tân cổ điển",
        "description": "Bán căn góc 3 ngủ D'Capitale ngã tư Trần Duy Hưng - Khuất Duy Tiến. Tầm nhìn thoáng ra công viên hồ điều hòa Nhân Chính, giao thông kết nối thuận tiện và đầy đủ tiện ích.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 6500000000.0,
        "currency": "VND",
        "area_sqm": 95.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "119 Trần Duy Hưng",
        "ward": "Phường Trung Hòa",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0063,
        "longitude": 105.7951,
        "status": "active",
    },
    {
        "title": "Nhà liền kề KĐT Starlake Tây Hồ Tây đẳng cấp kiểu Hàn Quốc",
        "description": "Bán nhà liền kề phân khu H7 KĐT Starlake Tây Hồ Tây. Xây dựng 4 tầng kiến trúc sang trọng hiện đại, gần hồ Tây và các đại sứ quán, cộng đồng cư dân quốc tế trí thức cao.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 46000000000.0,
        "currency": "VND",
        "area_sqm": 132.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Khu đô thị Starlake Tây Hồ Tây",
        "ward": "Phường Xuân Tảo",
        "district": "Quận Bắc Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0612,
        "longitude": 105.7983,
        "status": "active",
    },
    {
        "title": "Căn hộ Vinhomes Smart City Tây Mỗ 1PN+ giá hợp lý",
        "description": "Căn hộ 1PN+1 tòa Tonkin Vinhomes Smart City phân khu cao cấp nhất dự án. Thiết kế thông minh tối ưu diện tích, vườn phong cách Nhật, hồ bơi bốn mùa trong nhà.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 2650000000.0,
        "currency": "VND",
        "area_sqm": 48.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Khu đô thị Vinhomes Smart City, Đại lộ Thăng Long",
        "ward": "Phường Tây Mỗ",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9998,
        "longitude": 105.7483,
        "status": "active",
        "project_slug": "vinhomes-smart-city",
    },
    {
        "title": "Căn hộ Vinhomes Ocean Park 2PN góc view hồ nước ngọt Ngọc Trai 24.5ha",
        "description": "Bán căn góc 2 phòng ngủ tòa S2.05 phân khu Sapphire Vinhomes Ocean Park Gia Lâm. Tầng trung ban công đón gió view trực diện biển hồ nước mặn và hồ lớn Ngọc Trai. Đã có sổ đỏ lâu dài.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 3150000000.0,
        "currency": "VND",
        "area_sqm": 66.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Phân khu Sapphire, Khu đô thị Vinhomes Ocean Park",
        "ward": "Xã Đa Tốn",
        "district": "Huyện Gia Lâm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9926,
        "longitude": 105.9429,
        "status": "active",
        "project_slug": "vinhomes-ocean-park",
    },
    {
        "title": "Tòa nhà căn hộ dịch vụ phố Đội Cấn Ba Đình 8 tầng dòng tiền khủng",
        "description": "Bán tòa nhà 8 tầng thang máy phố Đội Cấn gồm 16 phòng studio cho khách Nhật Bản và chuyên gia nước ngoài thuê full phòng, doanh thu đạt 120 triệu/tháng. Sổ đỏ vuông vắn.",
        "property_type": "commercial",
        "listing_type": "sale",
        "price": 29500000000.0,
        "currency": "VND",
        "area_sqm": 90.0,
        "num_bedrooms": 16,
        "num_bathrooms": 16,
        "address": "285 Đội Cấn",
        "ward": "Phường Liễu Giai",
        "district": "Quận Ba Đình",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0365,
        "longitude": 105.8198,
        "status": "active",
    },

    # --- HÀ NỘI - CHO THUÊ (RENT) ---
    {
        "title": "Căn hộ Vinhomes Smart City 2PN Sapphire 2 đầy đủ nội thất",
        "description": "Cho thuê chung cư 2 phòng ngủ 2WC phân khu Sapphire 2 Vinhomes Smart City. Nhà mới tinh full nội thất cao cấp xách vali vào ở ngay. Hưởng trọn tiện ích công viên thể thao Sportia Park và vườn Nhật.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 11500000.0,
        "currency": "VND",
        "area_sqm": 64.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Phân khu Sapphire 2, KĐT Vinhomes Smart City",
        "ward": "Phường Tây Mỗ",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9998,
        "longitude": 105.7483,
        "status": "active",
        "project_slug": "vinhomes-smart-city",
    },
    {
        "title": "Căn hộ Vinhomes Ocean Park 1PN tòa Zenpark tiện nghi chuẩn Nhật",
        "description": "Cho thuê căn hộ 1 phòng ngủ cao cấp phân khu The Zenpark Ruby Vinhomes Ocean Park. Tiêu chuẩn bàn giao thông minh, điều hòa âm trần Daikin, sàn gỗ, sảnh đón lễ tân sang trọng, view vườn Nhật nội khu.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 8500000.0,
        "currency": "VND",
        "area_sqm": 45.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Tòa R1.02 The Zenpark, Vinhomes Ocean Park",
        "ward": "Xã Đa Tốn",
        "district": "Huyện Gia Lâm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9926,
        "longitude": 105.9429,
        "status": "active",
        "project_slug": "vinhomes-ocean-park",
    },
    {
        "title": "Căn hộ cao cấp Ciputra Tây Hồ 3PN view sân golf thoáng đãng",
        "description": "Cho thuê căn hộ khu đô thị Ciputra Nam Thăng Long, 3 phòng ngủ đầy đủ tiện nghi Châu Âu sang trọng. Không gian yên tĩnh trong lành, nhiều trường quốc tế UNIS, SIS, Hanoi Academy.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 35000000.0,
        "currency": "VND",
        "area_sqm": 145.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "Khu đô thị Ciputra, Lạc Long Quân",
        "ward": "Phường Xuân La",
        "district": "Quận Tây Hồ",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0768,
        "longitude": 105.8052,
        "status": "active",
    },
    {
        "title": "Cho thuê biệt thự khu đô thị Ngoại Giao Đoàn Bắc Từ Liêm",
        "description": "Biệt thự đơn lập 350m2 đất KĐT Ngoại Giao Đoàn, hoàn thiện cơ bản có thang máy và điều hòa trung tâm. Rất phù hợp làm văn phòng đại diện ngoại giao hoặc trụ sở công ty công nghệ.",
        "property_type": "villa",
        "listing_type": "rent",
        "price": 75000000.0,
        "currency": "VND",
        "area_sqm": 350.0,
        "num_bedrooms": 5,
        "num_bathrooms": 5,
        "address": "Khu Ngoại Giao Đoàn, Xuân Tảo",
        "ward": "Phường Xuân Tảo",
        "district": "Quận Bắc Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0658,
        "longitude": 105.7994,
        "status": "active",
    },
    {
        "title": "Studio view trọn vẹn Hồ Tây phố Quảng An Tây Hồ cho người nước ngoài",
        "description": "Cho thuê căn hộ studio dịch vụ khép kín phố Quảng An, ban công lớn ngắm hoàng hôn Hồ Tây thơ mộng. Khu vực tập trung nhiều chuyên gia nước ngoài, nhiều quán cafe ven hồ chill.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 14000000.0,
        "currency": "VND",
        "area_sqm": 42.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "36 Quảng An",
        "ward": "Phường Quảng An",
        "district": "Quận Tây Hồ",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0621,
        "longitude": 105.8284,
        "status": "active",
    },
    {
        "title": "Căn hộ Vinhomes Times City 2PN Minh Khai Hai Bà Trưng",
        "description": "Cho thuê căn hộ 2 phòng ngủ Park Hill Times City đầy đủ đồ đạc hiện đại, chỉ việc xách vali vào ở. Miễn phí sử dụng bể bơi, sân tennis, gần bệnh viện Vinmec và trường học Vinschool.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 16500000.0,
        "currency": "VND",
        "area_sqm": 75.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "458 Minh Khai",
        "ward": "Phường Vĩnh Tuy",
        "district": "Quận Hai Bà Trưng",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9945,
        "longitude": 105.8687,
        "status": "active",
    },
    {
        "title": "Mặt bằng kinh doanh thời trang phố Bà Triệu Hoàn Kiếm",
        "description": "Cho thuê mặt bằng tầng 1 phố mua sắm thời trang Bà Triệu, vỉa hè rộng rãi có chỗ đỗ ô tô và xe máy. Diện tích vuông vức, mặt tiền 6m cực đẹp, hệ thống chiếu sáng có sẵn.",
        "property_type": "commercial",
        "listing_type": "rent",
        "price": 65000000.0,
        "currency": "VND",
        "area_sqm": 80.0,
        "num_bedrooms": None,
        "num_bathrooms": 1,
        "address": "126 Bà Triệu",
        "ward": "Phường Nguyễn Du",
        "district": "Quận Hai Bà Trưng",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0189,
        "longitude": 105.8498,
        "status": "active",
    },
    {
        "title": "Nhà riêng 4 tầng ngõ ô tô đường Hoàng Quốc Việt Cầu Giấy",
        "description": "Cho thuê nhà riêng 4 tầng ngõ rộng ô tô tránh nhau đường Hoàng Quốc Việt. Khu dân trí cao, an ninh tốt, thích hợp vừa ở gia đình vừa làm trung tâm đào tạo hoặc văn phòng đại diện.",
        "property_type": "house",
        "listing_type": "rent",
        "price": 22000000.0,
        "currency": "VND",
        "area_sqm": 68.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "106 Hoàng Quốc Việt",
        "ward": "Phường Nghĩa Đô",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0471,
        "longitude": 105.7998,
        "status": "active",
    },
    {
        "title": "Căn hộ Discovery Complex Cầu Giấy 3PN rộng rãi kết nối Metro",
        "description": "Cho thuê căn hộ cao cấp Discovery Complex 302 Cầu Giấy, 3 phòng ngủ 2 vệ sinh view toàn cảnh quận Cầu Giấy. Tòa nhà có TTTM Lotte Cinema, phòng tập California Fitness & Yoga.",
        "property_type": "apartment",
        "listing_type": "rent",
        "price": 25000000.0,
        "currency": "VND",
        "area_sqm": 148.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "302 Cầu Giấy",
        "ward": "Phường Dịch Vọng",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0345,
        "longitude": 105.7925,
        "status": "active",
    },
    {
        "title": "Văn phòng trọn gói tầng cao tòa nhà Keangnam Landmark 72 Phạm Hùng",
        "description": "Cho thuê diện tích văn phòng chuyên nghiệp tầng 32 Keangnam Landmark 72 biểu tượng của Hà Nội. Đầy đủ sàn thảm, trần thạch cao, điều hòa trung tâm thông minh, view toàn cảnh thủ đô.",
        "property_type": "commercial",
        "listing_type": "rent",
        "price": 120000000.0,
        "currency": "VND",
        "area_sqm": 220.0,
        "num_bedrooms": None,
        "num_bathrooms": 4,
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng",
        "ward": "Phường Mễ Trì",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0169,
        "longitude": 105.7839,
        "status": "active",
    },
    # --- ĐẤT NỀN (LAND) ---
    {
        "title": "Đất nền thổ cư ven sông Quận 9 TP Thủ Đức view thoáng mát",
        "description": "Bán lô đất nền thổ cư 100% sổ hồng riêng, vị trí đắc địa gần khu công nghệ cao và cao tốc Long Thành Dầu Giây. Hạ tầng đồng bộ đường nhựa 12m, điện nước âm hoàn thiện.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 4200000000.0,
        "currency": "VND",
        "area_sqm": 120.0,
        "num_bedrooms": None,
        "num_bathrooms": None,
        "address": "Đường Lã Xuân Oai",
        "ward": "Phường Tăng Nhơn Phú A",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8415,
        "longitude": 106.7992,
        "status": "active",
    },
    {
        "title": "Đất đấu giá phân lô khu đô thị mới Đông Anh Hà Nội",
        "description": "Chính chủ cần bán mảnh đất đấu giá vuông vắn, mặt tiền 6m đường rộng 2 ô tô tránh nhau. Vị trí gần chân cầu Nhật Tân, tiềm năng tăng giá vượt trội khi lên quận.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 5600000000.0,
        "currency": "VND",
        "area_sqm": 90.0,
        "num_bedrooms": None,
        "num_bathrooms": None,
        "address": "Xã Vĩnh Ngọc",
        "ward": "Xã Vĩnh Ngọc",
        "district": "Huyện Đông Anh",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0924,
        "longitude": 105.8198,
        "status": "active",
    },
]


DEFAULT_SEED_USERS = [
    {
        "email": "admin@space247.vn",
        "full_name": "Quản Trị Viên Space247",
        "phone": "0901234567",
        "password": "Password123@",
        "role": UserRole.ADMIN.value,
    },
    {
        "email": "agent@space247.vn",
        "full_name": "Môi Giới Chuyên Nghiệp Space247",
        "phone": "0988889999",
        "password": "Password123@",
        "role": UserRole.AGENT.value,
    },
    {
        "email": "user@space247.vn",
        "full_name": "Khách Hàng Mẫu Space247",
        "phone": "0912345678",
        "password": "Password123@",
        "role": UserRole.USER.value,
    },
]


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """
    Seed default users (admin and agent) idempotently.
    Returns a dictionary of email -> User model instances.
    """
    user_map: dict[str, User] = {}
    for item in DEFAULT_SEED_USERS:
        email = item["email"]
        stmt = select(User).where(User.email == email)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            user_map[email] = existing
            logger.info("Found existing seed user: %s (role: %s)", email, existing.role)
        else:
            new_user = User(
                email=email,
                hashed_password=hash_password(item["password"]),
                full_name=item["full_name"],
                phone=item["phone"],
                role=item["role"],
                is_active=True,
            )
            session.add(new_user)
            await session.flush()
            user_map[email] = new_user
            logger.info("Created new seed user: %s (role: %s)", email, item["role"])

    return user_map


async def seed_projects(
    session: AsyncSession,
    projects_data: list[dict[str, Any]] | None = None,
    embedding_svc: Any = None,
) -> dict[str, Any]:
    """
    Seed real estate projects idempotently into the database.
    Computes 768-dim vector embeddings and PostGIS geometries for spatial and semantic search.
    """
    items_to_seed = projects_data if projects_data is not None else SAMPLE_PROJECTS
    if embedding_svc is None:
        embedding_svc = get_embedding_service()

    project_map: dict[str, Project] = {}
    stats = {"total": len(items_to_seed), "created": 0, "skipped": 0}

    # Ensure projects.geom exists if database was created prior to spatial column addition
    try:
        await session.execute(
            text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);")
        )
        await session.execute(
            text("CREATE INDEX IF NOT EXISTS ix_projects_geom ON projects USING gist (geom);")
        )
        await session.commit()
    except Exception as exc:
        await session.rollback()
        logger.debug("Schema verification for projects.geom finished: %s", exc)

    logger.info("Starting project seeding: %d projects to process...", len(items_to_seed))

    for idx, item in enumerate(items_to_seed, start=1):
        slug = item["slug"]
        stmt = select(Project).where(Project.slug == slug)
        res = await session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            project_map[slug] = existing
            logger.info("[%d/%d] Skipping existing project: '%s' (slug: %s)", idx, len(items_to_seed), item["name"], slug)
            stats["skipped"] += 1
            continue

        p_data = dict(item)
        if "id" not in p_data:
            p_data["id"] = uuid4()

        # Build text to embed
        text_content = (
            f"Dự án {item.get('name', '')}. "
            f"Chủ đầu tư: {item.get('developer', '')}. "
            f"Địa chỉ: {item.get('address', '')}, {item.get('district', '')}, {item.get('city', '')}. "
            f"Tiện ích: {', '.join(item.get('amenities', []))}. "
            f"{item.get('description', '')}"
        )
        p_data["embedding"] = embedding_svc.generate_embedding(text_content, is_query=False)

        if item.get("latitude") is not None and item.get("longitude") is not None:
            p_data["geom"] = f"SRID=4326;POINT({item['longitude']} {item['latitude']})"

        proj = Project(**p_data)
        session.add(proj)
        await session.flush()
        project_map[slug] = proj
        stats["created"] += 1
        logger.info(
            "[%d/%d] Created project: '%s' (%s - %s)",
            idx,
            len(items_to_seed),
            item["name"],
            item.get("developer"),
            item.get("city"),
        )

    await session.commit()
    logger.info(
        "Project seeding finished: %d created, %d skipped, %d total.",
        stats["created"],
        stats["skipped"],
        stats["total"],
    )
    return {
        "total": stats["total"],
        "created": stats["created"],
        "skipped": stats["skipped"],
        "project_map": project_map,
    }


async def seed_properties(
    session: AsyncSession,
    properties_data: list[dict[str, Any]] | None = None,
    embedding_svc=None,
    owner_user_id=None,
    project_map: dict[str, Project] | None = None,
) -> dict[str, int]:
    """
    Seed property records idempotently into the database.
    Checks existing records by title to avoid duplicating data.
    Associates properties to parent projects when project_slug is provided.
    """
    items_to_seed = properties_data if properties_data is not None else SAMPLE_PROPERTIES
    if embedding_svc is None:
        embedding_svc = get_embedding_service()

    stats = {"total": len(items_to_seed), "created": 0, "skipped": 0}

    logger.info("Starting property seeding: %d items to process...", len(items_to_seed))

    for idx, item in enumerate(items_to_seed, start=1):
        title = item["title"]
        project_slug = item.get("project_slug")
        target_project_id = None

        if project_slug:
            if project_map and project_slug in project_map:
                target_project_id = project_map[project_slug].id
            else:
                stmt_proj = select(Project.id).where(Project.slug == project_slug)
                res_proj = await session.execute(stmt_proj)
                target_project_id = res_proj.scalars().first()

        # 1. Check for existing property with identical title
        stmt = select(Property).where(Property.title == title)
        res = await session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            if target_project_id and existing.project_id is None:
                existing.project_id = target_project_id
                logger.info(
                    "[%d/%d] Linked existing property '%s' to project_id: %s",
                    idx,
                    len(items_to_seed),
                    title,
                    target_project_id,
                )
            logger.info("[%d/%d] Skipping existing property: '%s'", idx, len(items_to_seed), title)
            stats["skipped"] += 1
            continue

        # 2. Build metadata text and generate dense 768-dim vector embedding
        text_to_embed = embedding_svc.build_property_text(
            title=item.get("title", ""),
            property_type=item.get("property_type", ""),
            listing_type=item.get("listing_type", ""),
            price=item.get("price"),
            currency=item.get("currency", "VND"),
            area_sqm=item.get("area_sqm"),
            num_bedrooms=item.get("num_bedrooms"),
            num_bathrooms=item.get("num_bathrooms"),
            address=item.get("address", ""),
            ward=item.get("ward", ""),
            district=item.get("district", ""),
            city=item.get("city", ""),
            description=item.get("description", ""),
        )

        vector_embedding = embedding_svc.generate_embedding(text_to_embed, is_query=False)

        # 3. Create Property ORM instance
        prop_data = dict(item)
        if "project_slug" in prop_data:
            del prop_data["project_slug"]
        if target_project_id:
            prop_data["project_id"] = target_project_id
        if "id" not in prop_data:
            prop_data["id"] = uuid4()
        prop_data["embedding"] = vector_embedding
        if owner_user_id and "user_id" not in prop_data:
            prop_data["user_id"] = owner_user_id

        prop = Property(**prop_data)
        session.add(prop)
        stats["created"] += 1
        logger.info(
            "[%d/%d] Created property: '%s' (%s, %s, %s, project_id: %s)",
            idx,
            len(items_to_seed),
            title,
            item.get("property_type"),
            item.get("listing_type"),
            item.get("city"),
            target_project_id,
        )

    await session.commit()
    logger.info(
        "Property seeding finished: %d created, %d skipped, %d total.",
        stats["created"],
        stats["skipped"],
        stats["total"],
    )
    return stats


async def reindex_all_vectors(session: AsyncSession) -> int:
    """Recompute 768-dim embeddings for all existing properties in database."""
    embedding_svc = get_embedding_service()
    stmt = select(Property)
    res = await session.execute(stmt)
    properties = res.scalars().all()
    logger.info("Found %d properties to reindex vectors...", len(properties))

    updated_count = 0
    for idx, prop in enumerate(properties, start=1):
        text_to_embed = embedding_svc.build_property_text(
            title=prop.title or "",
            property_type=prop.property_type or "",
            listing_type=prop.listing_type or "",
            price=float(prop.price) if prop.price is not None else None,
            currency=prop.currency or "VND",
            area_sqm=prop.area_sqm,
            num_bedrooms=prop.num_bedrooms,
            num_bathrooms=prop.num_bathrooms,
            address=prop.address or "",
            ward=prop.ward or "",
            district=prop.district or "",
            city=prop.city or "",
            description=prop.description or "",
        )
        prop.embedding = embedding_svc.generate_embedding(text_to_embed, is_query=False)
        updated_count += 1
        if idx % 10 == 0 or idx == len(properties):
            logger.info("Reindexed [%d/%d] properties...", idx, len(properties))

    await session.commit()
    logger.info("Vector re-indexing completed successfully: %d properties updated.", updated_count)
    return updated_count


async def main():
    """CLI runner entry point."""
    is_reindex_mode = "--reindex-vectors" in sys.argv
    logger.info("Initializing database connection for Space247 (reindex_mode=%s)...", is_reindex_mode)
    try:
        async with AsyncSessionLocal() as session:
            try:
                if is_reindex_mode:
                    logger.info("--- Batch Vector Re-indexing Triggered ---")
                    count = await reindex_all_vectors(session=session)
                    logger.info("[Space247 Reindex Summary] Reindexed %d properties.", count)
                    return

                # 1. Seed users first
                logger.info("--- Step 1: Seeding Default Accounts ---")
                user_map = await seed_users(session=session)
                agent_user = user_map.get("agent@space247.vn")
                agent_id = agent_user.id if agent_user else None

                # 2. Seed real estate projects
                logger.info("--- Step 2: Seeding Real Estate Projects with Master Plans & Embeddings ---")
                proj_res = await seed_projects(session=session)
                logger.info(
                    "[Space247 Project Seed Summary] Total: %d | Created: %d | Skipped: %d",
                    proj_res["total"],
                    proj_res["created"],
                    proj_res["skipped"],
                )

                # 3. Seed properties linked to agent and projects
                logger.info("--- Step 3: Seeding Properties Linked to Projects ---")
                stats = await seed_properties(
                    session=session,
                    owner_user_id=agent_id,
                    project_map=proj_res["project_map"],
                )
                logger.info(
                    "[Space247 Property Seed Summary] Total: %d | Created: %d | Skipped: %d",
                    stats["total"],
                    stats["created"],
                    stats["skipped"],
                )
            except Exception as exc:
                await session.rollback()
                logger.exception("Error during database operation: %s", exc)
                sys.exit(1)
    finally:
        await engine.dispose()


def run_seed():
    """Synchronous entry point for console scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    run_seed()
