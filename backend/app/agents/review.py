import re
import logging

logger = logging.getLogger(__name__)

# 敏感词列表（示例）
SENSITIVE_WORDS = [
    "密码", "password", "secret", "token",
    "银行卡", "身份证", "社保号",
]


class ReviewAgent:
    async def review_content(self, content: str) -> dict:
        """审核内容，返回审核结果"""
        issues = []

        # 1. 敏感词检查
        sensitive_found = [word for word in SENSITIVE_WORDS if word.lower() in content.lower()]
        if sensitive_found:
            issues.append({
                "type": "sensitive_word",
                "words": sensitive_found,
                "message": f"检测到敏感词：{', '.join(sensitive_found)}",
            })

        # 2. Markdown 格式修正
        formatted_content = self._format_markdown(content)

        # 3. 内容质量检查
        if len(content.strip()) < 10:
            issues.append({
                "type": "too_short",
                "message": "内容过短，请补充更多信息。",
            })

        return {
            "approved": len([i for i in issues if i["type"] == "sensitive_word"]) == 0,
            "issues": issues,
            "formatted_content": formatted_content,
        }

    def _format_markdown(self, content: str) -> str:
        """Markdown 格式规范化"""
        # 移除多余空行
        content = re.sub(r"\n{3,}", "\n\n", content)
        # 确保标题后有空行
        content = re.sub(r"(^#{1,6}\s+.+)\n([^#\n])", r"\1\n\n\2", content, flags=re.MULTILINE)
        # 移除行尾空格
        content = re.sub(r" +\n", "\n", content)
        return content.strip()
