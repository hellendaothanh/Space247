"""
Comprehensive Seed script for Space247 Real Estate Platform.
Populates realistic properties, major projects, boarding houses, serviced apartments,
sample contracts, monthly invoices, and booking inquiries across Vietnam
(Hà Nội, Quảng Ninh, Hải Phòng, Đà Nẵng, Nha Trang, TP.HCM, Bình Dương, Cần Thơ, Phú Quốc)
with 768-dimensional dense vector embeddings and PostGIS geometries.

Can be executed via:
    uv run python -m scripts.seed_properties
    uv run python -m scripts.seed_properties --reindex-vectors
"""

import asyncio
from datetime import datetime, timezone, timedelta
import logging
import sys
from typing import Any
from uuid import uuid4

from geoalchemy2 import WKTElement
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, engine
from src.core.security import hash_password
from src.models.project import Project
from src.models.property import Property
from src.models.rental_property import (
    DepositTransaction,
    MonthlyInvoice,
    RentalContract,
    RentalInquiry,
    RentalProperty,
    RentalUnit,
)
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

# ==============================================================================
# 1. SAMPLE REAL ESTATE PROJECTS ACROSS VIETNAM (10 MAJOR DEVELOPMENTS)
# ==============================================================================
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
        "name": "Phú Mỹ Hưng The Peak - Midtown",
        "slug": "phu-my-hung-midtown-the-peak",
        "developer": "Công ty TNHH Phát triển Phú Mỹ Hưng & Liên doanh Nhật Bản",
        "description": (
            "Tuyệt tác kiến trúc đỉnh cao tại khu đô thị kiểu mẫu Nam Sài Gòn. "
            "Dự án tọa lạc dọc sông Cả Cấm với công viên hoa anh đào Sakura Park duy nhất tại Việt Nam. "
            "Chuỗi tiện ích nghỉ dưỡng khép kín với thác nước nhân tạo, hồ bơi chân mây và không gian xanh sinh thái ven sông."
        ),
        "status": "completed",
        "total_units": 2400,
        "launch_year": 2017,
        "handover_year": 2022,
        "address": "Đường Nguyễn Lương Bằng, Phường Tân Phú",
        "ward": "Phường Tân Phú",
        "district": "Quận 7",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7185,
        "longitude": 106.7192,
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 5800000000.0,
        "price_range_max": 25000000000.0,
        "amenities": [
            "Công viên hoa anh đào Sakura Park dọc sông Cả Cấm",
            "Hồ bơi chân mây vô cực tầng mái",
            "Phòng tập Golf giả lập 3D thượng lưu",
            "Khu vui chơi trẻ em Kid Club trong nhà và ngoài trời",
            "Hồ ngâm jacuzzi và phòng xông hơi sauna thư giãn",
            "Hệ thống trường quốc tế SSIS, Đài Bắc, Hàn Quốc bao quanh",
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
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 1850000000.0,
        "price_range_max": 28000000000.0,
        "amenities": [
            "Biển hồ nước mặn nhân tạo Crystal Lagoons 6.1ha",
            "Hồ Ngọc Trai nước ngọt 24.5ha bờ cát trắng",
            "Tòa tháp văn phòng thông minh TechnoPark Tower Top 10 thế giới",
            "Đại học tinh hoa quốc tế VinUni",
            "Bệnh viện Vinmec & Trường Vinschool",
            "Hệ thống công viên BBQ bãi biển ngoài trời",
        ],
    },
    {
        "name": "Khu Đô Thị Starlake Tây Hồ Tây",
        "slug": "starlake-tay-ho-tay",
        "developer": "Daewoo E&C (Hàn Quốc)",
        "description": (
            "Khu đô thị sinh thái cao cấp quy mô 186.3 ha tại trung tâm hành chính mới Tây Hồ Tây Hà Nội. "
            "Nơi đặt trụ sở của các Bộ ngành trung ương, đại sứ quán quốc tế và các tập đoàn toàn cầu như Samsung R&D, CJ, Emart. "
            "Mật độ xây dựng chỉ 16%, sở hữu công viên hồ điều hòa 4.5ha và hệ thống giáo dục quốc tế hàng đầu."
        ),
        "status": "completed",
        "total_units": 3200,
        "launch_year": 2016,
        "handover_year": 2023,
        "address": "Khu đô thị Starlake Tây Hồ Tây, Phường Xuân Tảo",
        "ward": "Phường Xuân Tảo",
        "district": "Quận Bắc Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0562,
        "longitude": 105.7984,
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 7500000000.0,
        "price_range_max": 75000000000.0,
        "amenities": [
            "Trung tâm R&D lớn nhất Đông Nam Á của Tập đoàn Samsung",
            "Đại siêu thị Emart và trung tâm thương mại Takashimaya",
            "Hồ điều hòa trung tâm 4.5ha cùng công viên nội khu rợp bóng cây",
            "Trường liên cấp quốc tế Gateway & Dewey School",
            "Hồ bơi 4 mùa nước ấm trong nhà",
            "Hệ thống an ninh khép kín đa tầng chuẩn ngoại giao đoàn",
        ],
    },
    {
        "name": "Sun Cosmo Residence Đà Nẵng",
        "slug": "sun-cosmo-residence-da-nang",
        "developer": "Tập đoàn Sun Group",
        "description": (
            "Tổ hợp bất động sản năng động ven sông Hàn ngay chân cầu Trần Thị Lý, thành phố Đà Nẵng. "
            "Dự án quy tụ 2 tòa tháp căn hộ The Panoma hướng trọn tầm nhìn 3 trong 1: Sông Hàn thơ mộng, "
            "biển Mỹ Khê cát trắng và trung tâm thành phố rực rỡ pháo hoa quốc tế DIFF."
        ),
        "status": "under_construction",
        "total_units": 650,
        "launch_year": 2023,
        "handover_year": 2025,
        "address": "Đường Trần Hưng Đạo, Phường Mỹ An",
        "ward": "Phường Mỹ An",
        "district": "Quận Ngũ Hành Sơn",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0538,
        "longitude": 108.2325,
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 3500000000.0,
        "price_range_max": 18000000000.0,
        "amenities": [
            "Bể bơi vô cực ngắm trọn lễ hội pháo hoa quốc tế DIFF sông Hàn",
            "Tuyến phố thương mại The Cosmo nhộn nhịp ngày đêm",
            "Sân tập golf mini mô phỏng",
            "Vườn thiền Sky Garden trên tầng mái",
            "Khu thể thao đa năng và phòng gym hướng sông",
            "Bến du thuyền sông Hàn cách dự án 300m",
        ],
    },
    {
        "name": "Sun Grand City Hillside & Grand World Phú Quốc",
        "slug": "sun-grand-city-hillside-phu-quoc",
        "developer": "Tập đoàn Sun Group",
        "description": (
            "Quần thể đô thị nghỉ dưỡng và giải trí biểu tượng tại bờ Tây Nam đảo ngọc Phú Quốc. "
            "Nằm tại tâm điểm thị trấn Hoàng Hôn Sunset Town, ôm trọn Cầu Hôn Kiss Bridge và ga đi cáp treo Hòn Thơm vượt biển. "
            "Căn hộ cao tầng đầu tiên sở hữu lâu dài tại đảo ngọc với kiến trúc Địa Trung Hải rực rỡ sắc màu."
        ),
        "status": "completed",
        "total_units": 1251,
        "launch_year": 2021,
        "handover_year": 2023,
        "address": "Thị trấn Hoàng Hôn Sunset Town, Phường An Thới",
        "ward": "Phường An Thới",
        "district": "Thành phố Phú Quốc",
        "city": "Tỉnh Kiên Giang",
        "latitude": 10.0245,
        "longitude": 104.0152,
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
        "master_plan_url": "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1600&q=80",
        "legal_status": "Sổ hồng sở hữu lâu dài",
        "price_range_min": 3200000000.0,
        "price_range_max": 16500000000.0,
        "amenities": [
            "Cầu Hôn Kiss Bridge kiệt tác kiến trúc Ý",
            "Ga cáp treo Hòn Thơm 3 dây vượt biển dài nhất thế giới",
            "Hồ bơi vô cực ngắm hoàng hôn biển Địa Trung Hải",
            "Quảng trường con sò La Festa sầm uất",
            "Show diễn đa phương tiện Kiss of the Sea trên mặt biển",
            "Chợ đêm Vui Phết Bazaar ven biển độc nhất vô nhị",
        ],
    },
]

