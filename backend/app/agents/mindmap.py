import logging

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class MindMapAgent:
    def __init__(self):
        self.llm = LLMService()

    async def generate(self, topic: str, context: str = "") -> dict:
        """生成思维导图"""
        prompt = f"""请根据以下主题生成一个思维导图的JSON结构。

主题：{topic}
{f"上下文信息：{context}" if context else ""}

要求：
1. 返回JSON格式的树形结构
2. 每个节点包含 name 和 children 字段
3. 层级不超过4层
4. 每层节点不超过7个

示例格式：
{{
  "name": "主题",
  "children": [
    {{"name": "分支1", "children": [{{"name": "叶子1"}}]}},
    {{"name": "分支2", "children": []}}
  ]
}}"""

        response = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )

        import json
        try:
            mindmap = json.loads(response)
            return {
                "format": "json",
                "data": mindmap,
                "mermaid": self._to_mermaid(mindmap),
            }
        except json.JSONDecodeError:
            return {
                "format": "text",
                "data": response,
                "mermaid": None,
            }

    def _to_mermaid(self, node: dict, indent: int = 0) -> str:
        """将 JSON 树转换为 Mermaid 格式"""
        lines = []
        prefix = "  " * indent

        if indent == 0:
            lines.append("mindmap")
            lines.append(f"  root(({node['name']}))")
        else:
            lines.append(f"{prefix}{node['name']}")

        for child in node.get("children", []):
            lines.append(self._to_mermaid(child, indent + 1))

        return "\n".join(lines)
