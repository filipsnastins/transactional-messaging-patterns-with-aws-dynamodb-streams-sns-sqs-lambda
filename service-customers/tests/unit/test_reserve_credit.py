import uuid
from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from customers.events import (
    CustomerCreditReservationFailedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
    OrderCreatedExternalEvent,
)
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_customer_not_found() -> None:
    uow = FakeUnitOfWork()
    order_created_event = OrderCreatedExternalEvent(
        customer_id=uuid.uuid4(), order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )

    await use_cases.reserve_credit(uow, order_created_event)
    [event] = uow.events.events

    assert isinstance(event, CustomerValidationFailedEvent)
    assert event.correlation_id == order_created_event.correlation_id
    assert event.customer_id == event.customer_id
    assert event.order_id == order_created_event.order_id
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
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=order_total
    )

    await use_cases.reserve_credit(uow, order_created_event)
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.available_credit() == expected_available_credit
    assert customer_from_db.credit_reservations == {order_created_event.order_id: order_total}


@pytest.mark.asyncio()
async def test_reserve_credit_for_multiple_orders() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event_1 = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.55")
    )
    order_created_event_2 = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("79.45")
    )

    await use_cases.reserve_credit(uow, order_created_event_1)
    await use_cases.reserve_credit(uow, order_created_event_2)
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("20.00")
    assert customer_from_db.credit_reservations == {
        order_created_event_1.order_id: order_created_event_1.order_total,
        order_created_event_2.order_id: order_created_event_2.order_total,
    }


@pytest.mark.asyncio()
async def test_customer_credit_limit_reserved_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )

    await use_cases.reserve_credit(uow, order_created_event)
    [_, event] = uow.events.events

    assert isinstance(event, CustomerCreditReservedEvent)
    assert event.correlation_id == order_created_event.correlation_id
    assert event.customer_id == customer.id
    assert event.order_id == order_created_event.order_id


@pytest.mark.asyncio()
async def test_insufficient_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("300.00")
    )

    await use_cases.reserve_credit(uow, order_created_event)
    [_, event] = uow.events.events

    assert isinstance(event, CustomerCreditReservationFailedEvent)
    assert event.correlation_id == order_created_event.correlation_id
    assert event.customer_id == customer.id
    assert event.order_id == order_created_event.order_id
