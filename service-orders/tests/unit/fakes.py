import copy
import uuid

from transactional_outbox import OutboxRepository, PublishedMessage

from adapters.order_repository import OrderAlreadyExistsError, OrderNotFoundError, OrderRepository
from orders.events import Event
from orders.order import Order
from service_layer.unit_of_work import UnitOfWork


class FakeOrderRepository(OrderRepository):
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    async def create(self, order: Order) -> None:
        if await self.get(order.id):
            raise OrderAlreadyExistsError(order.id)
        self._orders.append(copy.deepcopy(order))

    async def get(self, order_id: uuid.UUID) -> Order | None:
        return next((copy.deepcopy(v) for v in self._orders if v.id == order_id), None)

    async def update(self, order: Order) -> None:
        indices = [i for i, x in enumerate(self._orders) if x.id == order.id]
        if len(indices) == 0:
            raise OrderNotFoundError(order.id)
        assert len(indices) == 1
        self._orders[indices[0]] = copy.deepcopy(order)


class FakeOutboxRepository(OutboxRepository):
    def __init__(self, events: list[Event]) -> None:
        self.events = events

    async def publish(self, messages: list[Event]) -> None:
        self.events.extend(copy.deepcopy(messages))

    async def get(self, message_id: uuid.UUID) -> PublishedMessage | None:
        raise NotImplementedError

    async def mark_dispatched(self, message_id: uuid.UUID) -> None:
        raise NotImplementedError

    async def get_not_dispatched_messages(self) -> list[PublishedMessage]:
        raise NotImplementedError

    def clear(self) -> None:
        self.events.clear()


class FakeUnitOfWork(UnitOfWork):
    orders: FakeOrderRepository
    events: FakeOutboxRepository

    def __init__(self) -> None:
        self.orders = FakeOrderRepository([])
        self.events = FakeOutboxRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
