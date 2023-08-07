import datetime
import json
import uuid

from lambda_outbox_dynamodb_streams.app.message import Message


def test_message_model() -> None:
    message_id = uuid.uuid4()
    aggregate_id = uuid.uuid4()
    correlation_id = uuid.uuid4()
    created_at = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    message = Message(
        message_id=message_id,
        aggregate_id=aggregate_id,
        correlation_id=correlation_id,
        topic="test-topic",
        message=json.dumps({"message": "test-message"}),
        created_at=created_at,
    )

    assert message.message_id == message_id
    assert message.aggregate_id == aggregate_id
    assert message.correlation_id == correlation_id
    assert message.topic == "test-topic"
    assert message.message == json.dumps({"message": "test-message"})
    assert message.created_at == created_at
