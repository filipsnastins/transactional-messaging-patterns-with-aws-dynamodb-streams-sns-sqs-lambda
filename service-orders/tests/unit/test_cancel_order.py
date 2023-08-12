import uuid

import pytest

from orders.commands import ApproveOrderCommand, CancelOrderCommand
from orders.events import OrderCancelledEvent
from orders.order import Order, OrderState
from service_layer import use_cases
from service_layer.response import FailureResponse, OrderCancelledResponse, ResponseTypes
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_cancel_not_existing_order(uow: FakeUnitOfWork) -> None:
    order_id = uuid.uuid4()
    cmd = CancelOrderCommand(order_id=order_id)

    response = await use_cases.cancel_order(uow, cmd)

    assert isinstance(response, FailureResponse)
    assert response.type == ResponseTypes.ORDER_NOT_FOUND_ERROR


@pytest.mark.asyncio()
async def test_cancel_approved_order(uow: FakeUnitOfWork, order: Order) -> None:
    await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    response = await use_cases.cancel_order(uow, CancelOrderCommand(order_id=order.id))

    assert isinstance(response, OrderCancelledResponse)
    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.CANCELLED


@pytest.mark.asyncio()
async def test_order_cancelled_event_published(uow: FakeUnitOfWork, order: Order) -> None:
    await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))
    uow.events.clear()
    cmd = CancelOrderCommand(order_id=order.id)

    await use_cases.cancel_order(uow, cmd)

    [event] = uow.events.events
    assert isinstance(event, OrderCancelledEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == order.customer_id
    assert event.state == OrderState.CANCELLED


@pytest.mark.asyncio()
async def test_cannot_cancel_pending_order(uow: FakeUnitOfWork, order: Order) -> None:
    response = await use_cases.cancel_order(uow, CancelOrderCommand(order_id=order.id))

    assert isinstance(response, FailureResponse)
    assert response.type == ResponseTypes.PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR
    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.PENDING
