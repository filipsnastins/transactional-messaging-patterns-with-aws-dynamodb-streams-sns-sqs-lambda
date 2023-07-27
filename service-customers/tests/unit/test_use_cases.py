import uuid
from decimal import Decimal

import pytest
from adapters.repository import AbstractRepository, CustomerNotFoundError
from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from customers.events import CustomerCreatedEvent
from service_layer.unit_of_work import AbstractUnitOfWork
from service_layer.use_cases import create_customer


class FakeRepository(AbstractRepository):
    def __init__(self, customers: list[Customer]):
        super().__init__()
        self._customers = customers

    async def create(self, customer: Customer) -> None:
        self._customers.append(customer)

    async def get(self, customer_id: uuid.UUID) -> Customer:
        customer = next((p for p in self._customers if p.id == customer_id), None)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        return customer


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.customers = FakeRepository([])
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


@pytest.mark.asyncio()
async def test_create_customer() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await create_customer(uow, cmd)
    customer_from_db = await uow.customers.get(customer.id)

    assert uow.committed is True
    assert customer == customer_from_db
    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == {}
    assert customer.version == 0
    assert customer.created_at is not None


@pytest.mark.asyncio()
async def test_customer_created_event_created() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await create_customer(uow, cmd)
    [event] = customer.events

    assert isinstance(event, CustomerCreatedEvent)
    assert isinstance(event.event_id, uuid.UUID)
    assert event.event_id != customer.id
    assert event.customer_id == customer.id
    assert event.name == "John Doe"
    assert event.credit_limit == Decimal("200.00")
    assert event.created_at == customer.created_at


@pytest.mark.asyncio()
async def test_created_customer_has_clean_available_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await create_customer(uow, cmd)

    assert customer.available_credit() == Decimal("200.00")
