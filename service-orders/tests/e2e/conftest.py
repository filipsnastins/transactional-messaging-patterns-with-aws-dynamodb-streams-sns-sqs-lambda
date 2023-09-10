from typing import AsyncGenerator, Generator, cast

import httpx
import pytest
import pytest_asyncio
from docker.models.images import Image as DockerImage
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import MotoContainer, TomodachiContainer
from tomodachi_testcontainers.utils import get_available_port
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient


@pytest_asyncio.fixture()
async def _create_topics_and_queues(moto_sns_client: SNSClient, moto_sqs_client: SQSClient) -> None:
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="order--created",
        queue="order--created",
    )
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="order--approved",
        queue="order--approved",
    )
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="order--rejected",
        queue="order--rejected",
    )
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="order--cancelled",
        queue="order--cancelled",
    )


@pytest.fixture()
def tomodachi_container(
    tomodachi_image: DockerImage,
    moto_container: MotoContainer,
    _create_topics_and_queues: None,
    _reset_moto_container_on_teardown: None,
) -> Generator[TomodachiContainer, None, None]:
    aws_config = moto_container.get_aws_client_config()
    with (
        TomodachiContainer(
            image=str(tomodachi_image.id),
            edge_port=get_available_port(),
            http_healthcheck_path="/orders/health",
        )
        .with_env("ENVIRONMENT", "autotest")
        .with_env("AWS_REGION", aws_config["region_name"])
        .with_env("AWS_ACCESS_KEY_ID", aws_config["aws_access_key_id"])
        .with_env("AWS_SECRET_ACCESS_KEY", aws_config["aws_secret_access_key"])
        .with_env("AWS_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("DYNAMODB_ORDERS_TABLE_NAME", "orders")
        .with_env("DYNAMODB_INBOX_TABLE_NAME", "orders-inbox")
        .with_env("DYNAMODB_OUTBOX_TABLE_NAME", "orders-outbox")
    ) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture()
async def http_client(tomodachi_container: TomodachiContainer) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=tomodachi_container.get_external_url(),
        transport=httpx.AsyncHTTPTransport(retries=3),
        timeout=10.0,
    ) as client:
        yield client
