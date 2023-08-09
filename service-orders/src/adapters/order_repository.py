import uuid
from typing import Protocol

from orders.order import Order


class AbstractOrderRepository(Protocol):
    async def create(self, order: Order) -> None:
        ...

    async def get(self, order_id: uuid.UUID) -> Order | None:
        ...