# ==============================================================================
# 2. SAMPLE PROPERTIES (SALE, RENT, HOMESTAY - 40 NATIONWIDE LISTINGS)
# ==============================================================================
SAMPLE_PROPERTIES: list[dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # CATEGORY B: MUA BÁN (SALE) - CHUNG CƯ DỰ ÁN & CĂN HỘ CAO CẤP
    # --------------------------------------------------------------------------
    {
        "title": "Căn hộ 3PN Sapphire view Biển Hồ Vinhomes Ocean Park",
        "description": "Cần bán căn hộ 3 phòng ngủ tầng trung tháp S2.16 Vinhomes Ocean Park Gia Lâm. Ban công view trọn vẹn biển hồ nước mặn 6.1ha và hồ cát trắng Ngọc Trai. Đầy đủ nội thất cao cấp, sẵn sổ hồng sang tên ngay.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 4650000000.0,
        "currency": "VND",
        "area_sqm": 88.5,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "Tòa S2.16 Vinhomes Ocean Park, Xã Đa Tốn",
        "ward": "Xã Đa Tốn",
        "district": "Huyện Gia Lâm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9932,
        "longitude": 105.9421,
        "status": "active",
        "project_slug": "vinhomes-ocean-park",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Penthouse Duplex Starlake Tây Hồ Tây Đẳng Cấp Thượng Lưu",
        "description": "Căn hộ thông tầng Penthouse Duplex tháp H9 Starlake Tây Hồ Tây. Diện tích thông thủy 235m2 với trần cao 6.5m thoáng đạt, tầm nhìn panorama ngắm trọn Hồ Tây và cầu Nhật Tân. Tiện ích chuẩn ngoại giao đoàn, bàn giao thô dễ thiết kế.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 28500000000.0,
        "currency": "VND",
        "area_sqm": 235.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "Khu đô thị Starlake Tây Hồ Tây, Phường Xuân Tảo",
        "ward": "Phường Xuân Tảo",
        "district": "Quận Bắc Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0562,
        "longitude": 105.7984,
        "status": "active",
        "project_slug": "starlake-tay-ho-tay",
        "images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Căn hộ The Panoma 2PN Sun Cosmo Residence View Trọn Sông Hàn",
        "description": "Bán căn hộ 2 phòng ngủ tầng cao tháp The Panoma dự án Sun Cosmo Residence Đà Nẵng ngay sát cầu Trần Thị Lý. View trực diện sông Hàn, ngắm trọn pháo hoa DIFF và biển Mỹ Khê. Hưởng trọn tiện ích hồ bơi vô cực, sky garden tầng thượng.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 5200000000.0,
        "currency": "VND",
        "area_sqm": 75.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Đường Trần Hưng Đạo, Phường Mỹ An",
        "ward": "Phường Mỹ An",
        "district": "Quận Ngũ Hành Sơn",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0538,
        "longitude": 108.2325,
        "status": "active",
        "project_slug": "sun-cosmo-residence-da-nang",
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Căn hộ Landmark 81 Luxury View Panorama Sông Sài Gòn",
        "description": "Bán căn hộ 3PN cao cấp tháp biểu tượng Landmark 81 Vinhomes Central Park. Tầng cao view trực diện sông Sài Gòn và bán đảo Thanh Đa. Nội thất xa xỉ nhập khẩu từ Ý, sảnh lễ tân riêng biệt, hồ bơi chân mây và TTTM Vincom sầm uất ngay dưới chân.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 12800000000.0,
        "currency": "VND",
        "area_sqm": 108.5,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "Tòa Landmark 81, 208 Nguyễn Hữu Cảnh, Phường 22",
        "ward": "Phường 22",
        "district": "Quận Bình Thạnh",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7954,
        "longitude": 106.7218,
        "status": "active",
        "project_slug": "vinhomes-central-park",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Căn hộ The Peak Midtown Phú Mỹ Hưng View Công Viên Hoa Anh Đào",
        "description": "Chính chủ chuyển nhượng căn hộ 2 phòng ngủ tòa The Peak M8B Phú Mỹ Hưng Midtown. Thiết kế hiện đại mở rộng ban công đón gió sông Cả Cấm và công viên Sakura Park hoa anh đào. Đầy đủ tiện ích hồ bơi vô cực, phòng golf 3D và trường quốc tế.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 8900000000.0,
        "currency": "VND",
        "area_sqm": 90.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Khu phức hợp Midtown, Phường Tân Phú",
        "ward": "Phường Tân Phú",
        "district": "Quận 7",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7185,
        "longitude": 106.7192,
        "status": "active",
        "project_slug": "phu-my-hung-midtown-the-peak",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Căn hộ Hillside Địa Trung Hải Phú Quốc Trực Diện Cầu Hôn",
        "description": "Bán căn hộ nghỉ dưỡng 2PN tòa The Hill Sun Grand City Hillside Residence thị trấn Hoàng Hôn Sunset Town Phú Quốc. Sở hữu lâu dài, ban công view thẳng Cầu Hôn Kiss Bridge và sân khấu nhạc nước biểu diễn Vortex. Tiềm năng kinh doanh homestay cực cao.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 4800000000.0,
        "currency": "VND",
        "area_sqm": 68.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Thị trấn Hoàng Hôn Sunset Town, Phường An Thới",
        "ward": "Phường An Thới",
        "district": "Thành phố Phú Quốc",
        "city": "Tỉnh Kiên Giang",
        "latitude": 10.0245,
        "longitude": 104.0152,
        "status": "active",
        "project_slug": "sun-grand-city-hillside-phu-quoc",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
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
        "address": "Khu đô thị mới Thủ Thiêm, Phường An Khánh",
        "ward": "Phường An Khánh",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7725,
        "longitude": 106.7112,
        "status": "active",
        "project_slug": "the-metropole-thu-thiem",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
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
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Căn hộ Vinhomes Smart City 2PN view vườn Nhật Zen Park",
        "description": "Chính chủ cần bán căn hộ 2 phòng ngủ 2 vệ sinh tại phân khu The Tonkin Vinhomes Smart City Tây Mỗ. Căn góc thoáng sáng, nội thất bàn giao gắn tường sang trọng, liền kề nhà để xe nổi và hồ điều hòa trung tâm.",
        "property_type": "apartment",
        "listing_type": "sale",
        "price": 3200000000.0,
        "currency": "VND",
        "area_sqm": 65.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Đại lộ Thăng Long, Phường Tây Mỗ",
        "ward": "Phường Tây Mỗ",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9998,
        "longitude": 105.7483,
        "status": "active",
        "project_slug": "vinhomes-smart-city",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },

    # --------------------------------------------------------------------------
    # CATEGORY B: MUA BÁN (SALE) - NHÀ PHỐ MẶT TIỀN & HẺM XE HƠI
    # --------------------------------------------------------------------------
    {
        "title": "Nhà phố mặt tiền kinh doanh phố Duy Tân - Cầu Giấy",
        "description": "Bán tòa nhà văn phòng mặt tiền phố công nghệ Duy Tân Cầu Giấy. Diện tích 110m2, xây 7 tầng thang máy nhập khẩu, mặt tiền 6.5m vỉa hè rộng rãi. Hiện đang cho thuê nguyên căn 120 triệu/tháng ổn định lâu dài.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 26500000000.0,
        "currency": "VND",
        "area_sqm": 110.0,
        "num_bedrooms": 6,
        "num_bathrooms": 7,
        "address": "Phố Duy Tân, Phường Dịch Vọng Hậu",
        "ward": "Phường Dịch Vọng Hậu",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0315,
        "longitude": 105.7832,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nhà cổ kinh doanh phố đi bộ Hàng Buồm - Hoàn Kiếm",
        "description": "Bán nhà mặt phố cổ Hàng Buồm vị trí kim cương trung tâm phố cổ Hoàn Kiếm Hà Nội. Mặt tiền kinh doanh vàng, vỉa hè rộng, phù hợp làm khách sạn boutique, nhà hàng ẩm thực hoặc quán bar phục vụ du khách quốc tế.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 48000000000.0,
        "currency": "VND",
        "area_sqm": 75.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "Phố Hàng Buồm, Phường Hàng Buồm",
        "ward": "Phường Hàng Buồm",
        "district": "Quận Hoàn Kiếm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0368,
        "longitude": 105.8524,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nhà phố thương mại mặt tiền đường Lê Thị Riêng - Bến Thành",
        "description": "Cần bán gấp căn nhà phố mặt tiền đường Lê Thị Riêng phường Bến Thành Quận 1. Khu vực kinh doanh sầm uất đa ngành nghề, cách chợ Bến Thành và ga Metro số 1 chỉ 400m. Diện tích đất 95m2 nở hậu phong thủy tốt.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 39000000000.0,
        "currency": "VND",
        "area_sqm": 95.0,
        "num_bedrooms": 5,
        "num_bathrooms": 5,
        "address": "Đường Lê Thị Riêng, Phường Bến Thành",
        "ward": "Phường Bến Thành",
        "district": "Quận 1",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7712,
        "longitude": 106.6924,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nhà phố sân vườn hẻm xe hơi tránh nhau đường Võ Thị Sáu",
        "description": "Bán nhà phố phong cách hiện đại hẻm xe tải 8m đường Võ Thị Sáu Quận 3. Nhà 1 trệt 3 lầu có gara ô tô, sân thượng ngắm cảnh lộng gió. Khu cán bộ an ninh dân trí cao, gần công viên Lê Văn Tám.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 18500000000.0,
        "currency": "VND",
        "area_sqm": 120.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Đường Võ Thị Sáu, Phường Võ Thị Sáu",
        "ward": "Phường Võ Thị Sáu",
        "district": "Quận 3",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7876,
        "longitude": 106.6905,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nhà phố mặt tiền đường Bạch Đằng hướng thẳng sông Hàn",
        "description": "Vị trí độc tôn trên tuyến đường du lịch đẹp nhất Đà Nẵng. Nhà phố 4 tầng mặt tiền đường Bạch Đằng nhìn thẳng cầu Rồng và cầu Sông Hàn. Vỉa hè thênh thang, tuyến phố đi bộ tập trung khách du lịch trong và ngoài nước.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 29000000000.0,
        "currency": "VND",
        "area_sqm": 140.0,
        "num_bedrooms": 5,
        "num_bathrooms": 5,
        "address": "Đường Bạch Đằng, Phường Hải Châu 1",
        "ward": "Phường Hải Châu 1",
        "district": "Quận Hải Châu",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0682,
        "longitude": 108.2238,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Shophouse phố đi bộ phong cách châu Âu Bãi Cháy Hạ Long",
        "description": "Bán căn Shophouse 5 tầng mặt đường phố đi bộ Sun Plaza Bãi Cháy Quảng Ninh. Kiến trúc châu Âu sang trọng, kế cận công viên giải trí Sun World và bãi tắm Hạ Long. Đang khai thác kinh doanh cafe và lưu trú khách sạn mini rất tốt.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 16800000000.0,
        "currency": "VND",
        "area_sqm": 130.0,
        "num_bedrooms": 8,
        "num_bathrooms": 8,
        "address": "Đường Hạ Long, Phường Bãi Cháy",
        "ward": "Phường Bãi Cháy",
        "district": "Thành phố Hạ Long",
        "city": "Tỉnh Quảng Ninh",
        "latitude": 20.9575,
        "longitude": 107.0348,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nhà phố thương mại Shophouse Lê Hồng Phong Hải Phòng",
        "description": "Bán căn Shophouse mặt tiền trục đại lộ Lê Hồng Phong Hải Phòng. Nằm trong quần thể khu đô thị kiểu mới, kết nối sân bay Cát Bi và cảng Đình Vũ chỉ 10 phút. Nhà xây 4 tầng hoàn thiện mặt ngoài, tiện làm showroom văn phòng công ty.",
        "property_type": "house",
        "listing_type": "sale",
        "price": 14500000000.0,
        "currency": "VND",
        "area_sqm": 115.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Đại lộ Lê Hồng Phong, Phường Đông Khê",
        "ward": "Phường Đông Khê",
        "district": "Quận Ngô Quyền",
        "city": "Thành phố Hải Phòng",
        "latitude": 20.8524,
        "longitude": 106.7018,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },

    # --------------------------------------------------------------------------
    # CATEGORY B: MUA BÁN (SALE) - BIỆT THỰ SÂN VƯỜN & BIỆT THỰ NGHỈ DƯỠNG
    # --------------------------------------------------------------------------
    {
        "title": "Biệt thự đơn lập ven hồ Harmony Vinhomes Riverside",
        "description": "Bán căn biệt thự đơn lập phân khu Hướng Dương Vinhomes Riverside The Harmony Long Biên. Diện tích đất 350m2, sân vườn xanh mát ôm quanh hồ điều hòa. Không gian sống đẳng cấp giới tinh hoa Hà Nội với trường BIS và Vincom Plaza.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 58000000000.0,
        "currency": "VND",
        "area_sqm": 350.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "Khu đô thị Vinhomes Riverside, Phường Phúc Đồng",
        "ward": "Phường Phúc Đồng",
        "district": "Quận Long Biên",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0375,
        "longitude": 105.9082,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Biệt thự ven sông Thảo Điền Compound hồ bơi riêng biệt",
        "description": "Bán siêu biệt thự ven sông Sài Gòn đường Nguyễn Văn Hưởng Thảo Điền TP. Thủ Đức. Diện tích khuôn viên 450m2 có hồ bơi tràn bờ, sân vườn nhiệt đới và bến đỗ ca nô riêng. Khu compound an ninh 24/7 tuyệt đối yên tĩnh cho gia đình chuyên gia.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 72000000000.0,
        "currency": "VND",
        "area_sqm": 450.0,
        "num_bedrooms": 5,
        "num_bathrooms": 6,
        "address": "Đường Nguyễn Văn Hưởng, Phường Thảo Điền",
        "ward": "Phường Thảo Điền",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8062,
        "longitude": 106.7354,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Biệt thự đồi view toàn cảnh vịnh kỳ quan Hạ Long",
        "description": "Biệt thự nghỉ dưỡng đồi Monaco Bãi Cháy Hạ Long. Tọa lạc tại độ cao lý tưởng phóng tầm mắt ngắm toàn cảnh Vịnh Hạ Long kỳ quan thiên nhiên thế giới. Thiết kế phong cách Địa Trung Hải có hồ bơi vô cực và hầm rượu vang quý.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 32000000000.0,
        "currency": "VND",
        "area_sqm": 380.0,
        "num_bedrooms": 4,
        "num_bathrooms": 5,
        "address": "Đồi Monaco, Phường Bãi Cháy",
        "ward": "Phường Bãi Cháy",
        "district": "Thành phố Hạ Long",
        "city": "Tỉnh Quảng Ninh",
        "latitude": 20.9634,
        "longitude": 107.0289,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Biệt thự biển Ocean Villa An Viên Nha Trang",
        "description": "Chuyển nhượng biệt thự đơn lập khu đô thị sinh thái biển An Viên phía Nam thành phố Nha Trang. Cách bãi tắm biển chỉ vài bước chân, kề cận bến cáp treo Vinpearl Nha Trang. Sổ đỏ lâu dài trao tay, nội thất gỗ tự nhiên cao cấp.",
        "property_type": "villa",
        "listing_type": "sale",
        "price": 24500000000.0,
        "currency": "VND",
        "area_sqm": 280.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "Khu đô thị An Viên, Phường Vĩnh Trường",
        "ward": "Phường Vĩnh Trường",
        "district": "Thành phố Nha Trang",
        "city": "Tỉnh Khánh Hòa",
        "latitude": 12.2085,
        "longitude": 109.2142,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },

    # --------------------------------------------------------------------------
    # CATEGORY B: MUA BÁN (SALE) - ĐẤT NỀN THỔ CƯ & ĐẤT VEN ĐÔ
    # --------------------------------------------------------------------------
    {
        "title": "Đất nền đấu giá quy hoạch lên quận Đông Anh",
        "description": "Bán lô đất đấu giá Vĩnh Ngọc Đông Anh Hà Nội ngay chân cầu Nhật Tân. Diện tích 100m2 vuông vắn, đường trước nhà 13m rải nhựa có vỉa hè cây xanh, hạ tầng điện nước ngầm đồng bộ. Đón đầu quy hoạch Đông Anh lên quận và dự án thành phố thông minh.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 7200000000.0,
        "currency": "VND",
        "area_sqm": 100.0,
        "num_bedrooms": 0,
        "num_bathrooms": 0,
        "address": "Khu đấu giá X4, Xã Vĩnh Ngọc",
        "ward": "Xã Vĩnh Ngọc",
        "district": "Huyện Đông Anh",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0945,
        "longitude": 105.8276,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Đất thổ cư sổ hồng riêng gần sân bay quốc tế Long Thành",
        "description": "Bán đất thổ cư mặt tiền đường liên xã Long Phước huyện Long Thành tỉnh Đồng Nai. Cách cổng chính sân bay quốc tế Long Thành 3.5km, kết nối trực tiếp cao tốc TP.HCM - Long Thành - Dầu Giây. Sổ hồng riêng thổ cư 100%, xây dựng tự do.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 3800000000.0,
        "currency": "VND",
        "area_sqm": 160.0,
        "num_bedrooms": 0,
        "num_bathrooms": 0,
        "address": "Đường Bàu Cạn, Xã Long Phước",
        "ward": "Xã Long Phước",
        "district": "Huyện Long Thành",
        "city": "Tỉnh Đồng Nai",
        "latitude": 10.7432,
        "longitude": 107.0128,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Đất nền biệt thự vườn sinh thái Hòa Khương Hòa Vang",
        "description": "Bán lô đất biệt thự nhà vườn tại xã Hòa Khương huyện Hòa Vang thành phố Đà Nẵng. Không gian đồi thoai thoải nhìn về dãy Bà Nà Hills, suối nước mát quanh năm, thích hợp làm homestay nông nghiệp hoặc biệt phủ nghỉ dưỡng cuối tuần.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 4200000000.0,
        "currency": "VND",
        "area_sqm": 300.0,
        "num_bedrooms": 0,
        "num_bathrooms": 0,
        "address": "Thôn Phú Sơn Nam, Xã Hòa Khương",
        "ward": "Xã Hòa Khương",
        "district": "Huyện Hòa Vang",
        "city": "Thành phố Đà Nẵng",
        "latitude": 15.9842,
        "longitude": 108.1189,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Đất nền đô thị mới ven sông Cần Thơ",
        "description": "Bán đất nền khu đô thị Nam Cần Thơ phường Hưng Thạnh quận Cái Răng TP Cần Thơ. Mặt tiền đường 20m có dải phân cách cây xanh, gần cầu Hưng Lợi và siêu thị Go Cần Thơ. Đất sạch sổ đỏ hạ tầng hoàn thiện 100%.",
        "property_type": "land",
        "listing_type": "sale",
        "price": 3600000000.0,
        "currency": "VND",
        "area_sqm": 125.0,
        "num_bedrooms": 0,
        "num_bathrooms": 0,
        "address": "Đường số 10 Khu đô thị Nam Cần Thơ, Phường Hưng Thạnh",
        "ward": "Phường Hưng Thạnh",
        "district": "Quận Cái Răng",
        "city": "Thành phố Cần Thơ",
        "latitude": 10.0152,
        "longitude": 105.7824,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1574958269340-fa927503f3dd?auto=format&fit=crop&w=1200&q=80",
        ],
    },

    # --------------------------------------------------------------------------
    # CATEGORY C: PHÂN HỆ CHO THUÊ DÀI HẠN & MẶT BẰNG (RENT LISTINGS)
    # --------------------------------------------------------------------------
    {
        "title": "Cho thuê căn hộ 2PN Full nội thất Times City Park Hill",
        "description": "Cho thuê căn hộ 2 phòng ngủ tòa Park 9 Times City Park Hill Hai Bà Trưng Hà Nội. Nội thất trang bị cao cấp chuẩn gia đình gồm smart TV 65 inch, máy rửa bát Bosch, sofa nỉ Italia. Miễn phí phí dịch vụ quản lý, hồ bơi và thể thao.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 1, "service_fee_monthly": 0},
        "rental_rules": {"curfew": False, "allow_pets": False, "private_bathroom": True, "has_elevator": True},
        "price": 16500000.0,
        "currency": "VND",
        "area_sqm": 74.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "458 Minh Khai, Phường Vĩnh Tuy",
        "ward": "Phường Vĩnh Tuy",
        "district": "Quận Hai Bà Trưng",
        "city": "Thành phố Hà Nội",
        "latitude": 20.9954,
        "longitude": 105.8682,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Cho thuê căn hộ cao cấp 3PN Discovery Complex Cầu Giấy",
        "description": "Căn hộ 3PN tháp đôi Discovery Complex 302 Cầu Giấy. Kết nối trực tiếp ga đường sắt trên cao Nhổn - Ga Hà Nội qua cầu nối riêng. Tầng cao view hồ Nghĩa Đô thoáng đãng, TTTM Lotte Mart và rạp chiếu phim BHD ngay khối đế.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 2, "service_fee_monthly": 200000},
        "rental_rules": {"curfew": False, "allow_pets": False, "private_bathroom": True, "has_elevator": True},
        "price": 24000000.0,
        "currency": "VND",
        "area_sqm": 148.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "address": "302 Cầu Giấy, Phường Dịch Vọng",
        "ward": "Phường Dịch Vọng",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0345,
        "longitude": 105.7924,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Cho thuê căn hộ Sunrise City South Towers liền kề Quận 1",
        "description": "Cho thuê căn hộ 2 phòng ngủ tháp V5 Sunrise City đường Nguyễn Hữu Thọ Quận 7. Đối diện đại siêu thị Lotte Mart, sang chợ Bến Thành Quận 1 chỉ 7 phút. Hồ bơi chân mây 2000m2 view pháo hoa, hầm để xe rộng rãi 2 tầng.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 2, "service_fee_monthly": 250000},
        "rental_rules": {"curfew": False, "allow_pets": True, "private_bathroom": True, "has_elevator": True},
        "price": 18000000.0,
        "currency": "VND",
        "area_sqm": 76.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "23 Nguyễn Hữu Thọ, Phường Tân Hưng",
        "ward": "Phường Tân Hưng",
        "district": "Quận 7",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7425,
        "longitude": 106.7018,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Cho thuê căn hộ Hiyori Garden Tower tiêu chuẩn Nhật Bản",
        "description": "Căn hộ 2 phòng ngủ chuẩn sống Nhật Bản Hiyori Garden Tower gần cầu Rồng Sơn Trà Đà Nẵng. Nội thất trang nhã tối giản, có bồn tắm nằm cao cấp Toto, bể bơi có mái che 4 mùa, nhà trẻ tiêu chuẩn Nhật và phòng sinh hoạt cộng đồng.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 2, "service_fee_monthly": 150000},
        "rental_rules": {"curfew": False, "allow_pets": False, "private_bathroom": True, "has_elevator": True},
        "price": 15000000.0,
        "currency": "VND",
        "area_sqm": 69.0,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Đường Võ Văn Kiệt, Phường An Hải Đông",
        "ward": "Phường An Hải Đông",
        "district": "Quận Sơn Trà",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0612,
        "longitude": 108.2375,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Cho thuê căn hộ Sora Gardens trung tâm TP Mới Bình Dương",
        "description": "Cho thuê căn hộ 2PN Sora Gardens Tokyu trung tâm Thành phố Mới Bình Dương. Không gian sống đẳng cấp phong cách Nhật Bản dành cho chuyên gia nước ngoài và gia đình trẻ làm việc tại VSIP 2 và KCN Đồng An. Có hồ bơi tầng 4, vườn treo và siêu thị AEON.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 2, "service_fee_monthly": 180000},
        "rental_rules": {"curfew": False, "allow_pets": True, "private_bathroom": True, "has_elevator": True},
        "price": 12000000.0,
        "currency": "VND",
        "area_sqm": 71.5,
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "address": "Đại lộ Hùng Vương, Phường Hòa Phú",
        "ward": "Phường Hòa Phú",
        "district": "Thành phố Thủ Dầu Một",
        "city": "Tỉnh Bình Dương",
        "latitude": 11.0542,
        "longitude": 106.6718,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Mặt bằng kinh doanh thời trang phố Bà Triệu",
        "description": "Cho thuê mặt bằng tầng 1 mặt tiền phố thời trang thương hiệu cao cấp Bà Triệu quận Hai Bà Trưng Hà Nội. Mặt tiền 6.5m kính cường lực suốt, vỉa hè rộng 4m gửi xe tiện lợi. Phù hợp làm boutique thời trang, mỹ phẩm quốc tế hoặc trang sức cao cấp.",
        "property_type": "commercial",
        "listing_type": "rent",
        "rental_type": "entire_house",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 3},
        "rental_rules": {"curfew": False, "fingerprint_lock": True},
        "price": 65000000.0,
        "currency": "VND",
        "area_sqm": 95.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Phố Bà Triệu, Phường Lê Đại Hành",
        "ward": "Phường Lê Đại Hành",
        "district": "Quận Hai Bà Trưng",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0118,
        "longitude": 105.8495,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Shophouse ẩm thực F&B phố Phan Xích Long Phú Nhuận",
        "description": "Cho thuê nhà nguyên căn mặt tiền phố ẩm thực đêm Phan Xích Long Phú Nhuận TP.HCM. Diện tích 6x20m, 1 trệt 3 lầu thang máy, hệ thống PCCC đạt chuẩn nghiệm thu mới nhất. Phù hợp mở nhà hàng lẩu nướng, quán cafe thương hiệu lớn.",
        "property_type": "commercial",
        "listing_type": "rent",
        "rental_type": "entire_house",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 3},
        "rental_rules": {"curfew": False, "fingerprint_lock": True, "has_elevator": True},
        "price": 55000000.0,
        "currency": "VND",
        "area_sqm": 120.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "Đường Phan Xích Long, Phường 2",
        "ward": "Phường 2",
        "district": "Quận Phú Nhuận",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7985,
        "longitude": 106.6912,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Mặt bằng kinh doanh showroom đại lộ Nguyễn Văn Cừ Cần Thơ",
        "description": "Cho thuê mặt bằng kinh doanh vị trí góc 2 mặt tiền đại lộ Nguyễn Văn Cừ quận Ninh Kiều TP. Cần Thơ. Diện tích sàn 150m2 thông suốt, vỉa hè rộng đỗ được nhiều xe ô tô. Thích hợp mở phòng khám nha khoa, showroom nội thất, ngân hàng hoặc siêu thị tiện lợi.",
        "property_type": "commercial",
        "listing_type": "rent",
        "rental_type": "entire_house",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 3},
        "rental_rules": {"curfew": False, "fingerprint_lock": True},
        "price": 35000000.0,
        "currency": "VND",
        "area_sqm": 150.0,
        "num_bedrooms": 1,
        "num_bathrooms": 2,
        "address": "Đại lộ Nguyễn Văn Cừ, Phường An Khánh",
        "ward": "Phường An Khánh",
        "district": "Quận Ninh Kiều",
        "city": "Thành phố Cần Thơ",
        "latitude": 10.0384,
        "longitude": 105.7612,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Văn phòng hạng A Keangnam Landmark 72",
        "description": "Cho thuê sàn văn phòng hạng A diện tích linh hoạt tại tòa tháp Keangnam Landmark 72 Nam Từ Liêm Hà Nội. Hệ thống điều hòa trung tâm Chiller tiết kiệm năng lượng, 8 thang máy tốc độ cao, máy phát điện dự phòng 100%, an ninh kiểm soát thẻ từ thông minh.",
        "property_type": "commercial",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 3, "service_fee_monthly": 500000},
        "rental_rules": {"curfew": False, "has_elevator": True, "fingerprint_lock": True},
        "price": 85000000.0,
        "currency": "VND",
        "area_sqm": 180.0,
        "num_bedrooms": 0,
        "num_bathrooms": 2,
        "address": "Đường Phạm Hùng, Phường Mễ Trì",
        "ward": "Phường Mễ Trì",
        "district": "Quận Nam Từ Liêm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0168,
        "longitude": 105.7834,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Sàn văn phòng tài chính Bitexco Financial Tower",
        "description": "Cho thuê không gian làm việc đẳng cấp tại biểu tượng tài chính Bitexco Financial Tower Quận 1 TP.HCM. Tầm nhìn 360 độ ngắm trọn vẹn trung tâm kinh tế thành phố. Phù hợp làm trụ sở các quỹ đầu tư, công ty công nghệ và tập đoàn đa quốc gia.",
        "property_type": "commercial",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "rental_costs": {"electricity_billing": "state_rate", "deposit_months": 3, "service_fee_monthly": 800000},
        "rental_rules": {"curfew": False, "has_elevator": True, "fingerprint_lock": True},
        "price": 120000000.0,
        "currency": "VND",
        "area_sqm": 210.0,
        "num_bedrooms": 0,
        "num_bathrooms": 3,
        "address": "Số 2 Hải Triều, Phường Bến Nghé",
        "ward": "Phường Bến Nghé",
        "district": "Quận 1",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7718,
        "longitude": 106.7042,
        "status": "active",
        "images": [
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },

    # --------------------------------------------------------------------------
    # CATEGORY E: HOMESTAY & CĂN HỘ DU LỊCH (DAILY/VACATION LISTINGS)
    # --------------------------------------------------------------------------
    {
        "title": "Old Quarter Heritage Homestay Phố Cổ Hà Nội",
        "description": "Homestay mang đậm chất kiến trúc Pháp cổ truyền thống giữa lòng phố đi bộ Hàng Buồm Hoàn Kiếm. Cửa sổ vòm lãng mạn ngắm phố cổ về đêm, máy pha cafe espresso, bồn tắm gỗ sồi và ban công hoa giấy check-in thơ mộng.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "price": 750000.0,
        "currency": "VND",
        "area_sqm": 45.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "36 Hàng Buồm, Phường Hàng Buồm",
        "ward": "Phường Hàng Buồm",
        "district": "Quận Hoàn Kiếm",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0365,
        "longitude": 105.8521,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": False,
            "private_bathroom": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
            "max_occupants": 2,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Westlake Panorama Studio & Ban Công Trực Diện Hồ Tây",
        "description": "Căn hộ homestay studio view trực diện 100% mặt nước Hồ Tây đường Quảng An quận Tây Hồ. Ban công kính lộng gió đón hoàng hôn tím tuyệt đẹp, máy chiếu phim 4K Netflix, giường King size đệm cao su thiên nhiên êm ái.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "price": 950000.0,
        "currency": "VND",
        "area_sqm": 52.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Số 28 Đường Quảng An, Phường Quảng An",
        "ward": "Phường Quảng An",
        "district": "Quận Tây Hồ",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0628,
        "longitude": 105.8245,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": True,
            "private_bathroom": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
            "max_occupants": 2,
        },
        "images": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Sơn Trà Ocean View Beach Studio gần bãi tắm Mỹ Khê",
        "description": "Homestay căn hộ biển đường Võ Nguyên Giáp quận Sơn Trà Đà Nẵng. Cách bãi cát trắng biển Mỹ Khê chỉ 80m, ban công đón bình minh trên đại dương. Đầy đủ bếp từ nấu hải sản, máy giặt sấy riêng và hồ bơi tầng thượng miễn phí.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "price": 800000.0,
        "currency": "VND",
        "area_sqm": 48.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Đường Võ Nguyên Giáp, Phường Phước Mỹ",
        "ward": "Phường Phước Mỹ",
        "district": "Quận Sơn Trà",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0645,
        "longitude": 108.2468,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": False,
            "private_bathroom": True,
            "has_elevator": True,
            "live_with_owner": False,
            "max_occupants": 2,
        },
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Hạ Long Bay Coastal Retreat Villa view biển Bãi Cháy",
        "description": "Villa nghỉ dưỡng 3 phòng ngủ nhìn thẳng ra vịnh di sản Bãi Cháy Hạ Long Quảng Ninh. Sân vườn nướng BBQ hải sản tươi sống ngoài trời, hồ bơi mini gia đình riêng tư, không gian lý tưởng cho nhóm bạn bè hoặc gia đình 6-8 người kỳ nghỉ cuối tuần.",
        "property_type": "villa",
        "listing_type": "rent",
        "rental_type": "entire_house",
        "price": 2800000.0,
        "currency": "VND",
        "area_sqm": 160.0,
        "num_bedrooms": 3,
        "num_bathrooms": 3,
        "address": "Đường Hoàng Quốc Việt, Phường Bãi Cháy",
        "ward": "Phường Bãi Cháy",
        "district": "Thành phố Hạ Long",
        "city": "Tỉnh Quảng Ninh",
        "latitude": 20.9592,
        "longitude": 107.0215,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": True,
            "private_bathroom": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
            "max_occupants": 8,
        },
        "images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Sunset Hillside Villa hồ bơi vô cực Nam Phú Quốc",
        "description": "Biệt thự nghỉ dưỡng triền đồi Địa Trung Hải thị trấn Hoàng Hôn Sunset Town Phú Quốc. Hồ bơi vô cực trực diện biển ngắm trọn khoảnh khắc mặt trời lặn ngoạn mục, xem bắn pháo hoa Kiss Bridge hằng đêm ngay từ ban công villa.",
        "property_type": "villa",
        "listing_type": "rent",
        "rental_type": "entire_house",
        "price": 3500000.0,
        "currency": "VND",
        "area_sqm": 220.0,
        "num_bedrooms": 4,
        "num_bathrooms": 4,
        "address": "Khu đô thị Hillside, Phường An Thới",
        "ward": "Phường An Thới",
        "district": "Thành phố Phú Quốc",
        "city": "Tỉnh Kiên Giang",
        "latitude": 10.0268,
        "longitude": 104.0135,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": False,
            "private_bathroom": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
            "max_occupants": 8,
        },
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        ],
    },
    {
        "title": "Nha Trang Seaside Studio Hòn Chồng đón bình minh",
        "description": "Studio du lịch view biển Hòn Chồng đường Phạm Văn Đồng Nha Trang Khánh Hòa. Cửa kính lớn view trọn vẹn vịnh biển trong xanh, ban công ngắm nhìn đảo Hòn Đỏ. Trang bị bếp từ tiện nghi và cách chợ hải sản đêm Vĩnh Hải chỉ 500m.",
        "property_type": "apartment",
        "listing_type": "rent",
        "rental_type": "serviced_apartment",
        "price": 650000.0,
        "currency": "VND",
        "area_sqm": 40.0,
        "num_bedrooms": 1,
        "num_bathrooms": 1,
        "address": "Đường Phạm Văn Đồng, Phường Vĩnh Phước",
        "ward": "Phường Vĩnh Phước",
        "district": "Thành phố Nha Trang",
        "city": "Tỉnh Khánh Hòa",
        "latitude": 12.2745,
        "longitude": 109.2018,
        "status": "active",
        "rental_costs": {"electricity_billing": "fixed", "electricity_per_kwh": 0, "water_cost": 0, "deposit_months": 0},
        "rental_rules": {
            "curfew": False,
            "allow_pets": False,
            "private_bathroom": True,
            "has_elevator": True,
            "live_with_owner": False,
            "max_occupants": 2,
        },
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        ],
    },
]

