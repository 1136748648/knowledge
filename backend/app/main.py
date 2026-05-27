import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging import setup_logging
from app.core.trace import setup_trace_logging
from app.middleware import TraceMiddleware, SignatureMiddleware
from app.api import auth, qa, admin, system, heatmap, storage
from app.dal import get_adapter, LocalUserRepository
from app.core.exception_handler import custom_exception_handler

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
            if "admin" in user.roles and user.username != BUILTIN_ADMIN_USER:
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
        register_vector_agent,
        register_mindmap_agent,
    )
    
    register_security_agent()
    register_orchestrator_agent()
    register_db_agent()
    register_vector_agent()
    register_mindmap_agent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global SYSTEM_INITIALIZED

    adapter = get_adapter()
    await adapter.connect()
    logger.info("Database adapter connected")

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
app.add_middleware(SignatureMiddleware)

app.add_exception_handler(Exception, custom_exception_handler)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统配置"])
app.include_router(heatmap.router, tags=["热力图"])
app.include_router(storage.router, prefix="/api/storage", tags=["存储"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
