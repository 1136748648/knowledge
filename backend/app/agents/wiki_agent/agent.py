import logging

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry

logger = logging.getLogger(__name__)


class WikiAgent:
    """Wiki Agent - Wiki 文档管理服务（重新设计中）"""
    
    CAPABILITY = AgentCapability(
        agent_id="wiki_agent",
        name="Wiki Agent",
        description="Wiki 文档管理服务，支持文档搜索、创建、更新、删除（重新设计中）",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "get_page", "create_page", "update_page", "delete_page", "list_pages", "get_versions"]
                },
                "query": {"type": "string"},
                "page_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "slug": {"type": "string"},
                "parent_id": {"type": "string"},
                "sensitivity": {"type": "string", "enum": ["public", "internal", "confidential", "secret"]},
                "dept_id": {"type": "string"},
                "page": {"type": "integer"},
                "page_size": {"type": "integer"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "slug": {"type": "string"},
                "parent_id": {"type": "string"},
                "sensitivity": {"type": "string"},
                "dept_id": {"type": "string"},
                "created_by": {"type": "string"},
                "updated_by": {"type": "string"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "items": {"type": "array"},
                "total": {"type": "integer"}
            }
        },
        supported_intents=["PURE_KB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    def __init__(self, db=None, user=None):
        self.db = db
        self.user = user
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        logger.warning("WikiAgent is currently being redesigned. All operations are temporarily unavailable.")
        return MCPResponse(
            success=False,
            error="Wiki 功能正在重新设计中，暂不可用",
            confidence=0.0
        )


def register_agent() -> None:
    """注册 Wiki Agent"""
    registry = get_registry()
    registry.register(WikiAgent.CAPABILITY, WikiAgent)
