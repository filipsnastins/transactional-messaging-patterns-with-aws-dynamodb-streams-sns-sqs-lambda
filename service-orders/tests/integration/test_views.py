import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from orders.commands import CreateOrderCommand
from orders.order import Order
from service_layer import use_cases, views
from service_layer.response import FailureResponse, GetOrderResponse, OrderCreatedResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork
from utils.time import datetime_to_str

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest_asyncio.fixture()
async def order(uow: DynamoDBUnitOfWork) -> Order:
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("123.99"))
    response = await use_cases.create_order(uow, cmd)
    assert isinstance(response, OrderCreatedResponse)
    order = await uow.orders.get(order_id=response.id)
    assert order
    return order


@pytest.mark.asyncio()
async def test_get_not_existing_order(uow: DynamoDBUnitOfWork) -> None:
    order_id = uuid.uuid4()

    response = await views.get_order(uow, order_id=order_id)

    assert isinstance(response, FailureResponse)
    assert response.to_dict() == {
        "error": "ORDER_NOT_FOUND_ERROR",
        "_links": {
            "self": {"href": f"/order/{order_id}"},
            "cancel": {"href": f"/order/{order_id}/cancel"},
        },
    }


@pytest.mark.asyncio()
async def test_get_order(uow: DynamoDBUnitOfWork, order: Order) -> None:
    response = await views.get_order(uow, order_id=order.id)

    assert isinstance(response, GetOrderResponse)
    assert response.to_dict() == {
        "id": str(order.id),
        "customer_id": str(order.customer_id),
        "state": "PENDING",
        "order_total": 12399,
        "version": 0,
        "created_at": datetime_to_str(order.created_at),
        "updated_at": None,
        "_links": {
            "self": {"href": f"/order/{order.id}"},
            "cancel": {"href": f"/order/{order.id}/cancel"},
        },
    }
