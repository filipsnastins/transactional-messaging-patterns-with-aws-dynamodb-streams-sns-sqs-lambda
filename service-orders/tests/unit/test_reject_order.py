import uuid

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import RejectOrderCommand
from orders.events import OrderRejectedEvent
from orders.order import Order, OrderState
from service_layer import use_cases
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_reject_not_existing_order(uow: FakeUnitOfWork) -> None:
    order_id = uuid.uuid4()
    cmd = RejectOrderCommand(order_id=order_id)

    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.reject_order(uow, cmd)


@pytest.mark.asyncio()
async def test_reject_pending_order(uow: FakeUnitOfWork, order: Order) -> None:
    await use_cases.reject_order(uow, RejectOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.REJECTED


@pytest.mark.asyncio()
async def test_order_rejected_event_published(uow: FakeUnitOfWork, order: Order) -> None:
    cmd = RejectOrderCommand(order_id=order.id)

    await use_cases.reject_order(uow, cmd)

    [event] = uow.events.events
    assert isinstance(event, OrderRejectedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == order.customer_id
    assert event.state == OrderState.REJECTED
