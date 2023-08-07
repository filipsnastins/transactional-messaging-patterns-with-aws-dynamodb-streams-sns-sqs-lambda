import uuid
from decimal import Decimal

import pytest
from tomodachi_outbox.message import Message

from adapters.customer_repository import AbstractCustomerRepository
from adapters.event_repository import AbstractEventRepository
from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from customers.events import (
    CustomerCreatedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
    Event,
    OrderCreatedExternalEvent,
)
from service_layer import use_cases
from service_layer.unit_of_work import AbstractUnitOfWork


class FakeCustomerRepository(AbstractCustomerRepository):
    def __init__(self, customers: list[Customer]) -> None:
        super().__init__()
        self._customers = customers

    async def create(self, customer: Customer) -> None:
        self._customers.append(customer)

    async def get(self, customer_id: uuid.UUID) -> Customer | None:
        return next((p for p in self._customers if p.id == customer_id), None)


class FakeEventRepository(AbstractEventRepository):
    def __init__(self, events: list[Event]) -> None:
        self.events = events

    async def publish(self, events: list[Event]) -> None:
        self.events.extend(events)

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


@pytest.mark.asyncio()
async def test_create_customer() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await use_cases.create_customer(uow, cmd)
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
async def test_create_customer__customer_created_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await use_cases.create_customer(uow, cmd)
    [event] = uow.events.events

    assert isinstance(event, CustomerCreatedEvent)
    assert isinstance(event.event_id, uuid.UUID)
    assert event.event_id != customer.id
    assert event.customer_id == customer.id
    assert event.name == "John Doe"
    assert event.credit_limit == Decimal("200.00")
    assert event.created_at == customer.created_at


@pytest.mark.asyncio()
async def test_create_customer__new_customer_has_full_available_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)

    assert customer.available_credit() == Decimal("200.00")


@pytest.mark.asyncio()
async def test_reserve_credit__customer_not_found() -> None:
    uow = FakeUnitOfWork()
    event = OrderCreatedExternalEvent(customer_id=uuid.uuid4(), order_id=uuid.uuid4(), order_total=Decimal("100.00"))

    await use_cases.reserve_credit(uow, event)
    [event] = uow.events.events

    assert isinstance(event, CustomerValidationFailedEvent)
    assert event.customer_id == event.customer_id
    assert event.order_id == event.order_id
    assert event.error == CustomerValidationErrors.CUSTOMER_NOT_FOUND


@pytest.mark.parametrize(
    ("credit_limit", "order_total", "expected_available_credit"),
    [
        (Decimal("200.00"), Decimal("0"), Decimal("200.00")),
        (Decimal("200.00"), Decimal("100.00"), Decimal("100.00")),
        (Decimal("200.00"), Decimal("100.01"), Decimal("99.99")),
        (Decimal("200.00"), Decimal("200.00"), Decimal("0.00")),
    ],
)
@pytest.mark.asyncio()
async def test_reserve_credit(credit_limit: Decimal, order_total: Decimal, expected_available_credit: Decimal) -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=credit_limit)
    customer = await use_cases.create_customer(uow, cmd)
    event = OrderCreatedExternalEvent(customer_id=customer.id, order_id=uuid.uuid4(), order_total=order_total)

    await use_cases.reserve_credit(uow, event)

    assert customer.available_credit() == expected_available_credit


@pytest.mark.asyncio()
async def test_reserve_credit__customer_credit_limit_reserved_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    event = OrderCreatedExternalEvent(
        customer_id=customer.id,
        order_id=uuid.uuid4(),
        order_total=Decimal("100.00"),
        created_at=customer.created_at,
    )

    await use_cases.reserve_credit(uow, event)
    [_, event] = uow.events.events

    assert isinstance(event, CustomerCreditReservedEvent)
    assert event.customer_id == customer.id
    assert event.order_id == event.order_id
