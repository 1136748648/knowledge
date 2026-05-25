import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SecurityUtilsSkill:
    """安全工具 Skill - 提供安全相关的工具方法"""

    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select)",
        r"(?i)(or\s+1\s*=\s*1)",
        r"(?i)(drop\s+table)",
        r"(?i)(--\s*$)",
        r"(?i)(/\*.*\*/)",
        r"(?i)('\s*or\s*')",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(update\s+\w+\s+set)",
        r"(?i)(exec\s+(\w+))",
    ]

    SENSITIVE_WORDS = [
        "机密", "绝密", "保密", "内部资料",
        "密码", "密钥", "token", "api_key", "secret",
        "银行卡", "身份证", "手机号", "电话",
        "攻击", "漏洞", "入侵", "黑客", "病毒",
        "工资", "薪酬", "薪资", "奖金",
    ]

    SENSITIVE_FIELDS = {
        "employees": ["salary", "phone", "clearance_level", "password", "token"],
        "conversations": ["embedding_id"],
        "users": ["password_hash", "api_key"],
        "wiki": [],
    }

    async def detect_sql_injection(self, text: str) -> Dict[str, Any]:
        """检测 SQL 注入"""
        matches = []
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text):
                matches.append(pattern)

        return {
            "has_injection": len(matches) > 0,
            "patterns_found": matches,
            "suggestion": "检测到潜在的 SQL 注入攻击，已拦截。" if matches else "安全"
        }

    async def detect_sensitive_words(self, text: str) -> Dict[str, Any]:
        """检测敏感词"""
        found = []
        for word in self.SENSITIVE_WORDS:
            if word in text:
                found.append(word)

        suggestions = []
        if found:
            suggestions.append(f"检测到 {len(found)} 个敏感词：{', '.join(found)}")
            suggestions.append("建议：请检查内容是否包含敏感信息")

        return {
            "has_sensitive": len(found) > 0,
            "sensitive_words": found,
            "suggestions": suggestions
        }

    async def mask_sensitive_fields(self, data: Dict[str, Any], resource_type: str = "") -> Dict[str, Any]:
        """敏感字段脱敏 - 支持嵌套数据结构"""
        # 确定要脱敏的字段
        fields_to_mask = set()
        if resource_type:
            fields_to_mask.update(self.SENSITIVE_FIELDS.get(resource_type, []))
        # 始终添加用户相关的敏感字段
        fields_to_mask.update(self.SENSITIVE_FIELDS.get("users", []))
        
        # 递归处理数据
        return self._mask_data(data, fields_to_mask)
    
    def _mask_data(self, data: Any, fields_to_mask: set) -> Any:
        """递归脱敏数据"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if key.lower() in [f.lower() for f in fields_to_mask]:
                    masked[key] = "***"
                else:
                    masked[key] = self._mask_data(value, fields_to_mask)
            return masked
        elif isinstance(data, list):
            return [self._mask_data(item, fields_to_mask) for item in data]
        else:
            return data


async def execute(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行安全工具 Skill"""
    skill = SecurityUtilsSkill()

    if action == "detect_sql_injection":
        return await skill.detect_sql_injection(params.get("text", ""))
    elif action == "detect_sensitive_words":
        return await skill.detect_sensitive_words(params.get("text", ""))
    elif action == "mask_sensitive_fields":
        return await skill.mask_sensitive_fields(
            params.get("data", {}),
            params.get("resource_type", "")
        )
    else:
        return {"success": False, "error": f"不支持的操作: {action}"}