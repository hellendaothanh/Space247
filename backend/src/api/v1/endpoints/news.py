import math
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_agent_user
from src.core.database import get_db_session
from src.models.news import Article, NewsCategory
from src.models.user import User
from src.schemas.news import (
    ArticleCreate,
    ArticleDetailResponse,
    ArticleListItem,
    ArticlePaginationResponse,
    ArticleUpdate,
    NewsCategoryResponse,
)
from src.utils.slug import slugify_vietnamese

router = APIRouter()


@router.get(
    "/categories",
    response_model=list[NewsCategoryResponse],
    summary="Get all news categories with published article counts",
)
async def get_news_categories(
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve all news categories ordered by display_order with article counts."""
    cats_stmt = select(NewsCategory).order_by(NewsCategory.display_order.asc())
    cats_result = await db.execute(cats_stmt)
    categories = cats_result.scalars().all()

    response = []
    for cat in categories:
        count_stmt = (
            select(func.count(Article.id))
            .where(Article.category_id == cat.id, Article.is_published.is_(True))
        )
        count_res = await db.execute(count_stmt)
        count = count_res.scalar() or 0
        response.append(
            NewsCategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                icon=cat.icon,
                display_order=cat.display_order,
                article_count=count,
            )
        )
    return response


@router.get(
    "/featured",
    response_model=list[ArticleListItem],
    summary="Get top 5 featured/most viewed articles",
)
async def get_featured_articles(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve top featured articles ordered by view count and publication date."""
    stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(Article.is_published.is_(True))
        .order_by(Article.view_count.desc(), Article.published_at.desc().nullslast())
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return articles


@router.get(
    "",
    response_model=ArticlePaginationResponse,
    summary="List news articles with pagination, category filter, tag, and search",
)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category_slug: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Paginated list of published articles with rich filters."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(Article.is_published.is_(True))
    )

    if category_slug:
        query = query.join(NewsCategory, Article.category_id == NewsCategory.id).where(
            NewsCategory.slug == category_slug
        )

    if tag:
        # DB-agnostic tag search via array string conversion
        query = query.where(func.array_to_string(Article.tags, ",").ilike(f"%{tag}%"))

    if q:
        query = query.where(
            or_(
                Article.title.ilike(f"%{q}%"),
                Article.summary.ilike(f"%{q}%"),
            )
        )

    # Count total
    count_subquery = query.with_only_columns(func.count(Article.id)).order_by(None)
    total_res = await db.execute(count_subquery)
    total = total_res.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    paged_stmt = (
        query.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(paged_stmt)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ArticlePaginationResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{slug}",
    response_model=ArticleDetailResponse,
    summary="Get single article details and increment view count",
)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve full article detail by slug or UUID, increment view_count, and return related articles."""
    # Support lookup by slug or by UUID if provided
    conditions = [Article.slug == slug]
    try:
        parsed_uuid = uuid.UUID(slug)
        conditions.append(Article.id == parsed_uuid)
    except ValueError:
        pass

    stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(or_(*conditions), Article.is_published.is_(True))
    )
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bài viết không tồn tại hoặc chưa được xuất bản.",
        )

    # Increment view count
    article.view_count += 1
    await db.commit()
    await db.refresh(article)

    # Fetch 3 related articles from same category
    related_stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(
            Article.category_id == article.category_id,
            Article.id != article.id,
            Article.is_published.is_(True),
        )
        .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .limit(3)
    )
    related_res = await db.execute(related_stmt)
    related_articles = related_res.scalars().all()

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        slug=article.slug,
        summary=article.summary,
        content=article.content,
        thumbnail_url=article.thumbnail_url,
        category_id=article.category_id,
        category=article.category,
        author_id=article.author_id,
        author=article.author,
        tags=article.tags or [],
        view_count=article.view_count,
        is_published=article.is_published,
        published_at=article.published_at,
        created_at=article.created_at,
        related_articles=list(related_articles),
    )


@router.post(
    "",
    response_model=ArticleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new news article (Agent/Admin/Superadmin only)",
)
async def create_article(
    payload: ArticleCreate,
    current_user: User = Depends(get_current_agent_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Publish a new editorial article with auto-generated Vietnamese slug."""
    # Verify category exists
    cat_stmt = select(NewsCategory).where(NewsCategory.id == payload.category_id)
    cat_res = await db.execute(cat_stmt)
    category = cat_res.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh mục bài viết không tồn tại.",
        )

    # Generate or sanitize slug
    base_slug = payload.slug.strip() if payload.slug else slugify_vietnamese(payload.title)
    if not base_slug:
        base_slug = f"bai-viet-{uuid.uuid4().hex[:8]}"

    final_slug = base_slug
    suffix = 1
    while True:
        check_slug_stmt = select(Article.id).where(Article.slug == final_slug)
        existing = await db.execute(check_slug_stmt)
        if not existing.scalar_one_or_none():
            break
        final_slug = f"{base_slug}-{suffix}"
        suffix += 1

    now = datetime.now(timezone.utc)
    new_article = Article(
        id=uuid.uuid4(),
        title=payload.title.strip(),
        slug=final_slug,
        summary=payload.summary.strip(),
        content=payload.content.strip(),
        thumbnail_url=payload.thumbnail_url,
        category_id=payload.category_id,
        author_id=current_user.id,
        tags=payload.tags,
        view_count=0,
        is_published=payload.is_published,
        published_at=now if payload.is_published else None,
        created_at=now,
        updated_at=now,
    )

    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)

    # Re-fetch with relationships
    stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(Article.id == new_article.id)
    )
    res = await db.execute(stmt)
    full_article = res.scalar_one()

    return ArticleDetailResponse(
        id=full_article.id,
        title=full_article.title,
        slug=full_article.slug,
        summary=full_article.summary,
        content=full_article.content,
        thumbnail_url=full_article.thumbnail_url,
        category_id=full_article.category_id,
        category=full_article.category,
        author_id=full_article.author_id,
        author=full_article.author,
        tags=full_article.tags or [],
        view_count=full_article.view_count,
        is_published=full_article.is_published,
        published_at=full_article.published_at,
        created_at=full_article.created_at,
        related_articles=[],
    )


