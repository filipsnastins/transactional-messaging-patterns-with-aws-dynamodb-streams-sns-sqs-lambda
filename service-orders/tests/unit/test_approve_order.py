import uuid
from decimal import Decimal

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand, CreateOrderCommand
from orders.order import OrderState
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
async def test_pending_order_approved() -> None:
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    order = await use_cases.create_order(uow, cmd)

    await use_cases.approve_order(uow, ApproveOrderCommand(order_id=order.id))

    order_from_db = await uow.orders.get(order_id=order.id)
    assert order_from_db
    assert order_from_db.state == OrderState.APPROVED