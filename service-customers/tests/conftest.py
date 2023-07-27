import asyncio
import contextlib
from typing import AsyncGenerator, Generator, Iterator, cast

import httpx
import pytest
import pytest_asyncio
from adapters import dynamodb
from docker.models.images import Image as DockerImage
from tomodachi_testcontainers.containers import MotoContainer, TomodachiContainer
from tomodachi_testcontainers.utils import get_available_port


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    with contextlib.closing(asyncio.new_event_loop()) as loop:
        yield loop


@pytest.fixture()
def tomodachi_container(
    tomodachi_image: DockerImage, moto_container: MotoContainer, _reset_moto_container: None
) -> Generator[TomodachiContainer, None, None]:
    aws_config = moto_container.get_aws_client_config()
    with (
        TomodachiContainer(image=str(tomodachi_image.id), edge_port=get_available_port())
        .with_env("AWS_REGION", aws_config["region_name"])
        .with_env("AWS_ACCESS_KEY_ID", aws_config["aws_access_key_id"])
        .with_env("AWS_SECRET_ACCESS_KEY", aws_config["aws_secret_access_key"])
        .with_env("AWS_DYNAMODB_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("DYNAMODB_TABLE_NAME", "customers")
    ) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture()
async def http_client(
    tomodachi_container: TomodachiContainer,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=tomodachi_container.get_external_url()) as client:
        yield client


@pytest_asyncio.fixture()
async def _mock_dynamodb(
    monkeypatch: pytest.MonkeyPatch, moto_container: MotoContainer, _reset_moto_container: None
) -> None:
    aws_config = moto_container.get_aws_client_config()
    monkeypatch.setenv("AWS_REGION", aws_config["region_name"])
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", aws_config["aws_access_key_id"])
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", aws_config["aws_secret_access_key"])
    monkeypatch.setenv("AWS_DYNAMODB_ENDPOINT_URL", aws_config["endpoint_url"])
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "customers")
    await dynamodb.create_dynamodb_table()
