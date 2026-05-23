from typing import Any, Dict, Type

from app.dal.base import DatabaseAdapter, Repository
from app.dal.postgres import PostgreSQLAdapter

_adapters: Dict[str, DatabaseAdapter] = {}
_repositories: Dict[str, Type[Repository]] = {}


def get_adapter(db_type: str = "postgresql") -> DatabaseAdapter:
    if db_type not in _adapters:
        if db_type == "postgresql":
            _adapters[db_type] = PostgreSQLAdapter()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    return _adapters[db_type]


def register_repository(name: str, repo_class: Type[Repository]) -> None:
    _repositories[name] = repo_class


def get_repository(name: str, adapter: DatabaseAdapter = None) -> Repository:
    if name not in _repositories:
        raise ValueError(f"Repository not registered: {name}")
    adapter = adapter or get_adapter()
    return _repositories[name](adapter)


def initialize_adapters() -> None:
    for adapter in _adapters.values():
        import asyncio
        asyncio.create_task(adapter.connect())
