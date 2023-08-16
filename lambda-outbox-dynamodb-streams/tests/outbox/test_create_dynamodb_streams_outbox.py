import json
import uuid
from typing import Any

import pytest
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import MotoContainer
from tomodachi_testcontainers.pytest.async_probes import probe_until
from transactional_outbox.outbox import PublishedMessage
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_sqs import SQSClient

from lambda_outbox_dynamodb_streams.app.time import utcnow
from lambda_outbox_dynamodb_streams.outbox import create_dynamodb_streams_outbox

pytestmark = pytest.mark.usefixtures("_create_topics_and_queues", "_reset_moto_container_on_teardown")

TEST_OUTBOX_TABLE_NAME = "outbox"


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
        created_at=utcnow(),
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
            "AWS_ACCESS_KEY_ID": aws_config["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": aws_config["aws_secret_access_key"],
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

    await probe_until(_receive_sns_message, probe_interval=0.3, stop_after=8)

    # FIXME: Moto doesn't work well when the item from the same table is updated -
    # Lambda functions end up in an infinite loop

    # item = await moto_dynamodb_client.get_item(
    #     TableName=TEST_OUTBOX_TABLE_NAME, Key={"PK": {"S": f"MESSAGE#{message.message_id}"}}
    # )
    # assert item["Item"]
    # assert item["Item"]["IsDispatched"]["BOOL"] is True
    # assert item["Item"]["DispatchedAt"]["S"]
