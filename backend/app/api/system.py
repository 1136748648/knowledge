import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dal import get_db, get_adapter, Base
from app.core.security import get_current_active_user
from app.models.schemas import UserContext
from app.services.config_service import ConfigService
from app.services.llm_providers import ProviderRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

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

PROVIDER_GUIDES = {
    "openai": {
        "website": "https://platform.openai.com",
        "install": "pip install openai",
        "note": "需要在 platform.openai.com 获取 API Key",
    },
    "zhipu": {
        "website": "https://open.bigmodel.cn",
        "install": "pip install openai  (兼容 OpenAI 接口)",
        "note": "智谱开放平台注册后获取 API Key",
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


class SystemStatusResponse(BaseModel):
    initialized: bool
    version: str


class InitRequest(BaseModel):
    database: dict[str, str] = {}
    redis: dict[str, str] = {}
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


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    from app.main import SYSTEM_INITIALIZED
    return SystemStatusResponse(initialized=SYSTEM_INITIALIZED, version="0.1.0")


@router.get("/config/schema")
async def get_config_schema():
    return ConfigService.get_config_schema()


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


@router.get("/llm/providers")
async def list_llm_providers():
    providers = ProviderRegistry.list_providers()
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
    import httpx

    api_key = data.api_key
    api_base = data.api_base.rstrip("/")

    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")

    models_url = f"{api_base}/models"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                models_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            result = resp.json()

        raw_models = result.get("data", [])
        models = []
        for m in raw_models:
            model_id = m.get("id", "")
            model_type = "embedding" if "embed" in model_id.lower() else "chat"
            models.append({
                "id": model_id,
                "name": model_id,
                "type": model_type,
                "owned_by": m.get("owned_by", ""),
            })

        models.sort(key=lambda x: (0 if x["type"] == "chat" else 1, x["id"]))

        return {"models": models, "total": len(models)}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"API error: {e.response.text[:200]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


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


@router.post("/test/database", response_model=TestResult)
async def test_database_connection(data: TestConnectionRequest):
    from sqlalchemy.ext.asyncio import create_async_engine
    url = data.configs.get("url") or _assemble_db_url(data.configs)
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
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
    port = data.configs.get("port", "9091")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"http://{host}:{port}/healthz")
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


def _write_env_file(categories: dict[str, dict[str, str]]):
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    lines = ["# Knowledge Platform Configuration", "# Auto-generated by setup wizard", ""]

    db = categories.get("database", {})
    if db.get("host"):
        lines.append("# DATABASE")
        lines.append(f"DATABASE_URL={_assemble_db_url(db)}")
        lines.append("")

    redis_cfg = categories.get("redis", {})
    if redis_cfg.get("host"):
        lines.append("# REDIS")
        lines.append(f"REDIS_URL={_assemble_redis_url(redis_cfg)}")
        lines.append("")

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
    adapter = get_adapter()
    await adapter.connect()
    engine = adapter.engine
    
    from app.models import (
        WikiPage, WikiPageVersion, Employee, Conversation,
        KnowledgeNav, NavContentLink, AuditLog, CasbinRule,
        SystemConfig, LocalUser,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def _seed_admin(password: str):
    from app.models.local_user import LocalUser
    from app.core.security import hash_password
    from app.dal import LocalUserRepository

    adapter = get_adapter()
    user_repo = LocalUserRepository(adapter)
    existing = await user_repo.get_by_username("admin")

    if existing:
        existing.password_hash = hash_password(password)
        existing.roles = ["admin"]
        existing.is_active = True
        await user_repo.update(existing)
    else:
        admin = LocalUser(
            username="admin",
            password_hash=hash_password(password),
            email="admin@local",
            roles=["admin"],
            is_active=True,
        )
        await user_repo.create(admin)

    logger.info("Admin user seeded")


@router.post("/init")
async def initialize_system(data: InitRequest):
    import app.main as main_module

    if main_module.SYSTEM_INITIALIZED:
        raise HTTPException(status_code=400, detail="System is already initialized")

    if not data.admin_password or len(data.admin_password) < 6:
        raise HTTPException(status_code=400, detail="管理员密码至少 6 位")

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

    try:
        await _create_tables()
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据库表失败: {e}")

    try:
        await _seed_admin(data.admin_password)
    except Exception as e:
        logger.error(f"Failed to seed admin: {e}")
        raise HTTPException(status_code=500, detail=f"创建管理员账号失败: {e}")

    main_module.SYSTEM_INITIALIZED = True
    logger.info("System initialized successfully")

    from app.dal import get_adapter
    adapter = get_adapter()
    await adapter.disconnect()

    return {
        "message": "System initialized successfully",
        "restart": True,
        "note": "系统初始化完成，请重启服务后登录",
    }
