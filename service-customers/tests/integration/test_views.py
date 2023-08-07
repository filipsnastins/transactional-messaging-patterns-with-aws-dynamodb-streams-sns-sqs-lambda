import uuid
from decimal import Decimal

import pytest

from customers.commands import CreateCustomerCommand
from service_layer import use_cases, views
from service_layer.unit_of_work import DynamoDBUnitOfWork
from utils.time import datetime_to_str

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_get_not_existing_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer_id = uuid.uuid4()

    response = await views.get_customer(uow, customer_id=customer_id)

    assert response.to_dict() == {
        "error": "CUSTOMER_NOT_FOUND",
        "_links": {
            "self": {"href": f"/customer/{customer_id}"},
        },
    }


@pytest.mark.asyncio()
async def test_get_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("249.99"))
    customer = await use_cases.create_customer(uow, cmd)

    response = await views.get_customer(uow, customer_id=customer.id)

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
