from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.main import create_app
from src.core.database import get_db_session
from src.api.deps import get_current_agent_user
from src.models.news import Article, NewsCategory
from src.models.user import User
from src.utils.slug import slugify_vietnamese

app = create_app()


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session


@pytest.fixture
def sample_category():
    return NewsCategory(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        name="Thị trường BĐS",
        slug="thi-truong-bds",
        description="Phân tích xu hướng",
        icon="trending-up",
        display_order=1,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_article(sample_category):
    art = Article(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        title="Xu hướng bất động sản 2026",
        slug="xu-huong-bat-dong-san-2026",
        summary="Tổng quan thị trường và các điểm sáng đầu tư.",
        content="Nội dung chi tiết bài viết với định dạng markdown.",
        thumbnail_url="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab",
        category_id=sample_category.id,
        author_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        tags=["thi truong", "dau tu"],
        view_count=100,
        is_published=True,
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    art.category = sample_category
    art.author = None
    return art


@pytest.fixture
def dummy_agent_user():
    return User(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        email="agent@space247.vn",
        hashed_password="hash",
        full_name="Chuyên Viên Tư Vấn",
        role="agent",
        is_active=True,
    )


@pytest.fixture
async def client(mock_db_session, dummy_agent_user):
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_agent_user] = lambda: dummy_agent_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def test_slugify_vietnamese():
    assert slugify_vietnamese("Đại đô thị sinh thái 2026!") == "dai-do-thi-sinh-thai-2026"
    assert slugify_vietnamese("Bất Động Sản & Quy Hoạch") == "bat-dong-san-quy-hoach"
    assert slugify_vietnamese("  Căn hộ studio cao cấp @ Q.1  ") == "can-ho-studio-cao-cap-q-1"
    assert slugify_vietnamese("") == ""


@pytest.mark.asyncio
async def test_get_news_categories(client, mock_db_session, sample_category):
    cats_res = MagicMock()
    cats_res.scalars.return_value.all.return_value = [sample_category]

    count_res = MagicMock()
    count_res.scalar.return_value = 5

    mock_db_session.execute.side_effect = [cats_res, count_res]

    response = await client.get("/api/v1/news/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Thị trường BĐS"
    assert data[0]["article_count"] == 5


@pytest.mark.asyncio
async def test_get_featured_articles(client, mock_db_session, sample_article):
    feat_res = MagicMock()
    feat_res.scalars.return_value.all.return_value = [sample_article]
    mock_db_session.execute.return_value = feat_res

    response = await client.get("/api/v1/news/featured")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Xu hướng bất động sản 2026"


@pytest.mark.asyncio
async def test_list_articles(client, mock_db_session, sample_article):
    count_res = MagicMock()
    count_res.scalar.return_value = 1

    items_res = MagicMock()
    items_res.scalars.return_value.all.return_value = [sample_article]

    mock_db_session.execute.side_effect = [count_res, items_res]

    response = await client.get("/api/v1/news?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["slug"] == "xu-huong-bat-dong-san-2026"


@pytest.mark.asyncio
async def test_get_article_by_slug(client, mock_db_session, sample_article):
    article_res = MagicMock()
    article_res.scalar_one_or_none.return_value = sample_article

    related_res = MagicMock()
    related_res.scalars.return_value.all.return_value = []

    mock_db_session.execute.side_effect = [article_res, related_res]

    response = await client.get("/api/v1/news/xu-huong-bat-dong-san-2026")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Xu hướng bất động sản 2026"
    assert "related_articles" in data
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_get_article_not_found(client, mock_db_session):
    article_res = MagicMock()
    article_res.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = article_res

    response = await client.get("/api/v1/news/non-existent-article")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_article(client, mock_db_session, sample_category, sample_article):
    # Check category
    cat_res = MagicMock()
    cat_res.scalar_one_or_none.return_value = sample_category

    # Check existing slug
    slug_res = MagicMock()
    slug_res.scalar_one_or_none.return_value = None

    # Fetch inserted article
    fetch_res = MagicMock()
    fetch_res.scalar_one.return_value = sample_article

    mock_db_session.execute.side_effect = [cat_res, slug_res, fetch_res]

    payload = {
        "title": "Phân tích giá nhà đất ven đô 2026",
        "summary": "Tóm tắt phân tích xu hướng giá bất động sản ven đô.",
        "content": "Nội dung bài viết đầy đủ với các số liệu thực tế chi tiết.",
        "category_id": str(sample_category.id),
        "tags": ["ven do", "gia nha"],
        "is_published": True,
    }
    response = await client.post("/api/v1/news", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(sample_article.id)


@pytest.mark.asyncio
async def test_delete_article(client, mock_db_session, sample_article):
    article_res = MagicMock()
    article_res.scalar_one_or_none.return_value = sample_article
    mock_db_session.execute.return_value = article_res

    response = await client.delete(f"/api/v1/news/{sample_article.id}")
    assert response.status_code == 204
    assert mock_db_session.delete.called
    assert mock_db_session.commit.called
