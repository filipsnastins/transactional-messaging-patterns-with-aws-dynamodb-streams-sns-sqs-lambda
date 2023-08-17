import pytest
import pytest_asyncio
from aiobotocore.session import get_session
from tomodachi_testcontainers.containers import MotoContainer
from types_aiobotocore_dynamodb import DynamoDBClient
from unit_of_work.dynamodb import DynamoDBClientFactory, DynamoDBSession

from transactional_outbox.dynamodb import create_inbox_table, create_outbox_table


@pytest.fixture()
def client_factory(moto_container: MotoContainer) -> DynamoDBClientFactory:
    return lambda: get_session().create_client("dynamodb", **moto_container.get_aws_client_config())


@pytest_asyncio.fixture()
async def _create_outbox_table(moto_dynamodb_client: DynamoDBClient) -> None:
    await create_outbox_table(table_name="orders-outbox", client=moto_dynamodb_client)


@pytest_asyncio.fixture()
async def _create_inbox_table(moto_dynamodb_client: DynamoDBClient) -> None:
    await create_inbox_table(table_name="orders-inbox", client=moto_dynamodb_client)


@pytest.fixture()
def session(client_factory: DynamoDBClientFactory) -> DynamoDBSession:
    return DynamoDBSession(client_factory)
