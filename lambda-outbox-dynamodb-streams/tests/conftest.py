import pytest
import pytest_asyncio
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import MotoContainer
from transactional_outbox.dynamodb import DynamoDBOutboxRepository, create_outbox_table
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient
from unit_of_work.dynamodb import DynamoDBSession

from lambda_outbox_dynamodb_streams.app import clients
from lambda_outbox_dynamodb_streams.app.settings import get_settings
from tests.fakes import SampleMessage


@pytest.fixture()
def _environment(monkeypatch: pytest.MonkeyPatch, moto_container: MotoContainer) -> None:
    aws_config = moto_container.get_aws_client_config()
    monkeypatch.setenv("ENVIRONMENT", "autotest")
    monkeypatch.setenv("AWS_REGION", aws_config["region_name"])
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", aws_config["aws_access_key_id"])
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", aws_config["aws_secret_access_key"])
    monkeypatch.setenv("AWS_ENDPOINT_URL", aws_config["endpoint_url"])
    monkeypatch.setenv("DYNAMODB_OUTBOX_TABLE_NAME", "outbox")


@pytest_asyncio.fixture()
async def _create_outbox_table(
    moto_dynamodb_client: DynamoDBClient, _environment: None, _reset_moto_container_on_teardown: None
) -> None:
    await create_outbox_table(table_name="outbox", client=moto_dynamodb_client)


@pytest_asyncio.fixture()
async def _create_topics_and_queues(moto_sns_client: SNSClient, moto_sqs_client: SQSClient) -> None:
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="test-topic",
        queue="test-queue",
    )


@pytest.fixture()
def session() -> DynamoDBSession:
    return DynamoDBSession(clients.get_dynamodb_client)


@pytest.fixture()
def outbox_repository(session: DynamoDBSession) -> DynamoDBOutboxRepository:
    dynamodb_table_name = get_settings().dynamodb_outbox_table_name
    topic_map = {SampleMessage: "test-topic"}
    return DynamoDBOutboxRepository(dynamodb_table_name, session, topic_map)
