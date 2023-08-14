import datetime
import json
import uuid
from typing import Any

import pytest
import pytest_asyncio
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import MotoContainer
from tomodachi_testcontainers.pytest.async_probes import probe_until
from transactional_outbox.repository import PublishedMessage
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

from lambda_outbox_dynamodb_streams.outbox import create_dynamodb_streams_outbox

pytestmark = pytest.mark.usefixtures("_create_topics_and_queues", "_reset_moto_container_on_teardown")

TEST_OUTBOX_TABLE_NAME = "outbox"


@pytest_asyncio.fixture()
async def _create_topics_and_queues(moto_sns_client: SNSClient, moto_sqs_client: SQSClient) -> None:
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="test-topic",
        queue="test-queue",
    )


@pytest.mark.asyncio()
async def test_create_dynamodb_streams_outbox(
    moto_container: MotoContainer,
    moto_iam_client: IAMClient,
    moto_lambda_client: LambdaClient,
    moto_dynamodb_client: DynamoDBClient,
    moto_s3_client: S3Client,
    moto_sqs_client: SQSClient,
) -> None:
    aws_config = moto_container.get_aws_client_config()
    message = PublishedMessage(
        message_id=uuid.uuid4(),
        aggregate_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        topic="test-topic",
        message=json.dumps({"message": "test-message"}),
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
        is_dispatched=False,
        dispatched_at=None,
    )

    await create_dynamodb_streams_outbox(
        moto_lambda_client,
        moto_iam_client,
        moto_dynamodb_client,
        moto_s3_client,
        environment_variables={
            "AWS_REGION": aws_config["region_name"],
            "AWS_ENDPOINT_URL": moto_container.get_internal_url(),
            "DYNAMODB_OUTBOX_TABLE_NAME": TEST_OUTBOX_TABLE_NAME,
        },
        dynamodb_table_name=TEST_OUTBOX_TABLE_NAME,
    )

    await moto_dynamodb_client.put_item(
        TableName=TEST_OUTBOX_TABLE_NAME,
        Item={
            "PK": {"S": f"MESSAGE#{message.message_id}"},
            "MessageId": {"S": str(message.message_id)},
            "AggregateId": {"S": str(message.aggregate_id)},
            "CorrelationId": {"S": str(message.correlation_id)},
            "Topic": {"S": message.topic},
            "Message": {"S": message.message},
            "CreatedAt": {"S": message.created_at.isoformat()},
        },
    )

    async def _receive_sns_message() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "test-queue", JsonBase, dict[str, Any])

        assert message == {"message": "test-message"}

    await probe_until(_receive_sns_message, stop_after=8)