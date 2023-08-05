import datetime
import json
import uuid
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import LocalStackContainer
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

from tomodachi_transactional_outbox.message import Message
from tomodachi_transactional_outbox.outbox import create_dynamodb_streams_outbox

pytestmark = pytest.mark.usefixtures("_create_topics_and_queues", "_restart_localstack_container_on_teardown")

TEST_TABLE_NAME = "outbox"
TEST_LAMBDA_PATH = Path(__file__).parent.parent / "lambda"


@pytest_asyncio.fixture()
async def _create_topics_and_queues(localstack_sns_client: SNSClient, localstack_sqs_client: SQSClient) -> None:
    await snssqs_client.subscribe_to(
        localstack_sns_client,
        localstack_sqs_client,
        topic="test-topic",
        queue="test-queue",
    )


@pytest.mark.asyncio()
async def test_create_dynamodb_streams_outbox(
    localstack_container: LocalStackContainer,
    localstack_iam_client: IAMClient,
    localstack_lambda_client: LambdaClient,
    localstack_dynamodb_client: DynamoDBClient,
    localstack_sqs_client: SQSClient,
) -> None:
    message = Message(
        message_id=uuid.uuid4(),
        aggregate_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        topic="test-topic",
        message=json.dumps({"message": "test-message"}),
        created_at=datetime.datetime.utcnow().replace(tzinfo=datetime.UTC),
    )
    await localstack_dynamodb_client.create_table(
        TableName=TEST_TABLE_NAME,
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
        StreamSpecification={"StreamEnabled": True, "StreamViewType": "NEW_AND_OLD_IMAGES"},
    )

    await create_dynamodb_streams_outbox(
        localstack_lambda_client,
        localstack_iam_client,
        localstack_dynamodb_client,
        environment_variables={
            "AWS_REGION": "us-east-1",
            "DYNAMODB_OUTBOX_TABLE_NAME": TEST_TABLE_NAME,
            "AWS_ENDPOINT_URL": localstack_container.get_internal_url(),
        },
        dynamodb_table_name=TEST_TABLE_NAME,
        lambda_path=TEST_LAMBDA_PATH,
    )

    async def _wait_until_lambda_ready() -> None:
        response = await localstack_lambda_client.invoke(
            FunctionName="lambda-dynamodb-streams--outbox", InvocationType="DryRun"
        )

        assert response["StatusCode"] == 204

    await probe_until(_wait_until_lambda_ready)

    await localstack_dynamodb_client.put_item(
        TableName=TEST_TABLE_NAME,
        Item={
            "PK": {"S": f"MESSAGE#{str(message.message_id)}"},
            "MessageId": {"S": str(message.message_id)},
            "AggregateId": {"S": str(message.aggregate_id)},
            "CorrelationId": {"S": str(message.correlation_id)},
            "Topic": {"S": message.topic},
            "Message": {"S": message.message},
            "CreatedAt": {"S": message.created_at.isoformat()},
        },
    )

    async def _receive_sns_message() -> None:
        [message] = await snssqs_client.receive(localstack_sqs_client, "test-queue", JsonBase, dict[str, Any])

        assert message == {"message": "test-message"}

    await probe_until(_receive_sns_message, stop_after=8)
