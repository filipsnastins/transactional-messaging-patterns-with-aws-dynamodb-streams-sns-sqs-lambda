import uuid
from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from customers.events import CustomerCreatedEvent
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_create_customer() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await use_cases.create_customer(uow, cmd)
    customer_from_db = await uow.customers.get(customer.id)

    assert customer == customer_from_db
    assert isinstance(customer.id, uuid.UUID)
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == {}
    assert customer.version == 0
    assert customer.created_at
    assert customer.updated_at is None


@pytest.mark.asyncio()
async def test_customer_created_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    customer = await use_cases.create_customer(uow, cmd)
    [event] = uow.events.events

    assert isinstance(event, CustomerCreatedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.customer_id == customer.id
    assert event.name == "John Doe"
    assert event.credit_limit == Decimal("200.00")
    assert event.created_at == customer.created_at


@pytest.mark.asyncio()
async def test_new_customer_has_full_available_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)

    assert customer.available_credit() == Decimal("200.00")
