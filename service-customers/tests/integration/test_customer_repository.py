import uuid
from decimal import Decimal

import pytest

from adapters.customer_repository import CustomerAlreadyExistsError, CustomerNotFoundError, OptimisticLockError
from customers.customer import Customer
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_update_non_existing_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    await uow.customers.update(customer)

    with pytest.raises(CustomerNotFoundError, match=str(customer.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_create_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    await uow.customers.create(customer)
    await uow.commit()

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db == customer


@pytest.mark.asyncio()
async def test_customer_already_exists() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
    await uow.customers.create(customer)
    await uow.commit()

    await uow.customers.create(customer)
    with pytest.raises(CustomerAlreadyExistsError, match=str(customer.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_update_customer() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
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
    assert customer_from_db.version == 1
    assert customer_from_db.created_at == customer.created_at
    assert customer_from_db.updated_at
    assert customer_from_db.updated_at > customer.created_at


@pytest.mark.asyncio()
async def test_concurrent_customer_update_raises_optimistic_lock_error() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
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
