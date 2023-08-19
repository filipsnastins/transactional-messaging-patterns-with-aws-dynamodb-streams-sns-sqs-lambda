import json
import uuid
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from transactional_outbox.outbox import PublishedMessage
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

from lambda_outbox_dynamodb_streams.app.dispatch import TopicsCache, dispatch_message, envelope_json_message
from lambda_outbox_dynamodb_streams.app.time import utcnow

pytestmark = pytest.mark.usefixtures("_create_topics_and_queues", "_reset_moto_container_on_teardown")


@pytest.mark.asyncio()
async def test_topics_cache__topic_created_on_first_call(moto_sns_client: SNSClient, mocker: MockerFixture) -> None:
    client_spy = mocker.spy(moto_sns_client, "create_topic")
    topics_cache = TopicsCache(topic_name_prefix="autotest-")

    topic_arn = await topics_cache.get_or_create_topic("test-topic", moto_sns_client)

    assert topic_arn == "arn:aws:sns:us-east-1:123456789012:autotest-test-topic"
    assert client_spy.call_args == call(Name="autotest-test-topic")


@pytest.mark.asyncio()
async def test_topics_cache__cache_hit_on_second_call(moto_sns_client: SNSClient, mocker: MockerFixture) -> None:
    topics_cache = TopicsCache(topic_name_prefix="autotest-")
    await topics_cache.get_or_create_topic("test-topic", moto_sns_client)
    client_spy = mocker.spy(moto_sns_client, "create_topic")

    topic_arn = await topics_cache.get_or_create_topic("test-topic", moto_sns_client)

    assert topic_arn == "arn:aws:sns:us-east-1:123456789012:autotest-test-topic"
    assert client_spy.call_count == 0


@pytest.mark.asyncio()
async def test_envelope_json_message() -> None:
    message = PublishedMessage(
        message_id=uuid.uuid4(),
        aggregate_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        topic="test-topic",
        message=json.dumps({"message": "test-message"}),
        created_at=utcnow(),
        is_dispatched=False,
        dispatched_at=None,
    )

    envelope = json.loads(await envelope_json_message(message))

    assert envelope["service"] == {"name": None, "uuid": None}
    assert envelope["metadata"]["topic"] == "test-topic"
    assert envelope["data"] == {"message": "test-message"}


@pytest.mark.asyncio()
async def test_dispatch_message(moto_sns_client: SNSClient, moto_sqs_client: SQSClient) -> None:
    topics_cache = TopicsCache(topic_name_prefix="autotest-")
    message = PublishedMessage(
        message_id=uuid.uuid4(),
        aggregate_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        topic="test-topic",
        message=json.dumps({"message": "test-message"}),
        created_at=utcnow(),
        is_dispatched=False,
        dispatched_at=None,
    )

    await dispatch_message(moto_sns_client, message, envelope_json_message, topics_cache)

    async def _assert_message_received() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "autotest-test-queue", JsonBase, dict[str, str])

        assert message == {"message": "test-message"}

    await probe_until(_assert_message_received, probe_interval=0.3, stop_after=8)
