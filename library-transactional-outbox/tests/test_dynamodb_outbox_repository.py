import datetime
import json
import uuid
from dataclasses import dataclass, field

import pytest
from unit_of_work.dynamodb import DynamoDBClientFactory, DynamoDBSession

from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from transactional_outbox.dynamodb.repository import UnknownTopicError
from transactional_outbox.utils.time import datetime_to_str, utcnow

pytestmark = pytest.mark.usefixtures("_create_outbox_table", "_reset_moto_container_on_teardown")


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    order_id: uuid.UUID
    created_at: datetime.datetime = field(default_factory=utcnow)

    @property
    def message_id(self) -> uuid.UUID:
        return self.event_id

    @property
    def aggregate_id(self) -> uuid.UUID:
        return self.order_id

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "correlation_id": str(self.correlation_id),
            "order_id": str(self.order_id),
            "created_at": datetime_to_str(self.created_at),
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())


@dataclass(kw_only=True)
class OrderCreatedEvent(Event):
    pass


@dataclass(kw_only=True)
class UnknownOrderEvent(Event):
    pass


@pytest.fixture()
def session(client_factory: DynamoDBClientFactory) -> DynamoDBSession:
    return DynamoDBSession(client_factory)


@pytest.fixture()
def repo(session: DynamoDBSession) -> DynamoDBOutboxRepository:
    TOPIC_MAP = {
        OrderCreatedEvent: "order--created",
    }
    return DynamoDBOutboxRepository(table_name="orders-outbox", session=session, topic_map=TOPIC_MAP)


@pytest.mark.asyncio()
async def test_publish_message(session: DynamoDBSession, repo: DynamoDBOutboxRepository) -> None:
    event = OrderCreatedEvent(order_id=uuid.uuid4())

    await repo.publish([event])
    await session.commit()

    published_message = await repo.get(message_id=event.event_id)
    assert published_message
    assert published_message.message_id == event.event_id
    assert published_message.correlation_id == event.correlation_id
    assert published_message.aggregate_id == event.order_id
    assert published_message.topic == "order--created"
    assert json.loads(published_message.message) == event.to_dict()
    assert published_message.created_at == event.created_at
    assert published_message.is_dispatched is False
    assert published_message.dispatched_at is None


@pytest.mark.asyncio()
async def test_unknown_message_topic_raises(repo: DynamoDBOutboxRepository) -> None:
    event = UnknownOrderEvent(order_id=uuid.uuid4())  # Not present in TOPIC_MAP

    with pytest.raises(UnknownTopicError, match="UnknownOrderEvent"):
        await repo.publish([event])


@pytest.mark.asyncio()
async def test_get_not_dispatched_messages(session: DynamoDBSession, repo: DynamoDBOutboxRepository) -> None:
    event_1 = OrderCreatedEvent(order_id=uuid.uuid4())
    event_2 = OrderCreatedEvent(order_id=uuid.uuid4())
    event_3 = OrderCreatedEvent(order_id=uuid.uuid4())

    await repo.publish([event_1, event_2, event_3])
    await session.commit()

    not_dispatched_messages = await repo.get_not_dispatched_messages()
    assert len(not_dispatched_messages) == 3
    assert not_dispatched_messages[0] == await repo.get(message_id=event_1.event_id)
    assert not_dispatched_messages[1] == await repo.get(message_id=event_2.event_id)
    assert not_dispatched_messages[2] == await repo.get(message_id=event_3.event_id)


@pytest.mark.asyncio()
async def test_mark_dispatched(session: DynamoDBSession, repo: DynamoDBOutboxRepository) -> None:
    event = OrderCreatedEvent(order_id=uuid.uuid4())
    await repo.publish([event])
    await session.commit()

    await repo.mark_dispatched(message_id=event.event_id)

    published_message = await repo.get(message_id=event.event_id)
    assert published_message
    assert published_message.is_dispatched is True
    assert published_message.dispatched_at
    assert datetime.timedelta(seconds=1) > utcnow() - published_message.dispatched_at


@pytest.mark.asyncio()
async def test_dispatched_message_removed_from_not_dispatched_messages_collection(
    session: DynamoDBSession, repo: DynamoDBOutboxRepository
) -> None:
    event_1 = OrderCreatedEvent(order_id=uuid.uuid4())
    event_2 = OrderCreatedEvent(order_id=uuid.uuid4())
    await repo.publish([event_1, event_2])
    await session.commit()

    await repo.mark_dispatched(message_id=event_1.event_id)

    not_dispatched_messages = await repo.get_not_dispatched_messages()
    assert len(not_dispatched_messages) == 1
    assert not_dispatched_messages[0] == await repo.get(message_id=event_2.event_id)
