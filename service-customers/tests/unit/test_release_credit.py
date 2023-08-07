import uuid
from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from customers.events import CustomerValidationErrors, CustomerValidationFailedEvent, OrderCanceledExternalEvent
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_release_credit_for_non_existing_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    order_canceled_event = OrderCanceledExternalEvent(customer_id=customer.id, order_id=uuid.uuid4())

    await use_cases.release_credit(uow, order_canceled_event)
    [_, event] = uow.events.events
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.available_credit() == Decimal("200.00")
    assert isinstance(event, CustomerValidationFailedEvent)
    assert event.correlation_id == order_canceled_event.correlation_id
    assert event.customer_id == customer.id
    assert event.order_id == order_canceled_event.order_id
    assert event.error == CustomerValidationErrors.ORDER_NOT_FOUND
