"""
旧的数据库会话管理模块 - 已弃用

请使用 `app.dal` 模块代替：
- `from app.dal import get_db` 代替 `from app.db.session import get_db`
- `from app.dal import Base` 代替 `from app.db.session import Base`

此文件仅保留用于支持 Alembic 迁移
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

# 为了兼容 Alembic 迁移，保留这些引用
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_timeout=5,
    connect_args={"timeout": 3, "command_timeout": 5},
)

Base = declarative_base()
