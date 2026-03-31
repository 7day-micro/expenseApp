from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")  # Model
S = TypeVar("S")  # Schema


class BaseService(ABC, Generic[T, S]):
    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def create(self, data: S, user_id: Any) -> T:
        pass

    @abstractmethod
    async def get_by_id(self, id: Any, user_id: Any) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, user_id: Any) -> List[T]:
        pass
