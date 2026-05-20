import logging

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# 预设分类类目
CATEGORIES = [
    {"name": "企业资料", "keywords": ["愿景", "使命", "组织架构", "证照", "简介"]},
    {"name": "工作制度", "keywords": ["考勤", "薪酬", "行政", "假期", "福利", "规定"]},
    {"name": "项目资料", "keywords": ["立项", "进度", "结项", "需求", "设计"]},
    {"name": "客户资料", "keywords": ["客户", "合同", "报价", "合作"]},
    {"name": "销售资料", "keywords": ["销售", "报价", "方案", "话术", "业绩"]},
    {"name": "运维资料", "keywords": ["巡检", "故障", "运维", "监控", "部署"]},
    {"name": "研发资料", "keywords": ["技术", "规范", "API", "代码", "架构", "开发"]},
    {"name": "软件工具", "keywords": ["工具", "手册", "使用", "教程"]},
]


class NavigationAgent:
    def __init__(self):
        self.llm = LLMService()

    async def classify(self, title: str, content: str) -> list[dict]:
        """对内容进行分类，返回推荐的导航类目"""
        # 1. 关键词匹配
        keyword_results = self._keyword_match(title + " " + content)

        # 2. LLM 增强分类
        try:
            llm_results = await self._llm_classify(title, content)
            # 合并结果，LLM 结果优先
            merged = self._merge_results(keyword_results, llm_results)
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            merged = keyword_results

        return merged[:3]  # 最多返回 3 个推荐

    def _keyword_match(self, text: str) -> list[dict]:
        """关键词匹配分类"""
        results = []
        for category in CATEGORIES:
            score = sum(1 for kw in category["keywords"] if kw in text)
            if score > 0:
                results.append({
                    "category": category["name"],
                    "confidence": min(score * 0.2, 0.9),
                    "method": "keyword",
                })
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    async def _llm_classify(self, title: str, content: str) -> list[dict]:
        """LLM 分类"""
        categories_str = ", ".join(c["name"] for c in CATEGORIES)
        prompt = f"""请将以下文档分类到最合适的类目中（最多3个）。
可选类目：{categories_str}

文档标题：{title}
文档内容摘要：{content[:500]}

请返回JSON数组格式：[{{"category": "类目名", "confidence": 0.0-1.0}}]"""

        response = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        import json
        try:
            results = json.loads(response)
            return [{"method": "llm", **r} for r in results]
        except json.JSONDecodeError:
            return []
