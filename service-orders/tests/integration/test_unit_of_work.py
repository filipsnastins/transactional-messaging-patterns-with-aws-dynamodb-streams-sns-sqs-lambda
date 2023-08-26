import uuid
from decimal import Decimal

import pytest
import structlog
from transactional_messaging.idempotent_consumer import MessageAlreadyProcessedError

from orders.order import Order
from service_layer.unit_of_work import DynamoDBUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_uow_is_idempotent__when_message_id_is_given() -> None:
    message_id = uuid.uuid4()
    order = Order.create(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    async with DynamoDBUnitOfWork(message_id=message_id) as uow:
        await uow.orders.create(order)
        await uow.commit()

    order = Order.create(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    with pytest.raises(MessageAlreadyProcessedError, match=str(message_id)):  # noqa: PT012
        async with DynamoDBUnitOfWork(message_id=message_id) as uow:
            await uow.orders.create(order)
            await uow.commit()

    assert await uow.orders.get(order_id=order.id) is None


@pytest.mark.asyncio()
async def test_uow_skips_idempotence_check__when_message_id_not_given() -> None:
    async with DynamoDBUnitOfWork() as uow:
        order = Order.create(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
        await uow.orders.create(order)
        await uow.commit()

    assert await uow.orders.get(order_id=order.id)

    async with DynamoDBUnitOfWork() as uow:
        order = Order.create(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
        await uow.orders.create(order)
        await uow.commit()

    assert await uow.orders.get(order_id=order.id)
