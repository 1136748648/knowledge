import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.security import SecurityAgent
from app.agents.orchestrator import OrchestratorAgent
from app.models.schemas import UserContext
from app.mcps import MCPRequest
from app.dal import get_adapter

logger = logging.getLogger(__name__)


class QAService:
    def __init__(self):
        pass

    async def ask_question(self, user: UserContext, question: str, db_session: AsyncSession = None) -> dict:
        """
        按设计文档执行问答流程：
        1. SecurityAgent: SQL注入检测 + 权限检查
        2. OrchestratorAgent: 意图识别 + 任务分发
        3. 结果处理（脱敏）
        """
        # 获取数据库会话（如果未提供）
        own_session = False
        if db_session is None:
            adapter = get_adapter()
            db_session = await adapter.get_session()
            own_session = True
        
        try:
            # 步骤 1: 安全检查 - SQL注入检测
            security_agent = SecurityAgent(db_session, user)
            sql_check_request = MCPRequest(
                agent_id="security_agent",
                params={"action": "check_sql_injection", "text": question}
            )
            sql_check_response = await security_agent.handle_request(sql_check_request)
            
            if not sql_check_response.success:
                return {
                    "answer": "安全检查失败，请重试。",
                    "sources": [],
                    "intent": "error",
                    "confidence": 0.0
                }
            
            if sql_check_response.data.get("has_injection", False):
                logger.warning(f"SQL injection attempt detected: {question}")
                return {
                    "answer": "检测到潜在的安全风险，请求已被拦截。",
                    "sources": [],
                    "intent": "error",
                    "confidence": 0.0
                }
            
            # 步骤 2: 权限检查
            permission_check = MCPRequest(
                agent_id="security_agent",
                params={"action": "check_permission", "resource": "qa", "action_type": "query"}
            )
            permission_response = await security_agent.handle_request(permission_check)
            
            if not permission_response.success or not permission_response.data.get("allowed", False):
                return {
                    "answer": "您没有权限执行此操作。",
                    "sources": [],
                    "intent": "error",
                    "confidence": 0.0
                }
            
            # 步骤 3: 调用编排 Agent 处理查询
            orchestrator = OrchestratorAgent(db_session, user)
            result = await orchestrator.process_query(question)
            
            # 步骤 4: 对结果进行脱敏处理
            if "sources" in result:
                masked_sources = []
                for source in result["sources"]:
                    if isinstance(source, dict):
                        resource_type = source.get("type", "unknown")
                        data_to_mask = source.get("data", source)
                        
                        # 调用 SecurityAgent 进行脱敏
                        mask_request = MCPRequest(
                            agent_id="security_agent",
                            params={
                                "action": "mask_sensitive",
                                "data": data_to_mask,
                                "resource_type": resource_type
                            }
                        )
                        mask_response = await security_agent.handle_request(mask_request)
                        
                        if mask_response.success:
                            masked_source = source.copy()
                            # mask_sensitive 直接在 data 键中返回结果
                            masked_source["data"] = mask_response.data.get("data", data_to_mask)
                            masked_sources.append(masked_source)
                        else:
                            masked_sources.append(source)
                    else:
                        masked_sources.append(source)
                result["sources"] = masked_sources
            
            # 确保 intent 字段存在
            if "intent" not in result:
                result["intent"] = "unknown"
            
            return result
            
        finally:
            # 只关闭我们自己创建的会话
            if own_session and db_session is not None:
                try:
                    await db_session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
