import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from customers.commands import CreateCustomerCommand
from customers.customer import Customer
from service_layer import use_cases, views
from service_layer.response import CustomerCreatedResponse, FailureResponse, GetCustomerResponse, ResponseTypes
from service_layer.unit_of_work import DynamoDBUnitOfWork
from utils.time import datetime_to_str

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest_asyncio.fixture()
async def customer(uow: DynamoDBUnitOfWork) -> Customer:
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("249.99"))
    response = await use_cases.create_customer(uow, cmd)
    assert isinstance(response, CustomerCreatedResponse)
    assert response.type == ResponseTypes.SUCCESS
    customer = await uow.customers.get(response.id)
    assert customer
    return customer


@pytest.mark.asyncio()
async def test_get_not_existing_customer(uow: DynamoDBUnitOfWork) -> None:
    customer_id = uuid.uuid4()

    response = await views.get_customer(uow, customer_id=customer_id)

    assert isinstance(response, FailureResponse)
    assert response.to_dict() == {
        "error": "CUSTOMER_NOT_FOUND_ERROR",
        "_links": {
            "self": {"href": f"/customer/{customer_id}"},
        },
    }


@pytest.mark.asyncio()
async def test_get_customer(uow: DynamoDBUnitOfWork, customer: Customer) -> None:
    response = await views.get_customer(uow, customer_id=customer.id)

    assert isinstance(response, GetCustomerResponse)
    assert response.to_dict() == {
        "id": str(customer.id),
        "name": "John Doe",
        "credit_limit": 24999,
        "available_credit": 24999,
        "version": 0,
        "created_at": datetime_to_str(customer.created_at),
        "updated_at": None,
        "_links": {
            "self": {"href": f"/customer/{customer.id}"},
        },
    }
