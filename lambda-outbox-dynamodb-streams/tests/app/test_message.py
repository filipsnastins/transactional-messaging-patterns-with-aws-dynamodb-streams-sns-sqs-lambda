import datetime
import json
import uuid

import pytest
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord

from lambda_outbox_dynamodb_streams.app.message import create_published_message_from_stream_record


def test_create_published_message_from_stream_record() -> None:
    record = DynamoDBRecord(
        {
            "eventID": "1e8883d7812c4016b68a365ad51dd453",
            "eventName": "INSERT",
            "eventVersion": "1.0",
            "eventSource": "aws:dynamodb",
            "awsRegion": "us-east-1",
            "dynamodb": {
                "StreamViewType": "NEW_AND_OLD_IMAGES",
                "ApproximateCreationDateTime": "2023-08-15T08:24:08.202526",
                "SequenceNumber": "1100000000017454423009",
                "SizeBytes": 648,
                "Keys": {"PK": {"S": "MESSAGE#c79e7d16-4562-4350-ab53-f697bfc120e9"}},
                "NewImage": {
                    "PK": {"S": "MESSAGE#c79e7d16-4562-4350-ab53-f697bfc120e9"},
                    "MessageId": {"S": "c79e7d16-4562-4350-ab53-f697bfc120e9"},
                    "AggregateId": {"S": "de8fe25c-21a5-4169-b8ad-bc5084333ba9"},
                    "CorrelationId": {"S": "ed5ff64d-946d-43b3-ada0-532cd8eb1fa7"},
                    "Topic": {"S": "test-topic"},
                    "Message": {"S": '{"message": "test-message"}'},
                    "CreatedAt": {"S": "2023-08-15T08:24:05.961363+00:00"},
                },
                "OldImage": {},
            },
            "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/outbox/stream/2023-08-15T08:24:06.046495",
        }
    )

    message = create_published_message_from_stream_record(record)

    assert message
    assert message.message_id == uuid.UUID("c79e7d16-4562-4350-ab53-f697bfc120e9")
    assert message.aggregate_id == uuid.UUID("de8fe25c-21a5-4169-b8ad-bc5084333ba9")
    assert message.correlation_id == uuid.UUID("ed5ff64d-946d-43b3-ada0-532cd8eb1fa7")
    assert message.topic == "test-topic"
    assert message.message == json.dumps({"message": "test-message"})
    assert message.created_at == datetime.datetime(2023, 8, 15, 8, 24, 5, 961363, tzinfo=datetime.timezone.utc)
    assert message.is_dispatched is False
    assert message.dispatched_at is None


@pytest.mark.asyncio()
async def test_value_error_if_new_image_not_provided() -> None:
    record = DynamoDBRecord(
        {
            "eventID": "1e8883d7812c4016b68a365ad51dd453",
            "eventName": "INSERT",
            "eventVersion": "1.0",
            "eventSource": "aws:dynamodb",
            "awsRegion": "us-east-1",
            "dynamodb": {
                "StreamViewType": "NEW_AND_OLD_IMAGES",
                "ApproximateCreationDateTime": "2023-08-15T08:24:08.202526",
                "SequenceNumber": "1100000000017454423009",
                "SizeBytes": 648,
                "Keys": {"PK": {"S": "MESSAGE#c79e7d16-4562-4350-ab53-f697bfc120e9"}},
                "OldImage": {},
            },
            "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/outbox/stream/2023-08-15T08:24:06.046495",
        }
    )

    with pytest.raises(ValueError, match="PublishedMessage not created from stream record"):
        create_published_message_from_stream_record(record)
