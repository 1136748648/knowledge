import os
import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig
from app.core.encryption import encrypt, decrypt

logger = logging.getLogger(__name__)

# 配置字段定义：每个分类的字段及其元数据
# env_key: 对应的 .env 变量名（不填则默认 CATEGORY_KEY）
CONFIG_SCHEMA: dict[str, list[dict]] = {
    "database": [
        {"key": "url", "type": "string", "description": "PostgreSQL 连接串", "sensitive": False, "env_key": "DATABASE_URL"},
    ],
    "redis": [
        {"key": "url", "type": "string", "description": "Redis 连接串", "sensitive": False, "env_key": "REDIS_URL"},
    ],
    "milvus": [
        {"key": "host", "type": "string", "description": "Milvus 主机地址", "sensitive": False, "env_key": "MILVUS_HOST"},
        {"key": "port", "type": "int", "description": "Milvus 端口", "sensitive": False, "env_key": "MILVUS_PORT"},
        {"key": "collection", "type": "string", "description": "Milvus Collection 名称", "sensitive": False, "env_key": "MILVUS_COLLECTION"},
    ],
    "keycloak": [
        {"key": "server_url", "type": "string", "description": "Keycloak 服务地址", "sensitive": False, "env_key": "KEYCLOAK_SERVER_URL"},
        {"key": "realm", "type": "string", "description": "Keycloak Realm", "sensitive": False, "env_key": "KEYCLOAK_REALM"},
        {"key": "client_id", "type": "string", "description": "Client ID", "sensitive": False, "env_key": "KEYCLOAK_CLIENT_ID"},
        {"key": "client_secret", "type": "password", "description": "Client Secret", "sensitive": True, "env_key": "KEYCLOAK_CLIENT_SECRET"},
    ],
    "llm": [
        {"key": "provider", "type": "string", "description": "LLM 提供商", "sensitive": False, "env_key": "LLM_PROVIDER"},
        {"key": "api_key", "type": "password", "description": "API Key", "sensitive": True, "env_key": "LLM_API_KEY"},
        {"key": "api_base", "type": "string", "description": "API Base URL", "sensitive": False, "env_key": "LLM_API_BASE"},
        {"key": "model", "type": "string", "description": "聊天模型", "sensitive": False, "env_key": "LLM_MODEL"},
        {"key": "embedding_model", "type": "string", "description": "嵌入模型", "sensitive": False, "env_key": "LLM_EMBEDDING_MODEL"},
        {"key": "embedding_dim", "type": "int", "description": "嵌入维度", "sensitive": False, "env_key": "LLM_EMBEDDING_DIM"},
        {"key": "secret_key", "type": "password", "description": "Secret Key", "sensitive": True, "env_key": "LLM_SECRET_KEY"},
    ],
    "security": [
        {"key": "cors_origins", "type": "json", "description": "CORS 允许的来源", "sensitive": False, "env_key": "CORS_ORIGINS"},
        {"key": "jwt_algorithm", "type": "string", "description": "JWT 算法", "sensitive": False, "env_key": "JWT_ALGORITHM"},
    ],
    "audit": [
        {"key": "enabled", "type": "bool", "description": "是否启用审计日志", "sensitive": False, "env_key": "AUDIT_LOG_ENABLED"},
    ],
    "system": [
        {"key": "initialized", "type": "bool", "description": "系统是否已初始化", "sensitive": False},
        {"key": "setup_at", "type": "string", "description": "初始化时间", "sensitive": False},
    ],
    "storage": [
        {"key": "provider", "type": "string", "description": "存储提供商 (minio/s3/oss)", "sensitive": False, "env_key": "STORAGE_PROVIDER"},
        {"key": "endpoint", "type": "string", "description": "服务端点", "sensitive": False, "env_key": "STORAGE_ENDPOINT"},
        {"key": "access_key", "type": "string", "description": "访问密钥", "sensitive": True, "env_key": "STORAGE_ACCESS_KEY"},
        {"key": "secret_key", "type": "password", "description": "秘密密钥", "sensitive": True, "env_key": "STORAGE_SECRET_KEY"},
        {"key": "bucket", "type": "string", "description": "存储桶名称", "sensitive": False, "env_key": "STORAGE_BUCKET"},
        {"key": "region", "type": "string", "description": "区域", "sensitive": False, "env_key": "STORAGE_REGION"},
        {"key": "use_ssl", "type": "bool", "description": "是否使用 SSL", "sensitive": False, "env_key": "STORAGE_USE_SSL"},
    ],
}


