import pytest
import pytest_asyncio
from aiobotocore.session import get_session
from tomodachi_testcontainers.containers import MotoContainer
from types_aiobotocore_dynamodb import DynamoDBClient

from unit_of_work.dynamodb import DynamoDBClientFactory


@pytest.fixture()
def client_factory(moto_container: MotoContainer) -> DynamoDBClientFactory:
    return lambda: get_session().create_client("dynamodb", **moto_container.get_aws_client_config())


@pytest_asyncio.fixture()
async def _create_dynamodb_table(moto_dynamodb_client: DynamoDBClient) -> None:
    await moto_dynamodb_client.create_table(
        TableName="test-table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )
