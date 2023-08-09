import abc
from typing import Any

from adapters.event_repository import AbstractEventRepository
from adapters.order_repository import AbstractOrderRepository


class AbstractUnitOfWork(abc.ABC):
    orders: AbstractOrderRepository
    events: AbstractEventRepository

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.rollback()

    @abc.abstractmethod
    async def commit(self) -> None:
        pass

    @abc.abstractmethod
    async def rollback(self) -> None:
        pass