class ConfigService:
    """配置管理服务

    优先级：环境变量 > 数据库 > 代码默认值
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, category: str, key: str, default: str = None) -> str | None:
        """获取配置值，优先级：环境变量 > 数据库 > 默认值"""
        env_key = None
        schema = CONFIG_SCHEMA.get(category, [])
        for field in schema:
            if field["key"] == key:
                env_key = field.get("env_key")
                break
        if not env_key:
            env_key = f"{category.upper()}_{key.upper()}"

        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val

        pydantic_val = self._get_from_pydantic_settings(category, key)
        if pydantic_val is not None:
            return pydantic_val

        result = await self.db.execute(
            select(SystemConfig).where(
                SystemConfig.category == category,
                SystemConfig.key == key,
            )
        )
        row = result.scalar_one_or_none()
        if row and row.value is not None:
            if row.is_sensitive:
                try:
                    return decrypt(row.value)
                except Exception:
                    return row.value
            return row.value

        return default

    def _get_from_pydantic_settings(self, category: str, key: str) -> str | None:
        """从 Pydantic Settings 读取配置值"""
        settings_mapping = {
            "database": {"url": "DATABASE_URL"},
            "redis": {"url": "REDIS_URL", "host": "REDIS_HOST", "port": "REDIS_PORT"},
            "milvus": {"host": "MILVUS_HOST", "port": "MILVUS_PORT", "collection": "MILVUS_COLLECTION"},
            "llm": {
                "provider": "LLM_PROVIDER", "api_key": "LLM_API_KEY", "api_base": "LLM_API_BASE",
                "model": "LLM_MODEL", "embedding_model": "LLM_EMBEDDING_MODEL", "embedding_dim": "LLM_EMBEDDING_DIM",
            },
            "storage": {
                "provider": "STORAGE_PROVIDER", "endpoint": "STORAGE_ENDPOINT",
                "access_key": "STORAGE_ACCESS_KEY", "secret_key": "STORAGE_SECRET_KEY",
                "bucket": "STORAGE_BUCKET", "region": "STORAGE_REGION", "use_ssl": "STORAGE_USE_SSL",
            },
            "keycloak": {
                "server_url": "KEYCLOAK_SERVER_URL", "realm": "KEYCLOAK_REALM",
                "client_id": "KEYCLOAK_CLIENT_ID", "client_secret": "KEYCLOAK_CLIENT_SECRET",
            },
            "security": {"cors_origins": "CORS_ORIGINS", "jwt_algorithm": "JWT_ALGORITHM"},
            "audit": {"enabled": "AUDIT_LOG_ENABLED"},
        }

        env_key = pydantic_key = None
        schema = CONFIG_SCHEMA.get(category, [])
        for field in schema:
            if field["key"] == key:
                env_key = field.get("env_key")
                break
        if not env_key:
            env_key = f"{category.upper()}_{key.upper()}"

        pydantic_key = env_key.upper()

        try:
            from app.config import get_settings
            settings = get_settings()
            if hasattr(settings, pydantic_key):
                val = getattr(settings, pydantic_key)
                if val is not None and val != "":
                    if isinstance(val, bool):
                        return str(val).lower()
                    if isinstance(val, list):
                        import json
                        return json.dumps(val)
                    return str(val)
        except Exception:
            pass

        return None

    async def get_category(self, category: str, mask_sensitive: bool = True) -> dict[str, str]:
        """获取某分类的所有配置，优先级：环境变量 > 数据库"""
        schema = CONFIG_SCHEMA.get(category, [])

        # 1. 从数据库读取
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.category == category)
        )
        db_rows = {row.key: row for row in result.scalars().all()}

        configs = {}
        for field in schema:
            key = field["key"]
            is_sensitive = field.get("sensitive", False)

            # 环境变量优先
            env_key = field.get("env_key") or f"{category.upper()}_{key.upper()}"
            env_val = os.environ.get(env_key)
            if env_val is not None:
                configs[key] = env_val
                continue

            # 数据库
            row = db_rows.get(key)
            if row and row.value is not None:
                value = row.value
                if is_sensitive and mask_sensitive:
                    from app.core.encryption import mask_sensitive as mask
                    try:
                        decrypted = decrypt(value)
                        value = mask(decrypted)
                    except Exception:
                        value = "***"
                configs[key] = value

        return configs

    async def set(self, category: str, key: str, value: str, value_type: str = "string", is_sensitive: bool = False, description: str = None):
        """设置配置值"""
        if is_sensitive and value and value != "***":
            value = encrypt(value)

        result = await self.db.execute(
            select(SystemConfig).where(
                SystemConfig.category == category,
                SystemConfig.key == key,
            )
        )
        row = result.scalar_one_or_none()

        if row:
            row.value = value
            row.value_type = value_type
            row.updated_at = datetime.utcnow()
        else:
            row = SystemConfig(
                category=category,
                key=key,
                value=value,
                value_type=value_type,
                is_sensitive=is_sensitive,
                description=description,
            )
            self.db.add(row)

        await self.db.flush()

    async def set_batch(self, category: str, configs: dict[str, str]):
        """批量设置某分类的配置"""
        schema = CONFIG_SCHEMA.get(category, [])
        schema_map = {s["key"]: s for s in schema}

        for key, value in configs.items():
            if not value or ("***" in value):
                continue  # 跳过未修改的敏感字段（脱敏值含 ***）
            field_meta = schema_map.get(key, {})
            await self.set(
                category=category,
                key=key,
                value=value,
                value_type=field_meta.get("type", "string"),
                is_sensitive=field_meta.get("sensitive", False),
                description=field_meta.get("description", ""),
            )

    async def get_all_categories(self, mask_sensitive: bool = True) -> dict[str, dict[str, str]]:
        """获取所有分类的配置"""
        result = await self.db.execute(select(SystemConfig))
        rows = result.scalars().all()

        categories: dict[str, dict[str, str]] = {}
        for row in rows:
            if row.category not in categories:
                categories[row.category] = {}
            value = row.value
            if row.is_sensitive and mask_sensitive and value:
                from app.core.encryption import mask_sensitive as mask
                try:
                    decrypted = decrypt(value)
                    value = mask(decrypted)
                except Exception:
                    value = "***"
            categories[row.category][row.key] = value
        return categories

    async def is_system_initialized(self) -> bool:
        """检查系统是否已完成初始化"""
        val = await self.get("system", "initialized", "false")
        return val.lower() in ("true", "1", "yes")

    async def mark_initialized(self):
        """标记系统已初始化"""
        await self.set("system", "initialized", "true", "bool")
        await self.set("system", "setup_at", datetime.utcnow().isoformat(), "string")
        await self.db.commit()

    @staticmethod
    def get_config_schema() -> dict[str, list[dict]]:
        """获取配置字段定义（用于前端渲染表单）"""
        return CONFIG_SCHEMA
