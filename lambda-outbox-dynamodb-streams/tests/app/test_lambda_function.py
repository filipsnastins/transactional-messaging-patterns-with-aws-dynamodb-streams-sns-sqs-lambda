import datetime
import json
import uuid
from dataclasses import dataclass

import pytest
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_during_interval, probe_until
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from types_aiobotocore_sqs import SQSClient
from unit_of_work.dynamodb import DynamoDBSession

from lambda_outbox_dynamodb_streams.app import clients
from lambda_outbox_dynamodb_streams.app.lambda_function import async_record_handler
from lambda_outbox_dynamodb_streams.app.settings import get_settings

pytestmark = pytest.mark.usefixtures(
    "_environment", "_create_topics_and_queues", "_create_outbox_table", "_reset_moto_container_on_teardown"
)


@dataclass
class SampleMessage:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    created_at: datetime.datetime

    def serialize(self) -> str:
        return json.dumps({"message": "test-message"})


def record_factory(event_name: str) -> DynamoDBRecord:
    return DynamoDBRecord(
        {
            "eventID": "1e8883d7812c4016b68a365ad51dd453",
            "eventName": event_name,
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


def message_factory() -> SampleMessage:
    return SampleMessage(
        message_id=uuid.UUID("c79e7d16-4562-4350-ab53-f697bfc120e9"),
        aggregate_id=uuid.UUID("de8fe25c-21a5-4169-b8ad-bc5084333ba9"),
        correlation_id=uuid.UUID("ed5ff64d-946d-43b3-ada0-532cd8eb1fa7"),
        created_at=datetime.datetime(2023, 8, 15, 8, 24, 5, 961363, tzinfo=datetime.timezone.utc),
    )


@pytest.fixture()
def session() -> DynamoDBSession:
    return DynamoDBSession(clients.get_dynamodb_client)


@pytest.fixture()
def outbox_repository(session: DynamoDBSession) -> DynamoDBOutboxRepository:
    settings = get_settings()
    topic_map = {SampleMessage: "test-topic"}
    return DynamoDBOutboxRepository(settings.dynamodb_outbox_table_name, session, topic_map)


@pytest.mark.asyncio()
async def test_dynamodb_insert_event__message_dispatched(
    moto_sqs_client: SQSClient, session: DynamoDBSession, outbox_repository: DynamoDBOutboxRepository
) -> None:
    record = record_factory(event_name="INSERT")
    message = message_factory()
    await outbox_repository.publish([message])
    await session.commit()

    await async_record_handler(record)

    async def _assert_message_received() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "test-queue", JsonBase, dict[str, str])

        assert message == {"message": "test-message"}

    await probe_until(_assert_message_received, probe_interval=0.3, stop_after=8)


@pytest.mark.xfail(reason="Disabled because Moto Lambdas end up in an infinite loop when the same item is updated")
@pytest.mark.asyncio()
async def test_dynamodb_insert_event__message_marked_as_dispatched(
    session: DynamoDBSession, outbox_repository: DynamoDBOutboxRepository
) -> None:
    record = record_factory(event_name="INSERT")
    message = message_factory()
    await outbox_repository.publish([message])
    await session.commit()

    await async_record_handler(record)

    published_message = await outbox_repository.get(message_id=message.message_id)
    assert published_message
    assert published_message.is_dispatched is True
    assert published_message.dispatched_at


@pytest.mark.parametrize("event_name", ["MODIFY", "REMOVE"])
@pytest.mark.asyncio()
async def test_dynamodb_update_event__not_insert_message_skipped(moto_sqs_client: SQSClient, event_name: str) -> None:
    record = record_factory(event_name=event_name)

    await async_record_handler(record)

    async def _assert_message_received() -> None:
        messages = await snssqs_client.receive(moto_sqs_client, "test-queue", JsonBase, dict[str, str])

        assert len(messages) == 0

    await probe_during_interval(_assert_message_received, probe_interval=0.3, stop_after=5)
