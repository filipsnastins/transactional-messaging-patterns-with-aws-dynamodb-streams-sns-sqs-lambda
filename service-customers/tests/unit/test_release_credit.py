import uuid
from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from customers.customer import OrderNotFoundError
from customers.events import (
    CustomerCreditReleasedEvent,
    CustomerValidationErrors,
    CustomerValidationFailedEvent,
    OrderCanceledExternalEvent,
    OrderCreatedExternalEvent,
)
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_customer() -> None:
    uow = FakeUnitOfWork()
    order_canceled_event = OrderCanceledExternalEvent(customer_id=uuid.uuid4(), order_id=uuid.uuid4())

    await use_cases.release_credit(uow, order_canceled_event)
    [event] = uow.events.events

    assert isinstance(event, CustomerValidationFailedEvent)
    assert event.correlation_id == order_canceled_event.correlation_id
    assert event.customer_id == order_canceled_event.customer_id
    assert event.order_id == order_canceled_event.order_id
    assert event.error == CustomerValidationErrors.CUSTOMER_NOT_FOUND


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_canceled_event = OrderCanceledExternalEvent(customer_id=customer.id, order_id=uuid.uuid4())

    with pytest.raises(OrderNotFoundError, match=str(order_canceled_event.order_id)):
        await use_cases.release_credit(uow, order_canceled_event)


@pytest.mark.asyncio()
async def test_release_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )
    await use_cases.reserve_credit(uow, order_created_event)
    order_canceled_event = OrderCanceledExternalEvent(customer_id=customer.id, order_id=order_created_event.order_id)

    await use_cases.release_credit(uow, order_canceled_event)

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("200.00")


@pytest.mark.asyncio()
async def test_customer_credit_released_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )
    await use_cases.reserve_credit(uow, order_created_event)
    order_canceled_event = OrderCanceledExternalEvent(customer_id=customer.id, order_id=order_created_event.order_id)

    await use_cases.release_credit(uow, order_canceled_event)
    [_, _, event] = uow.events.events

    assert isinstance(event, CustomerCreditReleasedEvent)
    assert event.correlation_id == order_canceled_event.correlation_id
    assert event.customer_id == order_canceled_event.customer_id
    assert event.order_id == order_canceled_event.order_id
