import uuid
from decimal import Decimal
from unittest import mock

import pytest

from orders.commands import CreateOrderCommand
from orders.events import OrderCreatedEvent
from orders.order import Order, OrderState
from service_layer import use_cases
from service_layer.response import FailureResponse, OrderCreatedResponse, ResponseTypes
from tests.unit.fakes import FakeUnitOfWork


@pytest.mark.asyncio()
async def test_create_order(uow: FakeUnitOfWork) -> None:
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))

    response = await use_cases.create_order(uow, cmd)

    assert isinstance(response, OrderCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    order = await uow.orders.get(order_id=response.id)
    assert order
    assert order.id == response.id
    assert order.customer_id == cmd.customer_id
    assert order.state == OrderState.PENDING
    assert order.order_total == cmd.order_total
    assert order.version == 0
    assert order.created_at
    assert order.updated_at is None


@pytest.mark.asyncio()
async def test_order_created_event_published(uow: FakeUnitOfWork) -> None:
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))

    response = await use_cases.create_order(uow, cmd)

    assert isinstance(response, OrderCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    [event] = uow.events.messages
    assert isinstance(event, OrderCreatedEvent)
    assert event.event_id
    assert event.correlation_id == cmd.correlation_id
    assert event.order_id == response.id
    assert event.customer_id == cmd.customer_id
    assert event.state == OrderState.PENDING
    assert event.order_total == cmd.order_total


@pytest.mark.asyncio()
async def test_order_already_exists(uow: FakeUnitOfWork, order: Order) -> None:
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))

    with mock.patch("service_layer.use_cases.Order.create", return_value=order):
        response = await use_cases.create_order(uow, cmd)

    assert isinstance(response, FailureResponse)
    assert response.type == ResponseTypes.ORDER_ALREADY_EXISTS_ERROR
