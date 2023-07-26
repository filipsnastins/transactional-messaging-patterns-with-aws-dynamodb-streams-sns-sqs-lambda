import datetime
import uuid
from decimal import Decimal

import pytest
from adapters.repository import CustomerNotFoundError
from customers.customer import Customer
from service_layer.unit_of_work import DynamoDBCommitError, DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


@pytest.mark.asyncio()
async def test_session_not_committed_by_default() -> None:
    uow = DynamoDBUnitOfWork()
    customer = Customer(
        id=uuid.uuid4(),
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={},
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        version=0,
    )

    await uow.customers.create(customer)

    with pytest.raises(CustomerNotFoundError):
        await uow.customers.get(customer.id)


@pytest.mark.asyncio()
async def test_session_rollbacked() -> None:
    uow = DynamoDBUnitOfWork()
    customer = Customer(
        id=uuid.uuid4(),
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={},
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        version=0,
    )

    await uow.customers.create(customer)
    await uow.rollback()
    await uow.commit()

    with pytest.raises(CustomerNotFoundError):
        await uow.customers.get(customer.id)


@pytest.mark.asyncio()
async def test_commit_is_idempotent() -> None:
    uow = DynamoDBUnitOfWork()
    customer = Customer(
        id=uuid.uuid4(),
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={},
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        version=0,
    )

    await uow.customers.create(customer)
    await uow.commit()
    await uow.commit()

    customer_from_db = await uow.customers.get(customer.id)
    assert customer == customer_from_db


@pytest.mark.asyncio()
async def test_dynamodb_commit_error_raised_on_failing_condition_expression() -> None:
    uow = DynamoDBUnitOfWork()
    customer = Customer(id=uuid.uuid4(), name="John Doe", credit_limit=Decimal("200.00"))
    await uow.customers.create(customer)
    await uow.commit()

    await uow.customers.create(customer)
    with pytest.raises(DynamoDBCommitError) as exc_info:
        await uow.commit()

    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"
    assert exc_info.value.response["CancellationReasons"][0]["Code"] == "ConditionalCheckFailed"
    assert exc_info.value.response["CancellationReasons"][1]["Code"] == "None"
