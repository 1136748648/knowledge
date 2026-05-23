from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, WikiPageCreate, WikiPageUpdate,
    WikiPageResponse, WikiPageListResponse,
)
from app.services import get_wiki_service, WikiService

router = APIRouter()


@router.get("/", response_model=list[WikiPageListResponse])
async def list_wiki_pages(
    parent_id: UUID | None = None,
    sensitivity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取 Wiki 页面列表"""
    return await service.list_pages(current_user, parent_id, sensitivity, page, page_size)


@router.get("/{page_id}", response_model=WikiPageResponse)
async def get_wiki_page(
    page_id: UUID,
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取 Wiki 页面详情"""
    page = await service.get_page(current_user, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/", response_model=WikiPageResponse, status_code=201)
async def create_wiki_page(
    data: WikiPageCreate,
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """创建 Wiki 页面"""
    return await service.create_page(current_user, data)


@router.put("/{page_id}", response_model=WikiPageResponse)
async def update_wiki_page(
    page_id: UUID,
    data: WikiPageUpdate,
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """更新 Wiki 页面"""
    page = await service.update_page(current_user, page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.delete("/{page_id}", status_code=204)
async def delete_wiki_page(
    page_id: UUID,
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """删除 Wiki 页面"""
    if not await service.delete_page(current_user, page_id):
        raise HTTPException(status_code=404, detail="Page not found")


@router.get("/{page_id}/versions")
async def get_page_versions(
    page_id: UUID,
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取页面版本历史"""
    return await service.get_versions(current_user, page_id)


@router.get("/search/{query}")
async def search_wiki(
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: WikiService = Depends(get_wiki_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """全文搜索 Wiki"""
    return await service.search(current_user, query, page, page_size)