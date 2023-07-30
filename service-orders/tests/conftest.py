from typing import AsyncGenerator, Generator, cast

import httpx
import pytest
import pytest_asyncio
from docker.models.images import Image as DockerImage
from tomodachi_testcontainers.containers import TomodachiContainer
from tomodachi_testcontainers.utils import get_available_port


@pytest.fixture()
def tomodachi_container(tomodachi_image: DockerImage) -> Generator[TomodachiContainer, None, None]:
    with TomodachiContainer(image=str(tomodachi_image.id), edge_port=get_available_port()) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture()
async def http_client(
    tomodachi_container: TomodachiContainer,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=tomodachi_container.get_external_url()) as client:
        yield client
