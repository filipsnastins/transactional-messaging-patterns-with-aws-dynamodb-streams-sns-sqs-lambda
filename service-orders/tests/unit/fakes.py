import copy
import uuid

from transactional_outbox.fakes import FakeOutboxRepository

from adapters.order_repository import OrderAlreadyExistsError, OrderNotFoundError, OrderRepository
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


class FakeUnitOfWork(UnitOfWork):
    orders: FakeOrderRepository
    events: FakeOutboxRepository

    def __init__(self, message_id: uuid.UUID | None = None) -> None:
        super().__init__(message_id=message_id)
        self.orders = FakeOrderRepository([])
        self.events = FakeOutboxRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
