import uuid
from decimal import Decimal

import pytest

from orders.order import Order
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_create_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    order = Order.create(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))

    await uow.orders.create(order)
    await uow.commit()

    order_from_db = await uow.orders.get(order.id)
    assert order_from_db == order
