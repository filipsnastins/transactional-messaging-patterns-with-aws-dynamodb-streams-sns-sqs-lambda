import uuid
from decimal import Decimal

import pytest

from customers.customer import Customer, CustomerNotFoundError, OptimisticLockError
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_update_non_existing_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())

    await uow.customers.update(customer)

    with pytest.raises(CustomerNotFoundError, match=str(customer.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_create_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())

    await uow.customers.create(customer)
    await uow.commit()

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db == customer


@pytest.mark.asyncio()
async def test_update_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())
    await uow.customers.create(customer)
    await uow.commit()
    credit_reservations = {
        uuid.uuid4(): Decimal("100.00"),
        uuid.uuid4(): Decimal("200.00"),
    }

    customer.name = "John Doe Jr."
    customer.credit_limit = Decimal("399.99")
    customer.credit_reservations = credit_reservations
    await uow.customers.update(customer)
    await uow.commit()
    customer_from_db = await uow.customers.get(customer.id)

    assert customer_from_db
    assert customer_from_db.name == "John Doe Jr."
    assert customer_from_db.credit_limit == Decimal("399.99")
    assert customer_from_db.credit_reservations == credit_reservations
    assert customer_from_db.created_at == customer.created_at
    assert customer_from_db.version == 1


@pytest.mark.asyncio()
async def test_concurrent_customer_update_raises_optimistic_lock_error() -> None:
    uow = DynamoDBUnitOfWork.create()
    [customer, _] = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())
    await uow.customers.create(customer)
    await uow.commit()

    customer.credit_limit = Decimal("250.99")
    await uow.customers.update(customer)
    await uow.commit()

    customer.credit_limit = Decimal("399.49")
    await uow.customers.update(customer)
    with pytest.raises(OptimisticLockError):
        await uow.commit()

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db
    assert customer_from_db.credit_limit == Decimal("250.99")
    assert customer_from_db.version == 1
