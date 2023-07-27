import datetime
import uuid
from decimal import Decimal

import pytest
from adapters import dynamodb
from adapters.repository import CustomerAlreadyExistsError, DynamoDBRepository, DynamoDBSession
from botocore.exceptions import ClientError
from customers.customer import Customer
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


class FailingDynamoDBRepository(DynamoDBRepository):
    async def create(self, customer: Customer) -> None:
        self.session.add(
            {
                "ConditionCheck": {
                    "TableName": dynamodb.get_table_name(),
                    "Key": {"PK": {"S": f"CUSTOMER#{customer.id}"}},
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
        )
        self.session.add(
            {
                "Put": {
                    "TableName": dynamodb.get_table_name(),
                    "Item": {
                        "foo": {"S": "this-is-an-invalid-item"},
                    },
                }
            }
        )


@pytest.mark.asyncio()
async def test_session_not_committed_by_default() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer(
        id=uuid.uuid4(),
        name="John Doe",
        credit_limit=Decimal("200.00"),
        credit_reservations={},
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        version=0,
    )

    await uow.customers.create(customer)

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db is None


@pytest.mark.asyncio()
async def test_session_rollbacked() -> None:
    uow = DynamoDBUnitOfWork.create()
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

    customer_from_db = await uow.customers.get(customer.id)
    assert customer_from_db is None


@pytest.mark.asyncio()
async def test_commit_is_idempotent() -> None:
    uow = DynamoDBUnitOfWork.create()
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
async def test_domain_error_raised() -> None:
    uow = DynamoDBUnitOfWork.create()
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))
    await uow.customers.create(customer)
    await uow.commit()

    await uow.customers.create(customer)
    with pytest.raises(CustomerAlreadyExistsError, match=str(customer.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_dynamodb_error_raised() -> None:
    session = DynamoDBSession()
    uow = DynamoDBUnitOfWork(customers=FailingDynamoDBRepository(session))
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"))

    await uow.customers.create(customer)
    with pytest.raises(ClientError) as exc_info:
        await uow.commit()

    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"
