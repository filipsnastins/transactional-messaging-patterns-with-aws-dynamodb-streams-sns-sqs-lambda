import uuid
from decimal import Decimal

import pytest

from orders.commands import CreateOrderCommand
from service_layer import use_cases, views
from service_layer.unit_of_work import DynamoDBUnitOfWork
from utils.time import datetime_to_str

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_get_not_existing_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    order_id = uuid.uuid4()

    response = await views.get_order(uow, order_id=order_id)

    assert response.to_dict() == {
        "id": str(order_id),
        "error": "ORDER_NOT_FOUND",
        "_links": {
            "self": {"href": f"/order/{order_id}"},
        },
    }


@pytest.mark.asyncio()
async def test_get_order() -> None:
    uow = DynamoDBUnitOfWork.create()
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), total_amount=Decimal("123.99"))
    order = await use_cases.create_order(uow, cmd)

    response = await views.get_order(uow, order_id=order.id)

    assert response.to_dict() == {
        "id": str(order.id),
        "customer_id": str(cmd.customer_id),
        "state": "PENDING",
        "total_amount": 12399,
        "version": 0,
        "created_at": datetime_to_str(order.created_at),
        "updated_at": None,
        "_links": {
            "self": {"href": f"/order/{order.id}"},
        },
    }
