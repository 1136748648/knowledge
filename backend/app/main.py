import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging import setup_logging
from app.core.trace import setup_trace_logging
from app.middleware import TraceMiddleware
from app.api import auth, wiki, qa, knowledge, admin, system, heatmap, storage, tags, chunking_rules
from app.dal import get_adapter, LocalUserRepository

settings = get_settings()
setup_logging(log_dir="logs", level="DEBUG" if settings.DEBUG else "INFO")
setup_trace_logging(log_dir="logs", level="DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger(__name__)

# 从配置中读取内置管理员信息
BUILTIN_ADMIN_USER = settings.BUILTIN_ADMIN_USER
BUILTIN_ADMIN_PASS = settings.BUILTIN_ADMIN_PASS

SYSTEM_INITIALIZED = False


async def check_system_initialized():
    global SYSTEM_INITIALIZED
    try:
        adapter = get_adapter()
        user_repo = LocalUserRepository(adapter)
        
        users = await user_repo.get_all()
        for user in users:
            if "admin" in user.roles:
                SYSTEM_INITIALIZED = True
                logger.info("System is initialized (admin user found)")
                return
        
        SYSTEM_INITIALIZED = False
        logger.info("System not initialized (no admin user)")
    except Exception as e:
        SYSTEM_INITIALIZED = False
        logger.info(f"Database not available, system not initialized: {e}")


async def init_agents():
    from app.agents import (
        register_security_agent,
        register_orchestrator_agent,
        register_db_agent,
        register_wiki_agent,
        register_vector_agent,
        register_mindmap_agent,
    )
    
    register_security_agent()
    register_orchestrator_agent()
    register_db_agent()
    register_wiki_agent()
    register_vector_agent()
    register_mindmap_agent()


async def ensure_default_admin():
    try:
        adapter = get_adapter()
        user_repo = LocalUserRepository(adapter)
        
        existing = await user_repo.get_by_username(BUILTIN_ADMIN_USER)
        if existing:
            return

        from app.models.local_user import LocalUser
        from app.core.security import hash_password

        admin_user = LocalUser(
            username=BUILTIN_ADMIN_USER,
            password_hash=hash_password(BUILTIN_ADMIN_PASS),
            email="admin@local",
            roles=["admin"],
            is_active=True,
        )
        await user_repo.create(admin_user)
        logger.info("Default admin user created")
    except Exception as e:
        logger.warning(f"Database not available, skipping admin creation: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global SYSTEM_INITIALIZED

    adapter = get_adapter()
    await adapter.connect()
    logger.info("Database adapter connected")

    await check_system_initialized()

    if not SYSTEM_INITIALIZED:
        await ensure_default_admin()
        await check_system_initialized()

    try:
        from app.core.casbin_policy import init_policies
        await init_policies()
        logger.info("Casbin policies initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Casbin policies: {e}")

    try:
        from app.skills import register_all_skills
        register_all_skills()
        logger.info("Skills registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register skills: {e}")

    try:
        await init_agents()
        logger.info("Agents registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register agents: {e}")

    try:
        from app.tasks.heatmap_aggregator import start_scheduler
        start_scheduler()
        logger.info("Heatmap scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start heatmap scheduler: {e}")

    print("\n" + "=" * 50)
    print("  Knowledge Platform Backend Started")
    print("=" * 50)
    print(f"  API Docs:  http://localhost:8000/docs")
    print(f"  Health:    http://localhost:8000/health")
    print()
    if not SYSTEM_INITIALIZED:
        print("  [First Time Setup]")
        print(f"  Built-in Login: {BUILTIN_ADMIN_USER} / {BUILTIN_ADMIN_PASS}")
        print("  Login -> complete setup wizard -> system ready")
    else:
        print("  System is initialized and ready")
    print("=" * 50 + "\n")

    yield

    try:
        from app.tasks.heatmap_aggregator import stop_scheduler
        stop_scheduler()
        logger.info("Heatmap scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop heatmap scheduler: {e}")

    from app.services.cache_service import close_cache
    await close_cache()

    from app.core.redis import close_redis
    await close_redis()

    await adapter.disconnect()
    logger.info("Database adapter disconnected")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TraceMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(wiki.router, prefix="/api/wiki", tags=["Wiki"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识导航"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统配置"])
app.include_router(heatmap.router, tags=["热力图"])
app.include_router(storage.router, prefix="/api/storage", tags=["存储"])
app.include_router(tags.router, prefix="/api/tags", tags=["标签"])
app.include_router(chunking_rules.router, prefix="/api/chunking-rules", tags=["切片规则"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
