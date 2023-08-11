import copy
import uuid

from tomodachi_outbox.message import Message

from adapters.event_repository import AbstractEventRepository
from adapters.order_repository import AbstractOrderRepository, OrderNotFoundError
from orders.events import Event
from orders.order import Order
from service_layer.unit_of_work import AbstractUnitOfWork


class FakeOrderRepository(AbstractOrderRepository):
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    async def create(self, order: Order) -> None:
        self._orders.append(copy.deepcopy(order))

    async def get(self, order_id: uuid.UUID) -> Order | None:
        return next((copy.deepcopy(v) for v in self._orders if v.id == order_id), None)

    async def update(self, order: Order) -> None:
        indices = [i for i, x in enumerate(self._orders) if x.id == order.id]
        if len(indices) == 0:
            raise OrderNotFoundError(order.id)
        assert len(indices) == 1
        self._orders[indices[0]] = copy.deepcopy(order)


class FakeEventRepository(AbstractEventRepository):
    def __init__(self, events: list[Event]) -> None:
        self.events = events

    async def publish(self, events: list[Event]) -> None:
        self.events.extend(copy.deepcopy(events))

    async def get(self, event_id: uuid.UUID) -> Message | None:
        pass


class FakeUnitOfWork(AbstractUnitOfWork):
    orders: FakeOrderRepository
    events: FakeEventRepository

    def __init__(self) -> None:
        self.orders = FakeOrderRepository([])
        self.events = FakeEventRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
