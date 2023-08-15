from typing import AsyncGenerator

import pytest
import pytest_asyncio
from tomodachi_testcontainers.containers import MotoContainer

from adapters import dynamodb, inbox, outbox
from service_layer.unit_of_work import DynamoDBUnitOfWork, UnitOfWork


@pytest.fixture()
def _environment(monkeypatch: pytest.MonkeyPatch, moto_container: MotoContainer) -> None:
    aws_config = moto_container.get_aws_client_config()
    monkeypatch.setenv("ENVIRONMENT", "autotest")
    monkeypatch.setenv("AWS_REGION", aws_config["region_name"])
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", aws_config["aws_access_key_id"])
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", aws_config["aws_secret_access_key"])
    monkeypatch.setenv("AWS_ENDPOINT_URL", aws_config["endpoint_url"])
    monkeypatch.setenv("DYNAMODB_CUSTOMERS_TABLE_NAME", "customers")
    monkeypatch.setenv("DYNAMODB_INBOX_TABLE_NAME", "customers-inbox")
    monkeypatch.setenv("DYNAMODB_OUTBOX_TABLE_NAME", "customers-outbox")


@pytest_asyncio.fixture()
async def _mock_dynamodb(_environment: None, _reset_moto_container_on_teardown: None) -> None:
    await dynamodb.create_customers_table()
    await inbox.create_inbox_table()
    await outbox.create_outbox_table()


@pytest_asyncio.fixture()
async def uow() -> AsyncGenerator[UnitOfWork, None]:
    async with DynamoDBUnitOfWork() as uow:
        yield uow
