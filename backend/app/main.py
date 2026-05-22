import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.config import get_settings
from app.core.logging import setup_logging
from app.api import auth, wiki, qa, knowledge, admin, system

settings = get_settings()
setup_logging(log_dir="logs", level="DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger(__name__)

# ---- 内置管理员（首次启动时使用，无需数据库） ----
BUILTIN_ADMIN_USER = "builtin-admin"
BUILTIN_ADMIN_PASS = "admin123"

# 系统是否已完成初始化（有真实管理员账号）
SYSTEM_INITIALIZED = False


async def check_system_initialized():
    """检查数据库中是否存在管理员账号"""
    global SYSTEM_INITIALIZED
    try:
        from app.db.session import async_session
        from app.models.local_user import LocalUser

        async with async_session() as db:
            result = await db.execute(
                select(LocalUser).where(LocalUser.roles.any("admin"))
            )
            if result.scalar_one_or_none():
                SYSTEM_INITIALIZED = True
                logger.info("System is initialized (admin user found)")
            else:
                SYSTEM_INITIALIZED = False
                logger.info("System not initialized (no admin user)")
    except Exception as e:
        SYSTEM_INITIALIZED = False
        logger.info(f"Database not available, system not initialized: {e}")


async def ensure_default_admin():
    """数据库可用时，确保默认管理员存在"""
    try:
        from app.db.session import async_session
        from app.models.local_user import LocalUser
        from app.core.security import hash_password

        async with async_session() as db:
            result = await db.execute(
                select(LocalUser).where(LocalUser.username == BUILTIN_ADMIN_USER)
            )
            if result.scalar_one_or_none():
                return

            admin_user = LocalUser(
                username=BUILTIN_ADMIN_USER,
                password_hash=hash_password(BUILTIN_ADMIN_PASS),
                email="admin@local",
                roles=["admin"],
                is_active=True,
            )
            db.add(admin_user)
            await db.commit()
            logger.info("Default admin user created")
    except Exception as e:
        logger.warning(f"Database not available, skipping admin creation: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global SYSTEM_INITIALIZED

    # 检查系统初始化状态
    await check_system_initialized()

    if not SYSTEM_INITIALIZED:
        # 数据库可用但没有管理员 → 创建默认管理员
        await ensure_default_admin()
        await check_system_initialized()

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

    # Shutdown
    from app.services.cache_service import close_cache
    await close_cache()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(wiki.router, prefix="/api/wiki", tags=["Wiki"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识导航"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统配置"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
