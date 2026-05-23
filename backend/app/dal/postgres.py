from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.dal.base import DatabaseAdapter

settings = get_settings()

_base = None


def get_base() -> DeclarativeBase:
    """Get the SQLAlchemy declarative base class"""
    global _base
    if _base is None:
        class Base(DeclarativeBase):
            pass
        _base = Base
    return _base


class PostgreSQLAdapter(DatabaseAdapter):
    _engine = None
    _session_factory = None

    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.DATABASE_URL

    async def connect(self) -> None:
        if PostgreSQLAdapter._engine is None:
            PostgreSQLAdapter._engine = create_async_engine(
                self.db_url,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=5,
                pool_pre_ping=True,
                pool_timeout=5,
                connect_args={"timeout": 3, "command_timeout": 5},
            )
            PostgreSQLAdapter._session_factory = async_sessionmaker(
                PostgreSQLAdapter._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    async def disconnect(self) -> None:
        if PostgreSQLAdapter._engine is not None:
            await PostgreSQLAdapter._engine.dispose()
            PostgreSQLAdapter._engine = None
            PostgreSQLAdapter._session_factory = None

    async def get_session(self) -> AsyncSession:
        if PostgreSQLAdapter._session_factory is None:
            await self.connect()
        return PostgreSQLAdapter._session_factory()

    @property
    def engine(self):
        return PostgreSQLAdapter._engine

    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result

    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            row = result.first()
            if row:
                return row._asdict()
            return None

    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return [row._asdict() for row in result.all()]

    async def insert(self, table_name: str, data: Dict[str, Any]) -> Any:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        result = await self.fetch_one(query, data)
        return result

    async def update(self, table_name: str, data: Dict[str, Any], condition: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        updates = ", ".join(f"{key} = :{key}" for key in data.keys())
        query = f"UPDATE {table_name} SET {updates} WHERE {condition} RETURNING *"
        all_params = {**data, **(params or {})}
        result = await self.fetch_one(query, all_params)
        return result

    async def delete(self, table_name: str, condition: str, params: Dict[str, Any] = None) -> bool:
        query = f"DELETE FROM {table_name} WHERE {condition}"
        result = await self.execute(query, params or {})
        return result.rowcount > 0

    async def exists(self, table_name: str, condition: str, params: Dict[str, Any] = None) -> bool:
        query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {condition})"
        result = await self.fetch_one(query, params or {})
        return result.get("exists", False) if result else False
