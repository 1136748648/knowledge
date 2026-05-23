from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, NavNodeCreate, NavNodeUpdate, NavNodeResponse,
)
from app.services import get_knowledge_service, KnowledgeService

router = APIRouter()


@router.get("/nav", response_model=list[NavNodeResponse])
async def get_navigation_tree(
    service: KnowledgeService = Depends(get_knowledge_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取知识导航树"""
    return await service.get_tree(current_user)


@router.post("/nav", response_model=NavNodeResponse, status_code=201)
async def create_nav_node(
    data: NavNodeCreate,
    service: KnowledgeService = Depends(get_knowledge_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """创建导航节点"""
    return await service.create_node(current_user, data)


@router.put("/nav/{node_id}", response_model=NavNodeResponse)
async def update_nav_node(
    node_id: UUID,
    data: NavNodeUpdate,
    service: KnowledgeService = Depends(get_knowledge_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """更新导航节点"""
    node = await service.update_node(current_user, node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nav/{node_id}", status_code=204)
async def delete_nav_node(
    node_id: UUID,
    service: KnowledgeService = Depends(get_knowledge_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """删除导航节点"""
    if not await service.delete_node(current_user, node_id):
        raise HTTPException(status_code=404, detail="Node not found")


@router.post("/nav/{node_id}/link")
async def link_content_to_nav(
    node_id: UUID,
    content_type: str = Query(..., pattern="^(wiki|conversation|external)$"),
    content_id: str = ...,
    service: KnowledgeService = Depends(get_knowledge_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """关联内容到导航节点"""
    return await service.link_content(current_user, node_id, content_type, content_id)