import pytest
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_during_interval, probe_until
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from types_aiobotocore_sqs import SQSClient
from unit_of_work.dynamodb import DynamoDBSession

from lambda_outbox_dynamodb_streams.app.lambda_function import async_record_handler
from tests.fakes import message_factory, record_factory

pytestmark = pytest.mark.usefixtures(
    "_environment", "_create_topics_and_queues", "_create_outbox_table", "_reset_moto_container_on_teardown"
)


@pytest.mark.asyncio()
async def test_dynamodb_streams_insert_record__message_dispatched(
    moto_sqs_client: SQSClient, session: DynamoDBSession, outbox_repository: DynamoDBOutboxRepository
) -> None:
    record = record_factory(event_name="INSERT")
    message = message_factory()
    await outbox_repository.publish([message])
    await session.commit()

    await async_record_handler(record)

    async def _assert_message_received() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "autotest-test-queue", JsonBase, dict[str, str])

        assert message == {"message": "test-message"}

    await probe_until(_assert_message_received, probe_interval=0.3, stop_after=8)


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
    assert published_message.approximate_dispatch_count == 1
    assert published_message.is_dispatched is True
    assert published_message.last_dispatched_at


@pytest.mark.asyncio()
async def test_dispatch_the_same_message_twice(
    session: DynamoDBSession, outbox_repository: DynamoDBOutboxRepository
) -> None:
    record = record_factory(event_name="INSERT")
    message = message_factory()
    await outbox_repository.publish([message])
    await session.commit()

    await async_record_handler(record)
    await async_record_handler(record)

    published_message = await outbox_repository.get(message_id=message.message_id)
    assert published_message
    assert published_message.approximate_dispatch_count == 2


@pytest.mark.parametrize("event_name", ["MODIFY", "REMOVE"])
@pytest.mark.asyncio()
async def test_dynamodb_update_event__not_insert_dynamodb_stream_record_skipped(
    moto_sqs_client: SQSClient, event_name: str
) -> None:
    record = record_factory(event_name=event_name)

    await async_record_handler(record)

    async def _assert_message_received() -> None:
        messages = await snssqs_client.receive(moto_sqs_client, "autotest-test-queue", JsonBase, dict[str, str])

        assert len(messages) == 0

    await probe_during_interval(_assert_message_received, probe_interval=0.3, stop_after=5)
