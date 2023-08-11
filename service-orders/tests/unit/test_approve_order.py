import uuid
from decimal import Decimal

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand, CreateOrderCommand
from orders.events import OrderApprovedEvent
from orders.order import NotPendingOrderCannotBeApprovedError, OrderState
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_approve_not_existing_order() -> None:
    uow = FakeUnitOfWork()
    order_id = uuid.uuid4()
    cmd = ApproveOrderCommand(order_id=order_id)

    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.approve_order(uow, cmd)


@pytest.mark.asyncio()
async def test_approve_pending_order() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, cmd)

    await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.APPROVED


@pytest.mark.asyncio()
async def test_order_approved_event_published() -> None:
    uow = FakeUnitOfWork()
    create_order_cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, create_order_cmd)
    uow.events.clear()

    approve_order_cmd = ApproveOrderCommand(order_id=order.id)
    await use_cases.approve_order(uow, approve_order_cmd)

    [event] = uow.events.events
    assert isinstance(event, OrderApprovedEvent)
    assert event.correlation_id == approve_order_cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == create_order_cmd.customer_id
    assert event.state == OrderState.APPROVED


@pytest.mark.parametrize("order_state", [OrderState.REJECTED, OrderState.CANCELLED])
@pytest.mark.asyncio()
async def test_order_in_non_pending_state_cannot_be_approved(order_state: OrderState) -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, cmd)
    uow.events.clear()
    order.state = order_state
    await uow.orders.update(order)
    await uow.commit()

    with pytest.raises(NotPendingOrderCannotBeApprovedError, match=str(order.id)):
        await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    assert len(uow.events.events) == 0
    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == order_state
