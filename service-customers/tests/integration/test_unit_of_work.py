import datetime
import json
import uuid
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

from adapters import dynamodb
from adapters.customer_repository import CustomerAlreadyExistsError, DynamoDBCustomerRepository
from adapters.event_repository import EventAlreadyPublishedError
from customers.customer import Customer
from customers.events import CustomerCreatedEvent, Event
from service_layer.unit_of_work import DynamoDBUnitOfWork

pytestmark = pytest.mark.usefixtures("_mock_dynamodb")


class FailingDynamoDBCustomerRepository(DynamoDBCustomerRepository):
    async def create(self, customer: Customer) -> None:
        self.session.add(
            {
                "Put": {
                    "TableName": self.table_name,
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
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())
    await uow.customers.create(customer)
    await uow.commit()

    await uow.customers.create(customer)
    with pytest.raises(CustomerAlreadyExistsError, match=str(customer.id)):
        await uow.commit()


@pytest.mark.asyncio()
async def test_dynamodb_error_raised() -> None:
    uow = DynamoDBUnitOfWork.create()
    uow.customers = FailingDynamoDBCustomerRepository(dynamodb.get_aggregate_table_name(), uow.customers.session)
    customer = Customer.create(name="John Doe", credit_limit=Decimal("200.00"), correlation_id=uuid.uuid4())

    await uow.customers.create(customer)
    with pytest.raises(ClientError) as exc_info:
        await uow.commit()

    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"


@pytest.mark.asyncio()
async def test_events_published() -> None:
    uow = DynamoDBUnitOfWork.create()
    events: list[Event] = [
        CustomerCreatedEvent(
            event_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            name="John Doe",
            credit_limit=Decimal("200.00"),
            created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        ),
        CustomerCreatedEvent(
            event_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            name="Mary Doe",
            credit_limit=Decimal("300.00"),
            created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        ),
    ]

    await uow.events.publish(events)
    await uow.commit()

    message = await uow.events.get(events[0].event_id)
    assert message
    assert message.event_id == events[0].event_id
    assert message.aggregate_id == events[0].customer_id
    assert message.correlation_id == events[0].correlation_id
    assert message.topic == "customer--created"
    assert json.loads(message.message) == events[0].to_dict()
    assert message.created_at == events[0].created_at

    message = await uow.events.get(events[1].event_id)
    assert message
    assert message.event_id == events[1].event_id
    assert message.aggregate_id == events[1].customer_id
    assert message.correlation_id == events[1].correlation_id
    assert message.topic == "customer--created"
    assert json.loads(message.message) == events[1].to_dict()
    assert message.created_at == events[1].created_at


@pytest.mark.asyncio()
async def test_cannot_publish_event_with_the_same_event_id() -> None:
    uow = DynamoDBUnitOfWork.create()
    event_id = uuid.uuid4()
    event_1 = CustomerCreatedEvent(
        event_id=event_id,
        customer_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        name="John Doe",
        credit_limit=Decimal("200.00"),
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
    )
    event_2 = CustomerCreatedEvent(
        event_id=event_id,
        customer_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        name="Mary Doe",
        credit_limit=Decimal("300.00"),
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
    )
    await uow.events.publish([event_1])
    await uow.commit()

    await uow.events.publish([event_2])
    with pytest.raises(EventAlreadyPublishedError, match=str(event_id)):
        await uow.commit()
