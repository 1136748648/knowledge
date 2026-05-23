from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class DatabaseAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def get_session(self) -> AsyncSession:
        pass

    @abstractmethod
    async def execute(self, query: str, params: dict = None) -> Any:
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: dict = None) -> Optional[dict]:
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: dict = None) -> List[dict]:
        pass


class Transactional:
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter
        self.session = None

    async def __aenter__(self):
        self.session = await self.adapter.get_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


class Repository(ABC, Generic[ModelType]):
    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_all(self) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(self, entity: ModelType) -> ModelType:
        pass

    @abstractmethod
    async def update(self, entity: ModelType) -> ModelType:
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        pass

    async def get_by_ids(self, ids: List[Any]) -> List[ModelType]:
        results = []
        for id_ in ids:
            entity = await self.get_by_id(id_)
            if entity:
                results.append(entity)
        return results
