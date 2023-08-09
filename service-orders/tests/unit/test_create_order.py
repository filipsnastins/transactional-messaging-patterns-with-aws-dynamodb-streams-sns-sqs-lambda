import uuid
from decimal import Decimal

import pytest

from orders.commands import CreateOrderCommand
from orders.events import OrderCreatedEvent
from orders.order import OrderState
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_create_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), total_amount=Decimal("200.00"))

    order = await use_cases.create_order(uow, cmd)
    order_from_db = await uow.orders.get(order_id=order.id)

    assert order == order_from_db
    assert isinstance(order.id, uuid.UUID)
    assert order.customer_id == cmd.customer_id
    assert order.total_amount == cmd.total_amount
    assert order.state == OrderState.PENDING
    assert order.version == 0
    assert order.created_at
    assert order.updated_at is None


@pytest.mark.asyncio()
async def test_order_created_event_published() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), total_amount=Decimal("200.00"))

    order = await use_cases.create_order(uow, cmd)
    [event] = uow.events.events

    assert isinstance(event, OrderCreatedEvent)
    assert event.event_id
    assert event.correlation_id == cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == cmd.customer_id
    assert event.total_amount == cmd.total_amount
    assert event.created_at == order.created_at
