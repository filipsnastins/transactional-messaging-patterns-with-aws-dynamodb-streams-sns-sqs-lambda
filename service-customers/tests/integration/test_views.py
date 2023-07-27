import uuid
from decimal import Decimal

import pytest
from customers.commands import CreateCustomerCommand
from customers.customer import CustomerNotFoundError
from service_layer import use_cases, views
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_get_not_existing_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer_id = uuid.uuid4()

    with pytest.raises(CustomerNotFoundError, match=str(customer_id)):
        await views.get_customer(uow, customer_id=customer_id)


@pytest.mark.asyncio()
async def test_get_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    cmd = CreateCustomerCommand(name="John Doe", credit_limit=Decimal("200.00"))
    customer = await use_cases.create_customer(uow, cmd)
    customer.events = []

    customer_from_db = await views.get_customer(uow, customer_id=customer.id)

    assert customer_from_db == customer
