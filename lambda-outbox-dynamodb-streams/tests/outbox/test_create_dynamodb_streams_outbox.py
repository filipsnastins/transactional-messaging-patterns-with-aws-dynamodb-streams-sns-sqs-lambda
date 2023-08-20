from typing import Any

import pytest
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import MotoContainer
from tomodachi_testcontainers.pytest.async_probes import probe_until
from transactional_outbox.dynamodb import DynamoDBOutboxRepository
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_sqs import SQSClient
from unit_of_work.dynamodb import DynamoDBSession

from lambda_outbox_dynamodb_streams.outbox import create_dynamodb_streams_outbox
from lambda_outbox_dynamodb_streams.outbox.create import Settings
from tests.fakes import message_factory

pytestmark = pytest.mark.usefixtures(
    "_environment", "_create_topics_and_queues", "_create_outbox_table", "_reset_moto_container_on_teardown"
)

# Package Lambda as ZIP for changes in Lambda code to take effect


@pytest.mark.asyncio()
async def test_create_dynamodb_streams_outbox(
    moto_container: MotoContainer,
    moto_iam_client: IAMClient,
    moto_lambda_client: LambdaClient,
    moto_dynamodb_client: DynamoDBClient,
    moto_s3_client: S3Client,
    moto_sqs_client: SQSClient,
    session: DynamoDBSession,
    outbox_repository: DynamoDBOutboxRepository,
) -> None:
    message = message_factory()

    await create_dynamodb_streams_outbox(
        moto_lambda_client,
        moto_iam_client,
        moto_dynamodb_client,
        moto_s3_client,
        settings=Settings(
            dynamodb_outbox_table_name="outbox",
            aws_endpoint_url=moto_container.get_internal_url(),
            aws_sns_topic_prefix="autotest-",
        ),
    )
    await outbox_repository.publish([message])
    await session.commit()

    async def _receive_sns_message() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "autotest-test-queue", JsonBase, dict[str, Any])

        assert message == {"message": "test-message"}

    await probe_until(_receive_sns_message, probe_interval=0.3, stop_after=8)
