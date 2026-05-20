import logging
import os
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.schemas import UserContext
from app.services.config_service import ConfigService
from app.services.llm_providers import ProviderRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

# ---- .env 字段映射（简单字段直接映射，复杂字段在 _write_env_file 中特殊处理） ----
ENV_MAP = {
    "milvus": {"host": "MILVUS_HOST", "port": "MILVUS_PORT", "collection": "MILVUS_COLLECTION"},
    "keycloak": {
        "server_url": "KEYCLOAK_SERVER_URL",
        "realm": "KEYCLOAK_REALM",
        "client_id": "KEYCLOAK_CLIENT_ID",
        "client_secret": "KEYCLOAK_CLIENT_SECRET",
    },
    "llm": {
        "provider": "LLM_PROVIDER",
        "api_key": "LLM_API_KEY",
        "api_base": "LLM_API_BASE",
        "model": "LLM_MODEL",
        "embedding_model": "LLM_EMBEDDING_MODEL",
        "embedding_dim": "LLM_EMBEDDING_DIM",
    },
    "security": {"cors_origins": "CORS_ORIGINS", "jwt_algorithm": "JWT_ALGORITHM"},
}

# 提供商官方链接和安装指南
PROVIDER_GUIDES = {
    "openai": {
        "website": "https://platform.openai.com",
        "install": "pip install openai",
        "note": "需要在 platform.openai.com 获取 API Key",
    },
    "anthropic": {
        "website": "https://console.anthropic.com",
        "install": "pip install anthropic",
        "note": "需要在 console.anthropic.com 获取 API Key",
    },
    "zhipu": {
        "website": "https://open.bigmodel.cn",
        "install": "pip install openai  (兼容 OpenAI 接口)",
        "note": "智谱开放平台注册后获取 API Key",
    },
    "qwen": {
        "website": "https://dashscope.console.aliyun.com",
        "install": "pip install openai  (兼容 OpenAI 接口)",
        "note": "阿里云 DashScope 开通后获取 API Key",
    },
    "wenxin": {
        "website": "https://console.bce.baidu.com/qianfan",
        "install": "pip install requests",
        "note": "百度智能云千帆平台创建应用获取 API Key",
    },
    "moonshot": {
        "website": "https://platform.moonshot.cn",
        "install": "pip install openai  (兼容 OpenAI 接口)",
        "note": "月之暗面开放平台注册后获取 API Key",
    },
    "deepseek": {
        "website": "https://platform.deepseek.com",
        "install": "pip install openai  (兼容 OpenAI 接口)",
        "note": "DeepSeek 开放平台注册后获取 API Key",
    },
    "ollama": {
        "website": "https://ollama.com",
        "install": "curl -fsSL https://ollama.com/install.sh | sh",
        "note": "本地部署，无需 API Key，安装 Ollama 后 ollama pull 模型",
    },
}


# ---- Schemas ----

class SystemStatusResponse(BaseModel):
    initialized: bool
    version: str


class InitRequest(BaseModel):
    """系统初始化请求"""
    database: dict[str, str] = {}   # host, port, user, password, name
    redis: dict[str, str] = {}      # host, port, password, db (可选)
    milvus: dict[str, str] = {}
    keycloak: dict[str, str] = {}
    llm: dict[str, str] = {}
    security: dict[str, str] = {}
    audit: dict[str, str] = {}
    admin_password: str = ""


class ConfigUpdateRequest(BaseModel):
    configs: dict[str, str]


class TestConnectionRequest(BaseModel):
    configs: dict[str, str] = {}


class TestResult(BaseModel):
    success: bool
    message: str
    details: dict | None = None


class FetchModelsRequest(BaseModel):
    provider: str
    api_key: str
    api_base: str = ""


# ---- 系统状态 ----

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: AsyncSession = Depends(get_db)):
    from app.main import SYSTEM_INITIALIZED
    return SystemStatusResponse(initialized=SYSTEM_INITIALIZED, version="0.1.0")


# ---- 配置 Schema ----

@router.get("/config/schema")
async def get_config_schema():
    return ConfigService.get_config_schema()


# ---- 配置 CRUD ----

