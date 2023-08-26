import copy
import uuid

from transactional_messaging.fakes import FakeInboxRepository, FakeOutboxRepository

from adapters.customer_repository import CustomerNotFoundError, CustomerRepository
from customers.customer import Customer
from service_layer.unit_of_work import UnitOfWork


class FakeCustomerRepository(CustomerRepository):
    def __init__(self, customers: list[Customer]) -> None:
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


class FakeUnitOfWork(UnitOfWork):
    customers: FakeCustomerRepository
    inbox: FakeInboxRepository
    events: FakeOutboxRepository

    def __init__(self, message_id: uuid.UUID | None = None) -> None:
        super().__init__(message_id=message_id)
        self.customers = FakeCustomerRepository([])
        self.inbox = FakeInboxRepository([])
        self.events = FakeOutboxRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass
