from decimal import Decimal

import pytest
import pytest_asyncio

from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from service_layer import use_cases
from service_layer.response import CustomerCreatedResponse, ResponseTypes
from tests.unit.fakes import FakeUnitOfWork


@pytest.fixture()
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest_asyncio.fixture()
async def customer(uow: FakeUnitOfWork) -> Customer:
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    response = await use_cases.create_customer(uow, cmd)
    uow.events.clear()
    assert isinstance(response, CustomerCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    customer = await uow.customers.get(response.id)
    assert customer
    return customer
