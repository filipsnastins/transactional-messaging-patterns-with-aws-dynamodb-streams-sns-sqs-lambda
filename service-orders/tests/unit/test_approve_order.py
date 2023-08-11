import uuid

import pytest

from adapters.order_repository import OrderNotFoundError
from orders.commands import ApproveOrderCommand
from service_layer import use_cases
from tests.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_approve_not_existing_order() -> None:
    uow = FakeUnitOfWork()
    order_id = uuid.uuid4()
    cmd = ApproveOrderCommand(order_id=order_id)

    with pytest.raises(OrderNotFoundError, match=str(order_id)):
        await use_cases.approve_order(uow, cmd)
