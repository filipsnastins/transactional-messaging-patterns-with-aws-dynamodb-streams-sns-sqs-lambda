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
        topic="incoming-topic",
        queue="incoming-queue",
    )
    await snssqs_client.subscribe_to(
        moto_sns_client,
        moto_sqs_client,
        topic="outgoing-topic",
        queue="outgoing-queue",
    )


@pytest.fixture()
def tomodachi_container(
    tomodachi_image: DockerImage,
    moto_container: MotoContainer,
    _create_topics_and_queues: None,
    _reset_moto_container_on_teardown: None,
) -> Generator[TomodachiContainer, None, None]:
    with (
        TomodachiContainer(image=str(tomodachi_image.id), edge_port=get_available_port())
        .with_env("ENVIRONMENT", "production")
        .with_env("AWS_REGION", "us-east-1")
        .with_env("AWS_ACCESS_KEY_ID", "testing")
        .with_env("AWS_SECRET_ACCESS_KEY", "testing")
        .with_env("AWS_ENDPOINT_URL", moto_container.get_internal_url())
    ) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture()
async def http_client(tomodachi_container: TomodachiContainer) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=tomodachi_container.get_external_url()) as client:
        yield client
