import re
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserContext
from app.services.llm_service import LLMService
from app.services.db_service import DBService
from app.services.vector_service import VectorService
from app.agents.coordinator import CoordinatorAgent

logger = logging.getLogger(__name__)

# 意图分类关键词
DB_KEYWORDS = [
    "员工", "人员", "部门", "工号", "入职", "在职", "离职",
    "项目", "负责", "参与", "成员", "负责人",
    "考勤", "迟到", "早退", "打卡", "请假", "加班",
    "绩效", "KPI", "考核", "评分", "等级", "晋升",
    "上级", "下属", "经理", "总监",
    "多少人", "几个人", "统计", "人数",
]

KB_KEYWORDS = [
    "制度", "规定", "政策", "规范", "标准", "流程",
    "年假", "假期", "福利", "薪酬", "工资",
    "报销", "费用", "财务", "发票",
    "技术", "开发", "代码", "API", "架构",
    "FAQ", "常见问题", "怎么", "如何", "为什么",
    "会议", "纪要", "记录", "决议",
    "晋升", "升级", "条件", "要求",
]

SQL_INJECTION_PATTERNS = [
    r"(?i)(union\s+select)",
    r"(?i)(or\s+1\s*=\s*1)",
    r"(?i)(drop\s+table)",
    r"(?i)(--\s*$)",
    r"(?i)(/\*.*\*/)",
    r"(?i)('\s*or\s*')",
]


class RouterAgent:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.llm = LLMService()
        self.coordinator = CoordinatorAgent(db, user)

    async def route(self, question: str) -> dict:
        """路由用户问题到正确的处理流程"""
        # 1. SQL 注入检测
        if self._detect_sql_injection(question):
            return {
                "answer": "检测到潜在的 SQL 注入攻击，已拦截。",
                "sources": [],
                "intent": "SECURITY_BLOCK",
                "confidence": 1.0,
            }

        # 2. 意图分类
        intent_result = await self._classify_intent(question)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

        logger.info(f"Question: {question}, Intent: {intent}, Confidence: {confidence}")

        # 3. 根据意图路由
        if intent == "PURE_DB":
            result = await self.coordinator.handle_db_query(question, intent_result)
        elif intent == "PURE_KB":
            result = await self.coordinator.handle_kb_query(question, intent_result)
        elif intent == "HYBRID":
            result = await self.coordinator.handle_hybrid_query(question, intent_result)
        else:  # BOUNDARY
            result = {
                "answer": "抱歉，我无法理解您的问题或该问题超出了我的知识范围。请尝试重新描述您的问题。",
                "sources": [],
            }

        return {
            **result,
            "intent": intent,
            "confidence": confidence,
        }

    def _detect_sql_injection(self, text: str) -> bool:
        """检测 SQL 注入"""
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    async def _classify_intent(self, question: str) -> dict:
        """意图分类（先用关键词，再用 LLM 增强）"""
        # 关键词匹配
        db_score = sum(1 for kw in DB_KEYWORDS if kw in question)
        kb_score = sum(1 for kw in KB_KEYWORDS if kw in question)

        # 特殊规则
        if any(kw in question for kw in ["晋升", "升级"]) and any(kw in question for kw in ["条件", "符合", "要求"]):
            return {"intent": "HYBRID", "confidence": 0.9, "entities": {}, "keywords": []}

        if any(kw in question for kw in ["迟到", "早退"]) and any(kw in question for kw in ["扣钱", "罚款", "处罚"]):
            return {"intent": "HYBRID", "confidence": 0.9, "entities": {}, "keywords": []}

        # 根据关键词得分分类
        if db_score > 0 and kb_score == 0:
            return {"intent": "PURE_DB", "confidence": min(0.5 + db_score * 0.1, 0.95), "entities": {}, "keywords": []}
        elif kb_score > 0 and db_score == 0:
            return {"intent": "PURE_KB", "confidence": min(0.5 + kb_score * 0.1, 0.95), "entities": {}, "keywords": []}
        elif db_score > 0 and kb_score > 0:
            return {"intent": "HYBRID", "confidence": 0.7, "entities": {}, "keywords": []}

        # 关键词不明确时使用 LLM
        try:
            llm_result = await self.llm.classify_intent(question)
            return llm_result
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {"intent": "BOUNDARY", "confidence": 0.3, "entities": {}, "keywords": []}
