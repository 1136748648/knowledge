from typing import Optional
import uuid
from app.dal import KnowledgeNavRepository, NavContentLinkRepository
from app.models.schemas import UserContext, NavNodeCreate, NavNodeUpdate


class KnowledgeService:
    def __init__(
        self,
        nav_repo: KnowledgeNavRepository,
        link_repo: NavContentLinkRepository,
    ):
        self.nav_repo = nav_repo
        self.link_repo = link_repo

    async def get_tree(self, user: UserContext):
        nodes = await self.nav_repo.get_root_nodes()
        return [node for node in nodes if self._can_view_node(user, node)]

    async def get_node(self, node_id: uuid.UUID):
        return await self.nav_repo.get_by_id(node_id)

    async def create_node(self, user: UserContext, data: NavNodeCreate):
        path = data.name
        if data.parent_id:
            parent = await self.get_node(data.parent_id)
            if parent:
                path = f"{parent.path}.{data.name}"

        from app.models.navigation import KnowledgeNav

        node = KnowledgeNav(
            name=data.name,
            parent_id=data.parent_id,
            path=path,
            icon=data.icon,
            description=data.description,
            visibility_roles=data.visibility_roles,
            created_by=user.username,
        )
        return await self.nav_repo.create(node)

    async def update_node(self, user: UserContext, node_id: uuid.UUID, data: NavNodeUpdate):
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

        return await self.nav_repo.update(node)

    async def delete_node(self, user: UserContext, node_id: uuid.UUID) -> bool:
        node = await self.get_node(node_id)
        if not node:
            return False
        return await self.nav_repo.delete(node_id)

    async def link_content(
        self,
        user: UserContext,
        node_id: uuid.UUID,
        content_type: str,
        content_id: str,
    ):
        from app.models.navigation import NavContentLink

        link = NavContentLink(
            nav_id=node_id,
            content_type=content_type,
            content_id=content_id,
        )
        return await self.link_repo.create(link)

    def _can_view_node(self, user: UserContext, node) -> bool:
        if not node.visibility_roles:
            return True
        if "admin" in user.roles:
            return True
        return any(role in user.roles for role in node.visibility_roles)