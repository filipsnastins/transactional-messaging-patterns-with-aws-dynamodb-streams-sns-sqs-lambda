import uuid
from decimal import Decimal

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand, CancelOrderCommand, CreateOrderCommand
from orders.events import OrderCancelledEvent
from orders.order import OrderState, PendingOrderCannotBeCancelledError
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_cancel_not_existing_order() -> None:
    uow = FakeUnitOfWork()
    order_id = uuid.uuid4()

    cmd = CancelOrderCommand(order_id=order_id)
    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.cancel_order(uow, cmd)


@pytest.mark.asyncio()
async def test_cancel_approved_order() -> None:
    uow = FakeUnitOfWork()
    create_order_cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, create_order_cmd)
    approve_order_cmd = ApproveOrderCommand(order_id=order.id)
    await use_cases.approve_order(uow, approve_order_cmd)

    cancel_order_cmd = CancelOrderCommand(order_id=order.id)
    await use_cases.cancel_order(uow, cancel_order_cmd)

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.CANCELLED


@pytest.mark.asyncio()
async def test_order_cancelled_event_published() -> None:
    uow = FakeUnitOfWork()
    create_order_cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, create_order_cmd)
    approve_order_cmd = ApproveOrderCommand(order_id=order.id)
    await use_cases.approve_order(uow, approve_order_cmd)
    uow.events.clear()
    cancel_order_cmd = CancelOrderCommand(order_id=order.id)

    await use_cases.cancel_order(uow, cancel_order_cmd)

    [event] = uow.events.events
    assert isinstance(event, OrderCancelledEvent)
    assert event.correlation_id == cancel_order_cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == create_order_cmd.customer_id
    assert event.state == OrderState.CANCELLED


@pytest.mark.asyncio()
async def test_cannot_cancel_pending_order() -> None:
    uow = FakeUnitOfWork()
    create_order_cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, create_order_cmd)

    with pytest.raises(PendingOrderCannotBeCancelledError, match=str(order.id)):
        await use_cases.cancel_order(uow, CancelOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.PENDING