@router.get("/config")
async def get_all_configs(
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    service = ConfigService(db)
    return await service.get_all_categories(mask_sensitive=True)


@router.get("/config/{category}")
async def get_category_config(
    category: str,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    service = ConfigService(db)
    return await service.get_category(category, mask_sensitive=True)


@router.put("/config/{category}")
async def update_category_config(
    category: str,
    data: ConfigUpdateRequest,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    service = ConfigService(db)
    await service.set_batch(category, data.configs)
    await db.commit()
    return {"message": f"Configuration '{category}' updated successfully"}


# ---- LLM 提供商 ----

@router.get("/llm/providers")
async def list_llm_providers():
    providers = ProviderRegistry.list_providers()
    # 附加安装指南
    for p in providers:
        guide = PROVIDER_GUIDES.get(p["name"], {})
        p["website"] = guide.get("website", "")
        p["install_guide"] = guide.get("install", "")
        p["note"] = guide.get("note", "")
    return providers


@router.get("/llm/providers/{provider_name}/models")
async def list_provider_models(provider_name: str):
    try:
        return ProviderRegistry.list_provider_models(provider_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/llm/providers/{provider_name}/default-config")
async def get_provider_default_config(provider_name: str):
    try:
        return ProviderRegistry.get_provider_default_config(provider_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/llm/fetch-models")
async def fetch_models_from_api(data: FetchModelsRequest):
    """通过 API Key 和 URL 动态获取模型列表"""
    import httpx

    api_key = data.api_key
    api_base = data.api_base.rstrip("/")

    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")

    # 大部分提供商兼容 OpenAI /v1/models 接口
    models_url = f"{api_base}/models"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                models_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            result = resp.json()

        # 解析模型列表
        raw_models = result.get("data", [])
        models = []
        for m in raw_models:
            model_id = m.get("id", "")
            # 简单分类：包含 embed 的归为 embedding，其余为 chat
            model_type = "embedding" if "embed" in model_id.lower() else "chat"
            models.append({
                "id": model_id,
                "name": model_id,
                "type": model_type,
                "owned_by": m.get("owned_by", ""),
            })

        # 按类型排序：chat 在前
        models.sort(key=lambda x: (0 if x["type"] == "chat" else 1, x["id"]))

        return {"models": models, "total": len(models)}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"API error: {e.response.text[:200]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


# ---- 辅助：拼接连接串 ----

def _assemble_db_url(db: dict[str, str]) -> str:
    host = db.get("host", "localhost")
    port = db.get("port", "5432")
    user = db.get("user", "knowledge")
    password = db.get("password", "knowledge123")
    name = db.get("name", "knowledge")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def _assemble_redis_url(redis: dict[str, str]) -> str:
    host = redis.get("host", "localhost")
    port = redis.get("port", "6379")
    password = redis.get("password", "")
    db_num = redis.get("db", "0")
    if password:
        return f"redis://:{password}@{host}:{port}/{db_num}"
    return f"redis://{host}:{port}/{db_num}"


# ---- 连接测试 ----

@router.post("/test/database", response_model=TestResult)
async def test_database_connection(data: TestConnectionRequest):
    import sqlalchemy
    url = data.configs.get("url") or _assemble_db_url(data.configs)
    try:
        engine = sqlalchemy.create_engine(url.replace("+asyncpg", "+psycopg2"))
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return TestResult(success=True, message="Database connection successful")
    except Exception as e:
        return TestResult(success=False, message=f"Connection failed: {str(e)}")


@router.post("/test/redis", response_model=TestResult)
async def test_redis_connection(data: TestConnectionRequest):
    import redis
    url = data.configs.get("url") or _assemble_redis_url(data.configs)
    try:
        r = redis.from_url(url)
        r.ping()
        return TestResult(success=True, message="Redis connection successful")
    except Exception as e:
        return TestResult(success=False, message=f"Connection failed: {str(e)}")


@router.post("/test/milvus", response_model=TestResult)
async def test_milvus_connection(data: TestConnectionRequest):
    import httpx
    host = data.configs.get("host", "localhost")
    rest_port = 19531
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"http://{host}:{rest_port}/v1/vector/collections")
            resp.raise_for_status()
        return TestResult(success=True, message="Milvus connection successful")
    except Exception as e:
        return TestResult(success=False, message=f"Connection failed: {str(e)}")


@router.post("/test/llm", response_model=TestResult)
async def test_llm_connection(data: TestConnectionRequest):
    provider_name = data.configs.get("provider", "")
    if not provider_name:
        return TestResult(success=False, message="Provider is required")
    try:
        from app.services.llm_service import LLMService
        service = LLMService(provider_name=provider_name, config=data.configs)
        result = await service.chat(
            [{"role": "user", "content": "Hello, respond with 'OK'."}],
            max_tokens=10,
        )
        return TestResult(
            success=True,
            message=f"LLM connection successful ({service.display_name})",
            details={"response": result[:100]},
        )
    except Exception as e:
        return TestResult(success=False, message=f"LLM test failed: {str(e)}")


# ---- 系统初始化 ----

def _write_env_file(categories: dict[str, dict[str, str]]):
    """将配置写入 .env 文件"""
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    lines = ["# Knowledge Platform Configuration", "# Auto-generated by setup wizard", ""]

    # Database（拼接连接串）
    db = categories.get("database", {})
    if db.get("host"):
        lines.append("# DATABASE")
        lines.append(f"DATABASE_URL={_assemble_db_url(db)}")
        lines.append("")

    # Redis（可选，拼接连接串）
    redis_cfg = categories.get("redis", {})
    if redis_cfg.get("host"):
        lines.append("# REDIS")
        lines.append(f"REDIS_URL={_assemble_redis_url(redis_cfg)}")
        lines.append("")

    # 其他分类（直接映射）
    for category, mapping in ENV_MAP.items():
        configs = categories.get(category, {})
        if configs:
            lines.append(f"# {category.upper()}")
            for field_key, env_key in mapping.items():
                value = configs.get(field_key, "")
                if value:
                    lines.append(f"{env_key}={value}")
            lines.append("")

    env_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Config written to {env_path}")


async def _create_tables():
    """创建所有数据库表"""
    from app.db.session import engine, Base
    # 导入所有模型以注册到 Base.metadata
    from app.models import (
        WikiPage, WikiPageVersion, Employee, Conversation,
        KnowledgeNav, NavContentLink, AuditLog, CasbinRule,
        SystemConfig, LocalUser,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def _seed_admin(password: str, db: AsyncSession):
    """写入管理员账号（最高权限）"""
    from app.models.local_user import LocalUser
    from app.core.security import hash_password

    result = await db.execute(
        select(LocalUser).where(LocalUser.username == "admin")
    )
    existing = result.scalar_one_or_none()

    if existing:
        # 更新密码
        existing.password_hash = hash_password(password)
        existing.roles = ["admin"]
        existing.is_active = True
    else:
        admin = LocalUser(
            username="admin",
            password_hash=hash_password(password),
            email="admin@local",
            roles=["admin"],
            is_active=True,
        )
        db.add(admin)

    await db.commit()
    logger.info("Admin user seeded")


def _restart_backend():
    """延迟重启后端服务"""
    import time
    time.sleep(1)
    logger.info("Restarting backend...")
    os._exit(0)


@router.post("/init")
async def initialize_system(data: InitRequest, db: AsyncSession = Depends(get_db)):
    """系统初始化：写配置 → 建表 → 建管理员 → 重启"""
    import app.main as main_module

    if main_module.SYSTEM_INITIALIZED:
        raise HTTPException(status_code=400, detail="System is already initialized")

    if not data.admin_password or len(data.admin_password) < 6:
        raise HTTPException(status_code=400, detail="管理员密码至少 6 位")

    # Step 1: 写入 .env 文件
    categories = {
        "database": data.database,
        "redis": data.redis,
        "milvus": data.milvus,
        "keycloak": data.keycloak,
        "llm": data.llm,
        "security": data.security or {"cors_origins": '["http://localhost:5173"]', "jwt_algorithm": "RS256"},
        "audit": data.audit or {"enabled": "true"},
    }
    try:
        _write_env_file(categories)
    except Exception as e:
        logger.error(f"Failed to write .env: {e}")
        raise HTTPException(status_code=500, detail=f"写入配置文件失败: {e}")

    # Step 2: 创建数据库表
    try:
        await _create_tables()
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据库表失败: {e}")

    # Step 3: 写入管理员账号
    try:
        await _seed_admin(data.admin_password, db)
    except Exception as e:
        logger.error(f"Failed to seed admin: {e}")
        raise HTTPException(status_code=500, detail=f"创建管理员账号失败: {e}")

    # 标记已初始化
    main_module.SYSTEM_INITIALIZED = True
    logger.info("System initialized successfully")

    # Step 4: 延迟重启（响应发送后再执行）
    threading.Thread(target=_restart_backend, daemon=True).start()

    return {
        "message": "System initialized successfully",
        "restart": True,
        "note": "后端将在 1 秒后自动重启，请等待几秒后刷新页面",
    }
