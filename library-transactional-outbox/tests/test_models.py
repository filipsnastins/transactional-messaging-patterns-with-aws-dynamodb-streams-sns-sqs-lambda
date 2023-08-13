import datetime
import uuid

from transactional_outbox.repository import PublishedMessage


def test_create_published_message_model() -> None:
    msg = PublishedMessage(
        message_id=uuid.UUID("a3f3a3a3-3a3a-3a3a-3a3a-3a3a3a3a3a3a"),
        aggregate_id=uuid.UUID("b3f3b3b3-3b3b-3b3b-3b3b-3b3b3b3b3b3b"),
        correlation_id=uuid.UUID("c3f3c3c3-3c3c-3c3c-3c3c-3c3c3c3c3c3c"),
        topic="test-topic",
        message="test-message",
        created_at=datetime.datetime(2021, 1, 1, 0, 0, 0, 0).replace(tzinfo=datetime.UTC),
        is_dispatched=False,
        dispatched_at=None,
    )

    assert msg.message_id == uuid.UUID("a3f3a3a3-3a3a-3a3a-3a3a-3a3a3a3a3a3a")
    assert msg.aggregate_id == uuid.UUID("b3f3b3b3-3b3b-3b3b-3b3b-3b3b3b3b3b3b")
    assert msg.correlation_id == uuid.UUID("c3f3c3c3-3c3c-3c3c-3c3c-3c3c3c3c3c3c")
    assert msg.topic == "test-topic"
    assert msg.message == "test-message"
    assert msg.created_at == datetime.datetime(2021, 1, 1, 0, 0, 0, 0).replace(tzinfo=datetime.UTC)
    assert msg.is_dispatched is False
    assert msg.dispatched_at is None


def test_mark_message_as_dispatched() -> None:
    msg = PublishedMessage(
        message_id=uuid.UUID("a3f3a3a3-3a3a-3a3a-3a3a-3a3a3a3a3a3a"),
        aggregate_id=uuid.UUID("b3f3b3b3-3b3b-3b3b-3b3b-3b3b3b3b3b3b"),
        correlation_id=uuid.UUID("c3f3c3c3-3c3c-3c3c-3c3c-3c3c3c3c3c3c"),
        topic="test-topic",
        message="test-message",
        created_at=datetime.datetime(2021, 1, 1, 0, 0, 0, 0).replace(tzinfo=datetime.UTC),
        is_dispatched=True,
        dispatched_at=datetime.datetime(2022, 1, 1, 0, 0, 0, 0).replace(tzinfo=datetime.UTC),
    )

    assert msg.is_dispatched is True
    assert msg.dispatched_at == datetime.datetime(2022, 1, 1, 0, 0, 0, 0).replace(tzinfo=datetime.UTC)
