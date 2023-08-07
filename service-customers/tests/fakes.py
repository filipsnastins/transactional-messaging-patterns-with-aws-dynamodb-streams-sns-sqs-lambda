import copy
import uuid

from tomodachi_outbox.message import Message

from adapters.customer_repository import AbstractCustomerRepository
from adapters.event_repository import AbstractEventRepository
from customers.customer import Customer, CustomerNotFoundError
from customers.events import Event
from service_layer.unit_of_work import AbstractUnitOfWork


class FakeCustomerRepository(AbstractCustomerRepository):
    def __init__(self, customers: list[Customer]) -> None:
        super().__init__()
        self._customers = customers

    async def create(self, customer: Customer) -> None:
        self._customers.append(copy.deepcopy(customer))

    async def update(self, customer: Customer) -> None:
        indices = [i for i, x in enumerate(self._customers) if x.id == customer.id]
        if len(indices) == 0:
            raise CustomerNotFoundError(customer.id)
        assert len(indices) == 1
        self._customers[indices[0]] = copy.deepcopy(customer)

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        return next((copy.deepcopy(v) for v in self._customers if v.id == customer_id), None)


class FakeEventRepository(AbstractEventRepository):
    def __init__(self, events: list[Event]) -> None:
        self.events = events

    async def publish(self, events: list[Event]) -> None:
        self.events.extend(copy.deepcopy(events))

    async def get(self, event_id: uuid.UUID) -> Message | None:
        pass


class FakeUnitOfWork(AbstractUnitOfWork):
    customers: FakeCustomerRepository
    events: FakeEventRepository

    def __init__(self) -> None:
        self.customers = FakeCustomerRepository([])
        self.events = FakeEventRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
