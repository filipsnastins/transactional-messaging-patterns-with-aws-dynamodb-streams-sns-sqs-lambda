import uuid
from decimal import Decimal

import pytest

from customers.commands import ReserveCreditCommand
from customers.customer import Customer
from customers.events import (
    CustomerCreditReservationFailedEvent,
    CustomerCreditReservedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
)
from service_layer import use_cases
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_customer_not_found(uow: FakeUnitOfWork) -> None:
    cmd = ReserveCreditCommand(customer_id=uuid.uuid4(), order_id=uuid.uuid4(), order_total=Decimal("100.00"))

    await use_cases.reserve_credit(uow, cmd)

    [event] = uow.events.messages
    assert isinstance(event, CustomerValidationFailedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.customer_id == event.customer_id
    assert event.order_id == cmd.order_id
    assert event.error == CustomerValidationErrors.CUSTOMER_NOT_FOUND_ERROR


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
async def test_reserve_credit(
    uow: FakeUnitOfWork,
    customer: Customer,
    credit_limit: Decimal,
    order_total: Decimal,
    expected_available_credit: Decimal,
) -> None:
    customer.credit_limit = credit_limit
    await uow.customers.update(customer)
    cmd = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=order_total)

    await use_cases.reserve_credit(uow, cmd)
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.available_credit() == expected_available_credit
    assert customer_from_db.credit_reservations == {cmd.order_id: order_total}


@pytest.mark.asyncio()
async def test_reserve_credit_for_multiple_orders(uow: FakeUnitOfWork, customer: Customer) -> None:
    customer.credit_limit = Decimal("200.00")
    await uow.customers.update(customer)
    cmd_1 = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.55"))
    cmd_2 = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("79.45"))

    await use_cases.reserve_credit(uow, cmd_1)
    await use_cases.reserve_credit(uow, cmd_2)
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("20.00")
    assert customer_from_db.credit_reservations == {
        cmd_1.order_id: cmd_1.order_total,
        cmd_2.order_id: cmd_2.order_total,
    }


@pytest.mark.asyncio()
async def test_customer_credit_limit_reserved_event_published(uow: FakeUnitOfWork, customer: Customer) -> None:
    customer.credit_limit = Decimal("200.00")
    await uow.customers.update(customer)
    cmd = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00"))

    await use_cases.reserve_credit(uow, cmd)

    [event] = uow.events.messages
    assert isinstance(event, CustomerCreditReservedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.customer_id == customer.id
    assert event.order_id == cmd.order_id


@pytest.mark.asyncio()
async def test_insufficient_credit(uow: FakeUnitOfWork, customer: Customer) -> None:
    customer.credit_limit = Decimal("200.00")
    await uow.customers.update(customer)
    cmd = ReserveCreditCommand(customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("300.00"))

    await use_cases.reserve_credit(uow, cmd)

    [event] = uow.events.messages
    assert isinstance(event, CustomerCreditReservationFailedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.customer_id == customer.id
    assert event.order_id == cmd.order_id