# ==============================================================================
# 3. SAMPLE RENTAL PROPERTIES & UNITS (BOARDING HOUSES & SERVICED APARTMENTS)
# ==============================================================================
SAMPLE_RENTALS: list[dict[str, Any]] = [
    {
        "name": "Nhà Trọ Xanh Sinh Viên Bách - Kinh - Xây",
        "property_model": "boarding_house",
        "address": "Số 42 Ngõ 10 Tạ Quang Bửu, Phường Bách Khoa",
        "ward": "Phường Bách Khoa",
        "district": "Quận Hai Bà Trưng",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0055,
        "longitude": 105.8450,
        "description": "Khu nhà trọ 5 tầng mới xây sạch sẽ, camera an ninh 24/7, khóa vân tay thẻ từ, gần trường ĐH Bách Khoa, Kinh Tế Quốc Dân, Xây Dựng.",
        "shared_costs": {
            "electricity_per_kwh": 3800,
            "electricity_billing": "fixed",
            "water_cost": 100000,
            "water_unit": "per_person",
            "wifi_fee": 100000,
            "parking_fee_monthly": 100000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "P.101", "floor": 1, "area_sqm": 22.0, "price": 3800000, "deposit": 3800000, "status": "occupied", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.202", "floor": 2, "area_sqm": 25.0, "price": 4200000, "deposit": 4200000, "status": "available", "furnishing": "full", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 3},
            {"unit_number": "P.301", "floor": 3, "area_sqm": 20.0, "price": 3500000, "deposit": 3500000, "status": "available", "furnishing": "basic", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.401", "floor": 4, "area_sqm": 18.0, "price": 3200000, "deposit": 3200000, "status": "available", "furnishing": "basic", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Ký Túc Xá Cao Cấp Sinh Viên ĐHQG Cầu Giấy",
        "property_model": "boarding_house",
        "address": "Số 144 Xuân Thủy, Phường Dịch Vọng Hậu",
        "ward": "Phường Dịch Vọng Hậu",
        "district": "Quận Cầu Giấy",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0368,
        "longitude": 105.7815,
        "description": "KTX máy lạnh đầy đủ giường tầng nệm êm, tủ khóa cá nhân, phòng tự học yên tĩnh, chỉ 3 phút đi bộ sang ĐH Quốc Gia và ĐH Sư Phạm Hà Nội.",
        "shared_costs": {
            "electricity_per_kwh": 3500,
            "electricity_billing": "fixed",
            "water_cost": 80000,
            "water_unit": "per_person",
            "wifi_fee": 50000,
            "parking_fee_monthly": 80000,
        },
        "shared_rules": {
            "curfew": True,
            "curfew_time": "23:00",
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "P.201", "floor": 2, "area_sqm": 24.0, "price": 2200000, "deposit": 2200000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 4},
            {"unit_number": "P.202", "floor": 2, "area_sqm": 24.0, "price": 2200000, "deposit": 2200000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 4},
            {"unit_number": "P.303", "floor": 3, "area_sqm": 28.0, "price": 2500000, "deposit": 2500000, "status": "occupied", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 4},
        ],
    },
    {
        "name": "Căn Hộ Dịch Vụ Indochine Ba Đình",
        "property_model": "serviced_apartment",
        "address": "Số 56 Ngõ 285 Đội Cấn, Phường Liễu Giai",
        "ward": "Phường Liễu Giai",
        "district": "Quận Ba Đình",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0372,
        "longitude": 105.8142,
        "description": "Căn hộ dịch vụ phong cách hoài cổ Indochine trung tâm Ba Đình. Thang máy tốc độ cao, dọn phòng tuần 2 lần, máy giặt sấy trong phòng, cho phép nuôi thú cưng nhỏ.",
        "shared_costs": {
            "electricity_billing": "state_rate",
            "water_cost": 0,
            "wifi_fee": 0,
            "parking_fee_monthly": 120000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Studio 1A", "floor": 1, "area_sqm": 32.0, "price": 8500000, "deposit": 8500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Suite 2B", "floor": 2, "area_sqm": 45.0, "price": 11000000, "deposit": 11000000, "status": "occupied", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Căn Hộ Dịch Vụ Tây Hồ View Hồ Trúc Bạch",
        "property_model": "serviced_apartment",
        "address": "Số 15 Phố Trấn Vũ, Phường Trúc Bạch",
        "ward": "Phường Trúc Bạch",
        "district": "Quận Ba Đình",
        "city": "Thành phố Hà Nội",
        "latitude": 21.0452,
        "longitude": 105.8398,
        "description": "Căn hộ Studio cao cấp view thẳng hồ Trúc Bạch lộng gió. Không gian yên tĩnh phù hợp cho chuyên gia quốc tế, đại sứ quán và nhân viên văn phòng cao cấp.",
        "shared_costs": {
            "electricity_per_kwh": 4000,
            "electricity_billing": "fixed",
            "water_cost": 150000,
            "water_unit": "per_person",
            "wifi_fee": 0,
            "parking_fee_monthly": 150000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Studio 201", "floor": 2, "area_sqm": 35.0, "price": 9000000, "deposit": 9000000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Studio 301", "floor": 3, "area_sqm": 38.0, "price": 9500000, "deposit": 9500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Khu Nhà Trọ Sinh Viên Làng Đại Học Thủ Đức",
        "property_model": "boarding_house",
        "address": "Đường số 6, Khu phố 6, Phường Linh Trung",
        "ward": "Phường Linh Trung",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8698,
        "longitude": 106.7794,
        "description": "Nhà trọ sinh viên giá rẻ gần ĐH Nông Lâm, ĐH KHTN và KTX Khu B ĐHQG TP.HCM. Có gác lửng đúc bê tông chắc chắn, wifi cáp quang riêng từng lầu, cổng vân tay an toàn.",
        "shared_costs": {
            "electricity_per_kwh": 3500,
            "electricity_billing": "fixed",
            "water_cost": 70000,
            "water_unit": "per_person",
            "wifi_fee": 50000,
            "parking_fee_monthly": 80000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Unit A1", "floor": 1, "area_sqm": 18.0, "price": 2800000, "deposit": 2800000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Unit A2", "floor": 1, "area_sqm": 18.0, "price": 2800000, "deposit": 2800000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Unit B1", "floor": 2, "area_sqm": 22.0, "price": 3200000, "deposit": 3200000, "status": "occupied", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 3},
            {"unit_number": "Unit B2", "floor": 2, "area_sqm": 22.0, "price": 3200000, "deposit": 3200000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 3},
        ],
    },
    {
        "name": "Căn Hộ Dịch Vụ Cao Cấp Thảo Điền Riverview",
        "property_model": "serviced_apartment",
        "address": "Số 18 Đường số 41, Phường Thảo Điền",
        "ward": "Phường Thảo Điền",
        "district": "Thành phố Thủ Đức",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.8038,
        "longitude": 106.7321,
        "description": "Căn hộ dịch vụ phong cách Indochine sang trọng, có thang máy, dọn phòng 2 lần/tuần, hồ bơi sân thượng ngắm sông Sài Gòn.",
        "shared_costs": {
            "electricity_billing": "state_rate",
            "water_cost": 0,
            "wifi_fee": 0,
            "parking_fee_monthly": 150000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Studio 2A", "floor": 2, "area_sqm": 35.0, "price": 9500000, "deposit": 9500000, "status": "occupied", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Suite 4B", "floor": 4, "area_sqm": 50.0, "price": 14000000, "deposit": 14000000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Suite 5A", "floor": 5, "area_sqm": 55.0, "price": 16000000, "deposit": 16000000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Nhà Trọ Tiện Nghi Sinh Viên Quận 10",
        "property_model": "boarding_house",
        "address": "Số 268 Lý Thường Kiệt, Phường 14",
        "ward": "Phường 14",
        "district": "Quận 10",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7728,
        "longitude": 106.6578,
        "description": "Nhà trọ sinh viên tiện nghi nằm ngay đối diện cổng trường ĐH Bách Khoa TP.HCM. Có máy giặt chung sân phơi đồ lộng gió, giờ giấc tự do không chung chủ.",
        "shared_costs": {
            "electricity_per_kwh": 3800,
            "electricity_billing": "fixed",
            "water_cost": 100000,
            "water_unit": "per_person",
            "wifi_fee": 80000,
            "parking_fee_monthly": 100000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "P.101", "floor": 1, "area_sqm": 20.0, "price": 3600000, "deposit": 3600000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.102", "floor": 1, "area_sqm": 20.0, "price": 3600000, "deposit": 3600000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.201", "floor": 2, "area_sqm": 24.0, "price": 4000000, "deposit": 4000000, "status": "occupied", "furnishing": "full", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 3},
        ],
    },
    {
        "name": "Căn Hộ Dịch Vụ Studio Quận 1 Boutique",
        "property_model": "serviced_apartment",
        "address": "Số 15B Lê Thánh Tôn, Phường Bến Nghé",
        "ward": "Phường Bến Nghé",
        "district": "Quận 1",
        "city": "Thành phố Hồ Chí Minh",
        "latitude": 10.7812,
        "longitude": 106.7045,
        "description": "Khu phố Nhật Little Tokyo Quận 1, vị trí đắc địa đi bộ sang Vincom Đồng Khởi và nhà hát Thành phố. Căn hộ studio full nội thất gỗ ấm cúng, dịch vụ giặt ủi và dọn phòng chu đáo.",
        "shared_costs": {
            "electricity_per_kwh": 4200,
            "electricity_billing": "fixed",
            "water_cost": 150000,
            "water_unit": "per_person",
            "wifi_fee": 0,
            "parking_fee_monthly": 200000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Deluxe 101", "floor": 1, "area_sqm": 30.0, "price": 10500000, "deposit": 10500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Premium 202", "floor": 2, "area_sqm": 40.0, "price": 13500000, "deposit": 13500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Khu Phòng Trọ Sinh Viên ĐH Bách Khoa Đà Nẵng",
        "property_model": "boarding_house",
        "address": "Số 54 Ngô Thì Nhậm, Phường Hòa Khánh Nam",
        "ward": "Phường Hòa Khánh Nam",
        "district": "Quận Liên Chiểu",
        "city": "Thành phố Đà Nẵng",
        "latitude": 16.0745,
        "longitude": 108.1512,
        "description": "Nhà trọ sinh viên khép kín gần ĐH Bách Khoa và ĐH Sư Phạm Đà Nẵng. Khu dân cư an ninh, có sân để xe rộng rãi có mái che và camera giám sát, giá điện nước chuẩn nhà nước.",
        "shared_costs": {
            "electricity_per_kwh": 3000,
            "electricity_billing": "fixed",
            "water_cost": 50000,
            "water_unit": "per_person",
            "wifi_fee": 40000,
            "parking_fee_monthly": 50000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "P.101", "floor": 1, "area_sqm": 18.0, "price": 2200000, "deposit": 2200000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.102", "floor": 1, "area_sqm": 18.0, "price": 2200000, "deposit": 2200000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.203", "floor": 2, "area_sqm": 22.0, "price": 2600000, "deposit": 2600000, "status": "occupied", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 3},
        ],
    },
    {
        "name": "Nhà Trọ Sinh Viên Đại Học Cần Thơ",
        "property_model": "boarding_house",
        "address": "Hẻm 51 Đường 3/2, Phường Xuân Khánh",
        "ward": "Phường Xuân Khánh",
        "district": "Quận Ninh Kiều",
        "city": "Thành phố Cần Thơ",
        "latitude": 10.0285,
        "longitude": 105.7694,
        "description": "Khu nhà trọ sinh viên sạch đẹp nằm trong hẻm ẩm thực sinh viên 51 đường 3/2 quận Ninh Kiều. Đi bộ sang Khu 2 Đại học Cần Thơ chỉ 5 phút, khu trọ yên tĩnh học tập.",
        "shared_costs": {
            "electricity_per_kwh": 3000,
            "electricity_billing": "fixed",
            "water_cost": 40000,
            "water_unit": "per_person",
            "wifi_fee": 30000,
            "parking_fee_monthly": 50000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": False,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "P.01", "floor": 1, "area_sqm": 16.0, "price": 1800000, "deposit": 1800000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.02", "floor": 1, "area_sqm": 16.0, "price": 1800000, "deposit": 1800000, "status": "available", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "P.03", "floor": 2, "area_sqm": 20.0, "price": 2000000, "deposit": 2000000, "status": "occupied", "furnishing": "basic", "has_mezzanine": True, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
    {
        "name": "Căn Hộ Dịch Vụ Chuyên Gia VSIP 1 Thuận An",
        "property_model": "serviced_apartment",
        "address": "Đường D1, Khu Dân Cư Vietsing, Phường An Phú",
        "ward": "Phường An Phú",
        "district": "Thành phố Thuận An",
        "city": "Tỉnh Bình Dương",
        "latitude": 10.9325,
        "longitude": 106.7118,
        "description": "Căn hộ dịch vụ phong cách Nhật Bản & Hàn Quốc phục vụ chuyên gia làm việc tại KCN VSIP 1 và Việt Hương. Trang bị đầy đủ bếp từ, máy giặt, bồn tắm, dịch vụ dọn phòng chuyên nghiệp.",
        "shared_costs": {
            "electricity_per_kwh": 3800,
            "electricity_billing": "fixed",
            "water_cost": 100000,
            "water_unit": "per_person",
            "wifi_fee": 0,
            "parking_fee_monthly": 100000,
        },
        "shared_rules": {
            "curfew": False,
            "allow_pets": True,
            "fingerprint_lock": True,
            "live_with_owner": False,
        },
        "images": [
            "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        ],
        "units": [
            {"unit_number": "Studio S1", "floor": 2, "area_sqm": 35.0, "price": 7500000, "deposit": 7500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
            {"unit_number": "Suite S2", "floor": 3, "area_sqm": 48.0, "price": 9500000, "deposit": 9500000, "status": "available", "furnishing": "full", "has_mezzanine": False, "has_private_bathroom": True, "max_occupants": 2},
        ],
    },
]

# Alias for backward/test compatibility
SAMPLE_RENTAL_PROPERTIES = SAMPLE_RENTALS

# ==============================================================================
# 4. DEFAULT SEED USERS
# ==============================================================================
DEFAULT_SEED_USERS: list[dict[str, Any]] = [
    {
        "email": "host@space247.vn",
        "full_name": "Chủ Nhà Quản Trị Space247",
        "phone": "0933334444",
        "password": "Password123@",
        "role": UserRole.HOST.value,
        "phone_verified": True,
    },
    {
        "email": "superadmin@space247.vn",
        "full_name": "Superadmin Space247",
        "phone": "0900000001",
        "password": "Password123@",
        "role": UserRole.SUPERADMIN.value,
        "phone_verified": True,
    },
    {
        "email": "admin@space247.vn",
        "full_name": "Quản Trị Viên Space247",
        "phone": "0901234567",
        "password": "Password123@",
        "role": UserRole.ADMIN.value,
        "phone_verified": True,
    },
    {
        "email": "agent@space247.vn",
        "full_name": "Môi Giới Chuyên Nghiệp Space247",
        "phone": "0988889999",
        "password": "Password123@",
        "role": UserRole.AGENT.value,
        "phone_verified": True,
    },
    {
        "email": "user@space247.vn",
        "full_name": "Khách Hàng Mẫu Space247",
        "phone": "0912345678",
        "password": "Password123@",
        "role": UserRole.USER.value,
        "phone_verified": False,
    },
]


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """
    Seed default users (superadmin, admin, agent, user) idempotently.
    Returns a dictionary of email -> User model instances.
    """
    user_map: dict[str, User] = {}
    for item in DEFAULT_SEED_USERS:
        email = item["email"]
        stmt = select(User).where(User.email == email)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.role = item["role"]
            existing.phone_verified = item.get("phone_verified", False)
            existing.is_active = True
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
                phone_verified=item.get("phone_verified", False),
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
            p_data["geom"] = WKTElement(f"POINT({item['longitude']} {item['latitude']})", srid=4326)

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
            rental_type=item.get("rental_type"),
            rental_costs=item.get("rental_costs"),
            rental_rules=item.get("rental_rules"),
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

        if item.get("latitude") is not None and item.get("longitude") is not None:
            prop_data["geom"] = WKTElement(f"POINT({item['longitude']} {item['latitude']})", srid=4326)

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


async def seed_rental_properties(
    session: AsyncSession,
    host_id=None,
    rentals_data: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Seed two-sided RentalProperty and RentalUnit records idempotently.
    Checks existing rental properties by name and units by (property_id, unit_number).
    """
    items_to_seed = rentals_data if rentals_data is not None else SAMPLE_RENTALS
    created_props = 0
    created_units = 0
    skipped_props = 0

    logger.info("Starting rental properties seeding: %d complexes to process...", len(items_to_seed))

    for idx, item in enumerate(items_to_seed, start=1):
        stmt = select(RentalProperty).where(RentalProperty.name == item["name"])
        existing_r = (await session.execute(stmt)).scalar_one_or_none()

        if existing_r:
            r_prop = existing_r
            skipped_props += 1
            logger.info("[%d/%d] Existing rental complex: '%s'", idx, len(items_to_seed), item["name"])
        else:
            geom = None
            if item.get("latitude") is not None and item.get("longitude") is not None:
                geom = WKTElement(f"POINT({item['longitude']} {item['latitude']})", srid=4326)

            r_prop = RentalProperty(
                host_id=host_id,
                name=item["name"],
                property_model=item["property_model"],
                address=item["address"],
                ward=item["ward"],
                district=item["district"],
                city=item["city"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                geom=geom,
                description=item["description"],
                shared_costs=item["shared_costs"],
                shared_rules=item["shared_rules"],
                images=item["images"],
                is_active=True,
            )
            session.add(r_prop)
            await session.flush()
            created_props += 1
            logger.info("[%d/%d] Created rental complex: '%s' (%s - %s)", idx, len(items_to_seed), item["name"], item["property_model"], item["city"])

        # Seed units idempotently
        for u in item.get("units", []):
            stmt_u = select(RentalUnit).where(
                RentalUnit.property_id == r_prop.id,
                RentalUnit.unit_number == u["unit_number"],
            )
            existing_u = (await session.execute(stmt_u)).scalar_one_or_none()
            if existing_u:
                continue

            unit = RentalUnit(
                property_id=r_prop.id,
                unit_number=u["unit_number"],
                floor=u.get("floor"),
                area_sqm=u["area_sqm"],
                price=u["price"],
                deposit=u.get("deposit", u["price"]),
                status=u.get("status", "available"),
                furnishing=u.get("furnishing", "basic"),
                has_mezzanine=u.get("has_mezzanine", False),
                has_private_bathroom=u.get("has_private_bathroom", True),
                max_occupants=u.get("max_occupants", 2),
                images=u.get("images") or (item.get("images") or [])[:2],
            )
            session.add(unit)
            created_units += 1

    await session.commit()
    logger.info("Rental seeding finished: %d complexes created, %d skipped, %d units created.", created_props, skipped_props, created_units)
    return {
        "created_properties": created_props,
        "skipped_properties": skipped_props,
        "created_units": created_units,
    }


async def seed_contracts_invoices_and_inquiries(
    session: AsyncSession,
    agent_user: User,
    normal_user: User,
) -> dict[str, int]:
    """
    Seed sample rental contracts, monthly invoices, and rental inquiries idempotently
    for testing the Host Management Dashboard, reminder notifications, and VietQR checkout.
    """
    logger.info("--- Step 5: Seeding Sample Contracts, Invoices & Inquiries ---")
    stats = {"contracts": 0, "invoices": 0, "inquiries": 0}

    # 1. Look up units to attach contracts to
    stmt_unit1 = (
        select(RentalUnit)
        .join(RentalProperty)
        .where(RentalProperty.name == "Nhà Trọ Xanh Sinh Viên Bách - Kinh - Xây", RentalUnit.unit_number == "P.101")
    )
    unit1 = (await session.execute(stmt_unit1)).scalar_one_or_none()

    stmt_unit2 = (
        select(RentalUnit)
        .join(RentalProperty)
        .where(RentalProperty.name == "Căn Hộ Dịch Vụ Cao Cấp Thảo Điền Riverview", RentalUnit.unit_number == "Studio 2A")
    )
    unit2 = (await session.execute(stmt_unit2)).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    current_month_str = now.strftime("%Y-%m")
    # Previous month string (e.g. 2026-08)
    first_day_current_month = now.replace(day=1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    prev_month_str = last_day_prev_month.strftime("%Y-%m")

    # Contract 1: P.101
    contract1 = None
    if unit1:
        stmt_c1 = select(RentalContract).where(
            RentalContract.unit_id == unit1.id,
            RentalContract.tenant_id == normal_user.id,
            RentalContract.status == "active",
        )
        contract1 = (await session.execute(stmt_c1)).scalar_one_or_none()
        if not contract1:
            contract1 = RentalContract(
                unit_id=unit1.id,
                property_id=unit1.property_id,
                host_id=agent_user.id,
                tenant_id=normal_user.id,
                tenant_name=normal_user.full_name or "Nguyễn Văn A",
                tenant_phone=normal_user.phone or "0912345678",
                start_date=now - timedelta(days=90),
                end_date=now + timedelta(days=275),
                rental_price=float(unit1.price),
                deposit_amount=float(unit1.deposit or unit1.price),
                payment_cycle_months=1,
                electricity_rate=3800.0,
                water_rate=100000.0,
                water_billing_type="per_person",
                service_fee=100000.0,
                status="active",
            )
            session.add(contract1)
            await session.flush()
            stats["contracts"] += 1
            logger.info("Created sample active contract for unit P.101 (tenant: %s)", normal_user.email)

    # Contract 2: Studio 2A
    if unit2:
        stmt_c2 = select(RentalContract).where(
            RentalContract.unit_id == unit2.id,
            RentalContract.tenant_id == normal_user.id,
            RentalContract.status == "active",
        )
        contract2 = (await session.execute(stmt_c2)).scalar_one_or_none()
        if not contract2:
            contract2 = RentalContract(
                unit_id=unit2.id,
                property_id=unit2.property_id,
                host_id=agent_user.id,
                tenant_id=normal_user.id,
                tenant_name=normal_user.full_name or "Nguyễn Văn A",
                tenant_phone=normal_user.phone or "0912345678",
                start_date=now - timedelta(days=60),
                end_date=now + timedelta(days=305),
                rental_price=float(unit2.price),
                deposit_amount=float(unit2.deposit or unit2.price),
                payment_cycle_months=1,
                electricity_rate=3500.0,
                water_rate=25000.0,
                water_billing_type="per_m3",
                service_fee=150000.0,
                status="active",
            )
            session.add(contract2)
            await session.flush()
            stats["contracts"] += 1
            logger.info("Created sample active contract for unit Studio 2A (tenant: %s)", normal_user.email)

    # Invoices for Contract 1:
    if contract1 and unit1:
        # Invoice 1: Current month, unpaid/pending for testing debt reminder
        stmt_inv1 = select(MonthlyInvoice).where(
            MonthlyInvoice.contract_id == contract1.id,
            MonthlyInvoice.billing_month == current_month_str,
        )
        inv1 = (await session.execute(stmt_inv1)).scalar_one_or_none()
        if not inv1:
            elec_rate = float(contract1.electricity_rate)
            elec_amt = 55.0 * elec_rate
            water_amt = float(contract1.water_rate)
            svc_amt = float(contract1.service_fee)
            other_amt = 100000.0
            room_amt = float(contract1.rental_price)
            tot_amt = room_amt + elec_amt + water_amt + svc_amt + other_amt

            inv1 = MonthlyInvoice(
                contract_id=contract1.id,
                unit_id=unit1.id,
                host_id=agent_user.id,
                tenant_id=normal_user.id,
                billing_month=current_month_str,
                room_amount=room_amt,
                electricity_previous_index=120.0,
                electricity_current_index=175.0,
                electricity_rate=elec_rate,
                electricity_amount=elec_amt,
                water_previous_index=0.0,
                water_current_index=1.0,
                water_rate=float(contract1.water_rate),
                water_amount=water_amt,
                service_amount=svc_amt,
                other_amount=other_amt,
                total_amount=tot_amt,
                status="pending",
                due_date=now + timedelta(days=5),
                notes=f"Hóa đơn tiền phòng và điện nước tháng {current_month_str}",
            )
            session.add(inv1)
            stats["invoices"] += 1
            logger.info("Created sample pending monthly invoice for %s (Contract 1)", current_month_str)

        # Invoice 2: Previous month, paid
        stmt_inv2 = select(MonthlyInvoice).where(
            MonthlyInvoice.contract_id == contract1.id,
            MonthlyInvoice.billing_month == prev_month_str,
        )
        inv2 = (await session.execute(stmt_inv2)).scalar_one_or_none()
        if not inv2:
            elec_rate = float(contract1.electricity_rate)
            elec_amt = 50.0 * elec_rate
            water_amt = float(contract1.water_rate)
            svc_amt = float(contract1.service_fee)
            other_amt = 100000.0
            room_amt = float(contract1.rental_price)
            tot_amt = room_amt + elec_amt + water_amt + svc_amt + other_amt

            inv2 = MonthlyInvoice(
                contract_id=contract1.id,
                unit_id=unit1.id,
                host_id=agent_user.id,
                tenant_id=normal_user.id,
                billing_month=prev_month_str,
                room_amount=room_amt,
                electricity_previous_index=70.0,
                electricity_current_index=120.0,
                electricity_rate=elec_rate,
                electricity_amount=elec_amt,
                water_previous_index=0.0,
                water_current_index=1.0,
                water_rate=float(contract1.water_rate),
                water_amount=water_amt,
                service_amount=svc_amt,
                other_amount=other_amt,
                total_amount=tot_amt,
                status="paid",
                due_date=last_day_prev_month,
                paid_at=last_day_prev_month - timedelta(days=2),
                notes=f"Hóa đơn tiền phòng tháng {prev_month_str} (Đã thanh toán qua VietQR Napas 247)",
            )
            session.add(inv2)
            stats["invoices"] += 1
            logger.info("Created sample paid monthly invoice for %s (Contract 1)", prev_month_str)

    # 3. Rental Inquiry: P.202 available unit for VietQR reservation testing
    stmt_unit_inq = (
        select(RentalUnit)
        .join(RentalProperty)
        .where(RentalProperty.name == "Nhà Trọ Xanh Sinh Viên Bách - Kinh - Xây", RentalUnit.unit_number == "P.202")
    )
    unit_inq = (await session.execute(stmt_unit_inq)).scalar_one_or_none()
    if unit_inq:
        stmt_inq = select(RentalInquiry).where(
            RentalInquiry.unit_id == unit_inq.id,
            RentalInquiry.tenant_id == normal_user.id,
        )
        existing_inq = (await session.execute(stmt_inq)).scalar_one_or_none()
        if not existing_inq:
            inquiry = RentalInquiry(
                unit_id=unit_inq.id,
                tenant_id=normal_user.id,
                host_id=agent_user.id,
                inquiry_type="booking_request",
                tenant_name=normal_user.full_name or "Nguyễn Văn A",
                tenant_phone=normal_user.phone or "0912345678",
                message="Em chào anh chủ nhà, em là sinh viên năm 3 Bách Khoa muốn thuê phòng P.202 từ đầu tháng tới ạ.",
                status="pending",
            )
            session.add(inquiry)
            await session.flush()
            stats["inquiries"] += 1
            logger.info("Created sample pending booking inquiry for P.202 (Ready for VietQR deposit)")

            # Seed sample pending DepositTransaction
            stmt_dep = select(DepositTransaction).where(DepositTransaction.reference_code == "DEP-SAMPLE-P202")
            existing_dep = (await session.execute(stmt_dep)).scalar_one_or_none()
            if not existing_dep:
                dep_amount = float(unit_inq.deposit or 3800000.0)
                dep = DepositTransaction(
                    unit_id=unit_inq.id,
                    inquiry_id=inquiry.id,
                    tenant_id=normal_user.id,
                    host_id=agent_user.id,
                    amount=dep_amount,
                    reference_code="DEP-SAMPLE-P202",
                    payment_method="vietqr",
                    vietqr_url=f"https://img.vietqr.io/image/970422-0988889999-compact2.png?amount={int(dep_amount)}&addInfo=DEP%20SAMPLE%20P202&accountName=SPACE247%20VIETNAM",
                    status="pending",
                    expires_at=now + timedelta(minutes=30),
                )
                session.add(dep)
                logger.info("Created sample pending deposit transaction 'DEP-SAMPLE-P202'")

    await session.commit()
    logger.info("Contracts/Invoices/Inquiries seeding finished: %s", stats)
    return stats


async def reindex_all_vectors(session: AsyncSession) -> int:
    """Recompute 768-dim embeddings for all existing properties and projects in database."""
    embedding_svc = get_embedding_service()
    
    # 1. Properties
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
            rental_type=prop.rental_type,
            rental_costs=prop.rental_costs,
            rental_rules=prop.rental_rules,
        )
        prop.embedding = embedding_svc.generate_embedding(text_to_embed, is_query=False)
        updated_count += 1
        if idx % 10 == 0 or idx == len(properties):
            logger.info("Reindexed [%d/%d] properties...", idx, len(properties))

    # 2. Projects
    stmt_p = select(Project)
    res_p = await session.execute(stmt_p)
    projects = res_p.scalars().all()
    logger.info("Found %d projects to reindex vectors...", len(projects))
    for p in projects:
        text_content = (
            f"Dự án {p.name or ''}. "
            f"Chủ đầu tư: {p.developer or ''}. "
            f"Địa chỉ: {p.address or ''}, {p.district or ''}, {p.city or ''}. "
            f"Tiện ích: {', '.join(p.amenities or [])}. "
            f"{p.description or ''}"
        )
        p.embedding = embedding_svc.generate_embedding(text_content, is_query=False)

    await session.commit()
    logger.info("Vector re-indexing completed successfully: %d properties and %d projects updated.", updated_count, len(projects))
    return updated_count + len(projects)


async def main():
    """CLI runner entry point."""
    is_reindex_mode = "--reindex-vectors" in sys.argv
    logger.info("Initializing database connection for Space247 (reindex_mode=%s)...", is_reindex_mode)
    try:
        async with AsyncSessionLocal() as session:
            try:
                # 1. Seed users first
                logger.info("--- Step 1: Seeding Default Accounts ---")
                user_map = await seed_users(session=session)
                agent_user = user_map.get("agent@space247.vn")
                normal_user = user_map.get("user@space247.vn")
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

                # 4. Seed sample rental properties (Boarding house, Serviced Apartment, Homestay)
                logger.info("--- Step 4: Seeding Sample Two-Sided Rental Properties & Units ---")
                rental_stats = await seed_rental_properties(
                    session=session,
                    host_id=agent_id,
                )
                logger.info("[Space247 Rental Seed] %s", rental_stats)

                # 5. Seed sample contracts, invoices & inquiries
                if agent_user and normal_user:
                    await seed_contracts_invoices_and_inquiries(
                        session=session,
                        agent_user=agent_user,
                        normal_user=normal_user,
                    )

                # 6. Reindex vectors if requested
                if is_reindex_mode:
                    logger.info("--- Step 6: Batch Vector Re-indexing Triggered ---")
                    count = await reindex_all_vectors(session=session)
                    logger.info("[Space247 Reindex Summary] Reindexed %d properties & projects.", count)

                logger.info("=== Comprehensive Space247 Data Seeding Completed Successfully! ===")
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
