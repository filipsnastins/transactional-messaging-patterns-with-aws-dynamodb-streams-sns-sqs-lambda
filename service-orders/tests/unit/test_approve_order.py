import uuid

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand
from orders.events import OrderApprovedEvent
from orders.order import NotPendingOrderCannotBeApprovedError, Order, OrderState
from service_layer import use_cases
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_approve_not_existing_order(uow: FakeUnitOfWork) -> None:
    order_id = uuid.uuid4()
    cmd = ApproveOrderCommand(order_id=order_id)

    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.approve_order(uow, cmd)


@pytest.mark.asyncio()
async def test_approve_pending_order(uow: FakeUnitOfWork, order: Order) -> None:
    await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.APPROVED


@pytest.mark.asyncio()
async def test_order_approved_event_published(uow: FakeUnitOfWork, order: Order) -> None:
    cmd = ApproveOrderCommand(order_id=order.id)

    await use_cases.approve_order(uow, cmd)

    [event] = uow.events.messages
    assert isinstance(event, OrderApprovedEvent)
    assert event.correlation_id == cmd.correlation_id
    assert event.order_id == order.id
    assert event.customer_id == order.customer_id
    assert event.state == OrderState.APPROVED


@pytest.mark.parametrize("order_state", [OrderState.REJECTED, OrderState.CANCELLED])
@pytest.mark.asyncio()
async def test_order_in_non_pending_state_cannot_be_approved(
    uow: FakeUnitOfWork, order: Order, order_state: OrderState
) -> None:
    order.state = order_state
    await uow.orders.update(order)
    await uow.commit()

    with pytest.raises(NotPendingOrderCannotBeApprovedError, match=str(order.id)):
        await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    assert len(uow.events.messages) == 0
    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == order_state
