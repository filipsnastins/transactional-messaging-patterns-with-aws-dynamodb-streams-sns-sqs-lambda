import uuid
from decimal import Decimal

import pytest

from adapters.customer_repository import CustomerNotFoundError
from customers.commands import CreateCustomerCommand
from customers.customer import CreditNotReservedForOrderError
from customers.events import OrderCancelledExternalEvent, OrderCreatedExternalEvent
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_customer() -> None:
    uow = FakeUnitOfWork()
    order_cancelled_event = OrderCancelledExternalEvent(customer_id=uuid.uuid4(), order_id=uuid.uuid4())

    with pytest.raises(CustomerNotFoundError, match=str(order_cancelled_event.customer_id)):
        await use_cases.release_credit(uow, order_cancelled_event)


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_cancelled_event = OrderCancelledExternalEvent(customer_id=customer.id, order_id=uuid.uuid4())

    with pytest.raises(CreditNotReservedForOrderError, match=str(order_cancelled_event.order_id)):
        await use_cases.release_credit(uow, order_cancelled_event)


@pytest.mark.asyncio()
async def test_release_credit() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_created_event = OrderCreatedExternalEvent(
        customer_id=customer.id, order_id=uuid.uuid4(), order_total=Decimal("100.00")
    )
    await use_cases.reserve_credit(uow, order_created_event)
    order_cancelled_event = OrderCancelledExternalEvent(customer_id=customer.id, order_id=order_created_event.order_id)

    await use_cases.release_credit(uow, order_cancelled_event)

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("200.00")
