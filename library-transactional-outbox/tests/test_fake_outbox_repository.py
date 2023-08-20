import uuid

import pytest

from tests.events import OrderCreatedEvent
from transactional_outbox.fakes import FakeOutboxRepository
from transactional_outbox.outbox import PublishedMessage


@pytest.fixture()
def repo() -> FakeOutboxRepository:
    return FakeOutboxRepository([])


@pytest.mark.asyncio()
async def test_publish_message(repo: FakeOutboxRepository) -> None:
    event_1 = OrderCreatedEvent(order_id=uuid.uuid4())
    event_2 = OrderCreatedEvent(order_id=uuid.uuid4())

    await repo.publish([event_1, event_2])

    assert repo.messages == [event_1, event_2]


@pytest.mark.asyncio()
async def test_get_message(repo: FakeOutboxRepository) -> None:
    order_id = uuid.uuid4()
    event = OrderCreatedEvent(order_id=order_id)

    await repo.publish([event])

    assert await repo.get(message_id=event.event_id) == PublishedMessage(
        message_id=event.event_id,
        correlation_id=event.correlation_id,
        aggregate_id=order_id,
        topic="OrderCreatedEvent",
        message=event.serialize(),
        created_at=event.created_at,
    )


@pytest.mark.asyncio()
async def test_clear_message_repository(repo: FakeOutboxRepository) -> None:
    event = OrderCreatedEvent(order_id=uuid.uuid4())
    await repo.publish([event])

    repo.clear()

    assert repo.messages == []


@pytest.mark.asyncio()
async def test_in_place_modifications_do_not_persist(repo: FakeOutboxRepository) -> None:
    event = OrderCreatedEvent(order_id=uuid.uuid4())

    await repo.publish([event])
    event.order_id = uuid.uuid4()

    assert event != await repo.get(message_id=event.event_id)


@pytest.mark.asyncio()
async def test_stored_message_object_is_copied(repo: FakeOutboxRepository) -> None:
    event = OrderCreatedEvent(order_id=uuid.uuid4())

    await repo.publish([event])

    assert event is not await repo.get(message_id=event.event_id)
