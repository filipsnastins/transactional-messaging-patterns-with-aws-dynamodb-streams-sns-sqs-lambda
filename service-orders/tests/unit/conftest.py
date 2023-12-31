import uuid
from decimal import Decimal
from typing import AsyncGenerator

import pytest_asyncio

from orders.commands import CreateOrderCommand
from orders.order import Order
from service_layer import use_cases
from service_layer.response import OrderCreatedResponse
from service_layer.unit_of_work import UnitOfWork
from tests.unit.fakes import FakeUnitOfWork


@pytest_asyncio.fixture()
async def uow() -> AsyncGenerator[UnitOfWork, None]:
    async with FakeUnitOfWork() as uow:
        yield uow


@pytest_asyncio.fixture()
async def order(uow: FakeUnitOfWork) -> Order:
    cmd = CreateOrderCommand(customer_id=uuid.uuid4(), order_total=Decimal("200.00"))
    response = await use_cases.create_order(uow, cmd)
    uow.events.clear()
    assert isinstance(response, OrderCreatedResponse)
    order = await uow.orders.get(order_id=response.id)
    assert order
    return order
