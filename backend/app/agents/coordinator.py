import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserContext
from app.services.db_service import DBService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.db_service = DBService(db, user)
        self.llm = LLMService()

    async def handle_db_query(self, question: str, intent_result: dict) -> dict:
        """处理纯数据库查询"""
        # 提取实体
        entities = intent_result.get("entities", {})
        employee_names = entities.get("employee_names", [])
        departments = entities.get("departments", [])

        # 尝试匹配员工
        employee = None
        if employee_names:
            employee = await self.db_service.get_employee_by_name(employee_names[0])

        if employee:
            # 根据问题类型生成回答
            answer = await self._generate_db_answer(question, employee)
            return {
                "answer": answer,
                "sources": [{"type": "database", "table": "employees", "id": employee.employee_id}],
            }

        if departments:
            count = await self.db_service.count_employees_by_department(departments[0])
            return {
                "answer": f"{departments[0]}共有 {count} 人。",
                "sources": [{"type": "database", "table": "employees", "filter": f"department={departments[0]}"}],
            }

        return {
            "answer": "未找到相关的员工信息。",
            "sources": [],
        }

    async def handle_kb_query(self, question: str, intent_result: dict) -> dict:
        """处理纯知识库查询"""
        # TODO: 调用向量搜索
        return {
            "answer": "知识库查询功能正在开发中。",
            "sources": [],
        }

    async def handle_hybrid_query(self, question: str, intent_result: dict) -> dict:
        """处理混合查询（数据库 + 知识库）"""
        # TODO: 跨库联合查询
        return {
            "answer": "混合查询功能正在开发中。",
            "sources": [],
        }

    async def _generate_db_answer(self, question: str, employee) -> str:
        """根据问题生成数据库查询回答"""
        # 简单的规则匹配，后续可用 LLM 增强
        if "部门" in question:
            return f"{employee.name}的部门是{employee.department}。"
        elif "上级" in question or "领导" in question:
            if employee.manager_id:
                manager = await self.db_service.get_employee_by_id(employee.manager_id)
                if manager:
                    return f"{employee.name}的上级是{manager.name}（{manager.employee_id}）。"
            return f"{employee.name}没有上级信息。"
        elif "工号" in question:
            return f"{employee.name}的工号是{employee.employee_id}。"
        elif "入职" in question:
            return f"{employee.name}的入职日期是{employee.hire_date}。"
        elif "职级" in question or "级别" in question:
            return f"{employee.name}的职级是{employee.level}。"
        else:
            return (
                f"员工信息：\n"
                f"- 姓名：{employee.name}\n"
                f"- 工号：{employee.employee_id}\n"
                f"- 部门：{employee.department}\n"
                f"- 职级：{employee.level}\n"
                f"- 状态：{employee.status}"
            )
