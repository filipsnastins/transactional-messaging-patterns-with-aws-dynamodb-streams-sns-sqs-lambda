import uuid
from decimal import Decimal

import pytest
import structlog
from transactional_outbox.idempotent_consumer import MessageAlreadyProcessedError

from customers.customer import Customer
from service_layer.unit_of_work import DynamoDBUnitOfWork

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_uow_is_idempotent__when_message_id_is_given() -> None:
    message_id = uuid.uuid4()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
    async with DynamoDBUnitOfWork(message_id=message_id) as uow:
        await uow.customers.create(customer)
        await uow.commit()

    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
    with pytest.raises(MessageAlreadyProcessedError, match=str(message_id)):  # noqa: PT012
        async with DynamoDBUnitOfWork(message_id=message_id) as uow:
            await uow.customers.create(customer)
            await uow.commit()

    assert await uow.customers.get(customer_id=customer.id) is None


@pytest.mark.asyncio()
async def test_uow_skips_idempotence_check__when_message_id_not_given() -> None:
    async with DynamoDBUnitOfWork() as uow:
        customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
        await uow.customers.create(customer)
        await uow.commit()

    assert await uow.customers.get(customer_id=customer.id)

    async with DynamoDBUnitOfWork() as uow:
        customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
        await uow.customers.create(customer)
        await uow.commit()

    assert await uow.customers.get(customer_id=customer.id)
