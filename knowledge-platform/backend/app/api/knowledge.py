from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, NavNodeCreate, NavNodeUpdate, NavNodeResponse,
)
from app.services.nav_service import NavService

router = APIRouter()


@router.get("/nav", response_model=list[NavNodeResponse])
async def get_navigation_tree(
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取知识导航树"""
    service = NavService(db, current_user)
    return await service.get_tree()


@router.post("/nav", response_model=NavNodeResponse, status_code=201)
async def create_nav_node(
    data: NavNodeCreate,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建导航节点"""
    service = NavService(db, current_user)
    return await service.create_node(data)


@router.put("/nav/{node_id}", response_model=NavNodeResponse)
async def update_nav_node(
    node_id: UUID,
    data: NavNodeUpdate,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新导航节点"""
    service = NavService(db, current_user)
    node = await service.update_node(node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nav/{node_id}", status_code=204)
async def delete_nav_node(
    node_id: UUID,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除导航节点"""
    service = NavService(db, current_user)
    if not await service.delete_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")


@router.post("/nav/{node_id}/link")
async def link_content_to_nav(
    node_id: UUID,
    content_type: str = Query(..., pattern="^(wiki|conversation|external)$"),
    content_id: str = ...,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """关联内容到导航节点"""
    service = NavService(db, current_user)
    return await service.link_content(node_id, content_type, content_id)
