from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from customers.events import CustomerCreatedEvent
from service_layer import use_cases
from service_layer.response import CustomerCreatedResponse, ResponseTypes
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_create_customer(uow: FakeUnitOfWork) -> None:
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    response = await use_cases.create_customer(uow, cmd)

    assert isinstance(response, CustomerCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    customer = await uow.customers.get(response.id)
    assert customer
    assert customer.id == response.id
    assert customer.name == "John Doe"
    assert customer.credit_limit == Decimal("200.00")
    assert customer.credit_reservations == {}
    assert customer.version == 0
    assert customer.created_at
    assert customer.updated_at is None


@pytest.mark.asyncio()
async def test_customer_created_event_published(uow: FakeUnitOfWork) -> None:
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    response = await use_cases.create_customer(uow, cmd)

    assert isinstance(response, CustomerCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    [event] = uow.events.messages
    assert isinstance(event, CustomerCreatedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.customer_id == response.id
    assert event.name == "John Doe"
    assert event.credit_limit == Decimal("200.00")


@pytest.mark.asyncio()
async def test_new_customer_has_full_available_credit(uow: FakeUnitOfWork) -> None:
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))

    response = await use_cases.create_customer(uow, cmd)

    assert isinstance(response, CustomerCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    customer = await uow.customers.get(response.id)
    assert customer
    assert customer.available_credit() == Decimal("200.00")
