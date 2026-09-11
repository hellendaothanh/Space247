from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class NewsCategoryBase(BaseModel):
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    display_order: int = 0


class NewsCategoryResponse(NewsCategoryBase):
    id: UUID
    article_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ArticleAuthor(BaseModel):
    id: UUID
    full_name: str | None = None
    email: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    summary: str
    thumbnail_url: str | None = None
    category_id: UUID
    category: NewsCategoryResponse | None = None
    author_id: UUID | None = None
    author: ArticleAuthor | None = None
    tags: list[str] = []
    view_count: int = 0
    is_published: bool = True
    published_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleDetailResponse(ArticleListItem):
    content: str
    related_articles: list[ArticleListItem] = []

    model_config = ConfigDict(from_attributes=True)


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    slug: str | None = Field(None, max_length=300)
    summary: str = Field(..., min_length=10)
    content: str = Field(..., min_length=20)
    thumbnail_url: str | None = None
    category_id: UUID
    tags: list[str] = []
    is_published: bool = True


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=255)
    slug: str | None = Field(None, max_length=300)
    summary: str | None = Field(None, min_length=10)
    content: str | None = Field(None, min_length=20)
    thumbnail_url: str | None = None
    category_id: UUID | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class ArticlePaginationResponse(BaseModel):
    items: list[ArticleListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
