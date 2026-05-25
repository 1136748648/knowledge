import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcps import AgentCapability, MCPRequest, MCPResponse, create_mcp_client, get_registry
from app.models.schemas import UserContext
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """编排 Agent - 意图识别、任务分解、跨Agent协调、结果聚合"""

    CAPABILITY = AgentCapability(
        agent_id="orchestrator_agent",
        name="编排 Agent",
        description="任务编排服务，支持意图识别、任务分解、跨Agent协调、结果聚合",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["process_query", "classify_intent", "dispatch_tasks"]},
                "query": {"type": "string"},
                "tasks": {"type": "array"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "sources": {"type": "array"},
                "intent": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
        supported_intents=["PURE_DB", "PURE_KB", "HYBRID"],
        version="1.0",
        priority=5
    )

    DB_KEYWORDS = ["员工", "人员", "部门", "工号", "入职", "在职", "离职", "项目", "负责"]
    KB_KEYWORDS = ["制度", "规定", "政策", "规范", "标准", "流程", "技术", "开发", "FAQ"]

    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.mcp_client = create_mcp_client(db, user)
        self.llm = LLMService()

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        action = request.params.get("action")

        try:
            if action == "process_query":
                query = request.params.get("query", "")
                result = await self.process_query(query)
                return MCPResponse(
                    success=True,
                    data=result,
                    sources=result.get("sources", []),
                    confidence=result.get("confidence", 0.0)
                )

            elif action == "classify_intent":
                query = request.params.get("query", "")
                result = await self.classify_intent(query)
                return MCPResponse(
                    success=True,
                    data=result,
                    sources=[{"type": "orchestrator", "action": "classify_intent"}],
                    confidence=result.get("confidence", 0.0)
                )

            elif action == "dispatch_tasks":
                tasks = request.params.get("tasks", [])
                results = await self.dispatch_tasks(tasks)
                return MCPResponse(
                    success=True,
                    data={"results": results},
                    sources=[{"type": "orchestrator", "action": "dispatch_tasks"}],
                    confidence=1.0
                )

            else:
                return MCPResponse(success=False, error=f"不支持的操作: {action}", confidence=0.0)

        except Exception as e:
            logger.error(f"OrchestratorAgent error: {str(e)}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)

    async def process_query(self, query: str) -> dict:
        """处理用户查询"""
        intent_result = await self.classify_intent(query)
        intent = intent_result["intent"]

        if intent == "PURE_DB":
            return await self.handle_db_query(query)
        elif intent == "PURE_KB":
            return await self.handle_kb_query(query)
        elif intent == "HYBRID":
            return await self.handle_hybrid_query(query)
        else:
            return {"answer": "抱歉，我无法理解您的问题。", "sources": [], "intent": intent, "confidence": 0.3}

    async def classify_intent(self, query: str) -> dict:
        """意图分类"""
        db_score = sum(1 for kw in self.DB_KEYWORDS if kw in query)
        kb_score = sum(1 for kw in self.KB_KEYWORDS if kw in query)

        if db_score > 0 and kb_score == 0:
            return {"intent": "PURE_DB", "confidence": min(0.5 + db_score * 0.1, 0.95)}
        elif kb_score > 0 and db_score == 0:
            return {"intent": "PURE_KB", "confidence": min(0.5 + kb_score * 0.1, 0.95)}
        elif db_score > 0 and kb_score > 0:
            return {"intent": "HYBRID", "confidence": 0.7}

        try:
            llm_result = await self.llm.classify_intent(query)
            return llm_result
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {"intent": "BOUNDARY", "confidence": 0.3}

    def _extract_name(self, query: str) -> str:
        """从查询中提取姓名"""
        name_pattern = r'叫(.+?)[的？?]|找(.+?)[的？?]|(.+?)的信息'
        match = re.search(name_pattern, query)
        if match:
            for group in match.groups():
                if group and len(group.strip()) >= 2:
                    return group.strip()
        return ""

    def _extract_department(self, query: str) -> str:
        """从查询中提取部门"""
        dept_pattern = r'(.+?)部|(.+?)部门|在(.+?)的'
        match = re.search(dept_pattern, query)
        if match:
            for group in match.groups():
                if group and len(group.strip()) >= 2:
                    return group.strip() + "部"
        return ""

    async def handle_db_query(self, query: str) -> dict:
        """处理数据库查询 - 改进版，能提取查询参数"""
        # 尝试提取姓名或部门
        name = self._extract_name(query)
        department = self._extract_department(query)
        
        all_sources = []
        
        # 如果有姓名，先按姓名查找
        if name:
            params = {"action": "get_employee_by_name", "employee_name": name}
            response = await self.mcp_client.call("db_agent", MCPRequest(action="get_employee_by_name", params=params))
            
            if response.success and response.data:
                all_sources.extend(response.sources or [])
                return {
                    "answer": f"找到员工信息：\n{self._format_employee_data(response.data)}",
                    "sources": all_sources,
                    "intent": "PURE_DB",
                    "confidence": response.confidence
                }
        
        # 如果有部门，查找部门员工
        if department:
            params = {"action": "get_employees_by_department", "department": department}
            response = await self.mcp_client.call("db_agent", MCPRequest(action="get_employees_by_department", params=params))
            
            if response.success and response.data:
                all_sources.extend(response.sources or [])
                answer = f"{department}的员工列表：\n"
                for emp in response.data:
                    answer += f"- {emp.get('name', 'N/A')} ({emp.get('level', 'N/A')})\n"
                return {
                    "answer": answer,
                    "sources": all_sources,
                    "intent": "PURE_DB",
                    "confidence": response.confidence
                }
        
        # 默认尝试查找
        return {"answer": "未找到相关数据，请尝试提供更具体的员工姓名或部门。", "sources": [], "intent": "PURE_DB", "confidence": 0.0}

    def _format_employee_data(self, data: dict) -> str:
        """格式化员工数据"""
        if not data:
            return ""
        return (
            f"姓名：{data.get('name', 'N/A')}\n"
            f"部门：{data.get('department', 'N/A')}\n"
            f"职位：{data.get('level', 'N/A')}\n"
            f"邮箱：{data.get('email', 'N/A')}\n"
            f"状态：{data.get('status', 'N/A')}"
        )

    async def handle_kb_query(self, query: str) -> dict:
        """处理知识库查询"""
        params = {"action": "search", "query": query}
        response = await self.mcp_client.call("wiki_agent", MCPRequest(action="search", params=params))

        if response.success and response.data:
            sources = response.sources or []
            # 确保 sources 中的数据格式正确
            formatted_sources = []
            for source in sources:
                if isinstance(source, dict) and "data" not in source:
                    source["data"] = response.data
                formatted_sources.append(source)
            
            return {
                "answer": str(response.data),
                "sources": formatted_sources,
                "intent": "PURE_KB",
                "confidence": response.confidence
            }
        return {"answer": "未找到相关文档。", "sources": [], "intent": "PURE_KB", "confidence": 0.0}

    async def handle_hybrid_query(self, query: str) -> dict:
        """处理混合查询"""
        db_result = await self.handle_db_query(query)
        kb_result = await self.handle_kb_query(query)

        answer = db_result["answer"]
        if "未找到" not in kb_result["answer"]:
            answer += f"\n\n相关文档：\n{kb_result['answer']}"

        return {
            "answer": answer,
            "sources": db_result["sources"] + kb_result["sources"],
            "intent": "HYBRID",
            "confidence": (db_result["confidence"] + kb_result["confidence"]) / 2
        }

    async def dispatch_tasks(self, tasks: list) -> list:
        """分发任务到各个 Agent"""
        results = []
        for task in tasks:
            agent_id = task.get("agent_id")
            action = task.get("action")
            params = task.get("params", {})

            response = await self.mcp_client.call(agent_id, MCPRequest(action=action, params=params))
            results.append({
                "agent_id": agent_id,
                "success": response.success,
                "data": response.data
            })
        return results


def register_agent() -> None:
    registry = get_registry()
    registry.register(OrchestratorAgent.CAPABILITY, OrchestratorAgent)