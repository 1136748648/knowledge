from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, WikiPageCreate, WikiPageUpdate,
    WikiPageResponse, WikiPageListResponse,
)
from app.services.wiki_service import WikiService

router = APIRouter()


@router.get("/", response_model=list[WikiPageListResponse])
async def list_wiki_pages(
    parent_id: UUID | None = None,
    sensitivity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Wiki 页面列表"""
    service = WikiService(db, current_user)
    return await service.list_pages(parent_id, sensitivity, page, page_size)


@router.get("/{page_id}", response_model=WikiPageResponse)
async def get_wiki_page(
    page_id: UUID,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Wiki 页面详情"""
    service = WikiService(db, current_user)
    page = await service.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/", response_model=WikiPageResponse, status_code=201)
async def create_wiki_page(
    data: WikiPageCreate,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建 Wiki 页面"""
    service = WikiService(db, current_user)
    return await service.create_page(data)


@router.put("/{page_id}", response_model=WikiPageResponse)
async def update_wiki_page(
    page_id: UUID,
    data: WikiPageUpdate,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新 Wiki 页面"""
    service = WikiService(db, current_user)
    page = await service.update_page(page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.delete("/{page_id}", status_code=204)
async def delete_wiki_page(
    page_id: UUID,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除 Wiki 页面"""
    service = WikiService(db, current_user)
    if not await service.delete_page(page_id):
        raise HTTPException(status_code=404, detail="Page not found")


@router.get("/{page_id}/versions")
async def get_page_versions(
    page_id: UUID,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取页面版本历史"""
    service = WikiService(db, current_user)
    return await service.get_versions(page_id)


@router.get("/search/{query}")
async def search_wiki(
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """全文搜索 Wiki"""
    service = WikiService(db, current_user)
    return await service.search(query, page, page_size)