@router.put(
    "/{article_id}",
    response_model=ArticleDetailResponse,
    summary="Update an existing article (Author/Admin/Superadmin only)",
)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    current_user: User = Depends(get_current_agent_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update article content or metadata."""
    stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.author))
        .where(Article.id == article_id)
    )
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bài viết không tồn tại.",
        )

    # Authorization: author or admin or superadmin
    if current_user.role not in ("admin", "superadmin") and article.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa bài viết này.",
        )

    if payload.title is not None:
        article.title = payload.title.strip()
    if payload.slug is not None:
        article.slug = payload.slug.strip()
    if payload.summary is not None:
        article.summary = payload.summary.strip()
    if payload.content is not None:
        article.content = payload.content.strip()
    if payload.thumbnail_url is not None:
        article.thumbnail_url = payload.thumbnail_url
    if payload.category_id is not None:
        # Check category exists
        cat_res = await db.execute(select(NewsCategory).where(NewsCategory.id == payload.category_id))
        if not cat_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Danh mục bài viết không tồn tại.",
            )
        article.category_id = payload.category_id
    if payload.tags is not None:
        article.tags = payload.tags
    if payload.is_published is not None:
        article.is_published = payload.is_published
        if payload.is_published and not article.published_at:
            article.published_at = datetime.now(timezone.utc)

    article.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(article)

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        slug=article.slug,
        summary=article.summary,
        content=article.content,
        thumbnail_url=article.thumbnail_url,
        category_id=article.category_id,
        category=article.category,
        author_id=article.author_id,
        author=article.author,
        tags=article.tags or [],
        view_count=article.view_count,
        is_published=article.is_published,
        published_at=article.published_at,
        created_at=article.created_at,
        related_articles=[],
    )


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an article (Author/Admin/Superadmin only)",
)
async def delete_article(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_agent_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Permanently delete an article."""
    stmt = select(Article).where(Article.id == article_id)
    res = await db.execute(stmt)
    article = res.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bài viết không tồn tại.",
        )

    if current_user.role not in ("admin", "superadmin") and article.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa bài viết này.",
        )

    await db.delete(article)
    await db.commit()
    return None
