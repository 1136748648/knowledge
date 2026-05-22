import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.navigation import KnowledgeNav, NavContentLink
from app.models.schemas import UserContext, NavNodeCreate, NavNodeUpdate


class NavService:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user

    async def get_tree(self) -> list[KnowledgeNav]:
        """获取导航树（返回顶层节点，子节点通过 relationship 加载）"""
        query = (
            select(KnowledgeNav)
            .where(KnowledgeNav.parent_id.is_(None))
            .order_by(KnowledgeNav.sort_order)
        )
        result = await self.db.execute(query)
        nodes = result.scalars().all()

        # 过滤权限不可见的节点
        visible_nodes = []
        for node in nodes:
            if self._can_view_node(node):
                visible_nodes.append(node)
        return visible_nodes

    async def get_node(self, node_id: uuid.UUID) -> KnowledgeNav | None:
        result = await self.db.execute(
            select(KnowledgeNav).where(KnowledgeNav.id == node_id)
        )
        return result.scalar_one_or_none()

    async def create_node(self, data: NavNodeCreate) -> KnowledgeNav:
        # 计算 path
        path = data.name
        if data.parent_id:
            parent = await self.get_node(data.parent_id)
            if parent:
                path = f"{parent.path}.{data.name}"

        node = KnowledgeNav(
            name=data.name,
            parent_id=data.parent_id,
            path=path,
            icon=data.icon,
            description=data.description,
            visibility_roles=data.visibility_roles,
            created_by=self.user.username,
        )
        self.db.add(node)
        await self.db.flush()
        return node

    async def update_node(self, node_id: uuid.UUID, data: NavNodeUpdate) -> KnowledgeNav | None:
        node = await self.get_node(node_id)
        if not node:
            return None

        if data.name is not None:
            node.name = data.name
        if data.parent_id is not None:
            node.parent_id = data.parent_id
        if data.icon is not None:
            node.icon = data.icon
        if data.description is not None:
            node.description = data.description
        if data.sort_order is not None:
            node.sort_order = data.sort_order
        if data.visibility_roles is not None:
            node.visibility_roles = data.visibility_roles

        await self.db.flush()
        return node

    async def delete_node(self, node_id: uuid.UUID) -> bool:
        node = await self.get_node(node_id)
        if not node:
            return False
        await self.db.delete(node)
        await self.db.flush()
        return True

    async def link_content(self, node_id: uuid.UUID, content_type: str, content_id: str) -> NavContentLink:
        link = NavContentLink(
            nav_id=node_id,
            content_type=content_type,
            content_id=content_id,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    def _can_view_node(self, node: KnowledgeNav) -> bool:
        """检查用户是否可以查看该导航节点"""
        if not node.visibility_roles:
            return True  # 空列表表示所有人可见
        if "admin" in self.user.roles:
            return True
        return any(role in self.user.roles for role in node.visibility_roles)
