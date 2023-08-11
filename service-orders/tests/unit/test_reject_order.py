import uuid
from decimal import Decimal

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import CreateOrderCommand, RejectOrderCommand
from orders.events import OrderRejectedEvent
from orders.order import OrderState
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_reject_not_existing_order() -> None:
    uow = FakeUnitOfWork()
    order_id = uuid.uuid4()
    cmd = RejectOrderCommand(order_id=order_id)

    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.reject_order(uow, cmd)


@pytest.mark.asyncio()
async def test_reject_pending_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, cmd)

    await use_cases.reject_order(uow, RejectOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.REJECTED


@pytest.mark.asyncio()
async def test_order_rejected_event_published() -> None:
    uow = FakeUnitOfWork()
    create_order_cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, create_order_cmd)
    uow.events.clear()
    reject_order_cmd = RejectOrderCommand(order_id=order.id)

    await use_cases.reject_order(uow, reject_order_cmd)

    [event] = uow.events.events
    assert isinstance(event, OrderRejectedEvent)
    assert event.correlation_id == reject_order_cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == create_order_cmd.customer_id
    assert event.state == OrderState.REJECTED
