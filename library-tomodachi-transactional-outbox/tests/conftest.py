from typing import AsyncGenerator

import pytest_asyncio
from aiobotocore.session import get_session
from tomodachi_testcontainers.containers import MotoContainer
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient


@pytest_asyncio.fixture()
async def moto_iam_client(moto_container: MotoContainer) -> AsyncGenerator[IAMClient, None]:
    async with get_session().create_client("iam", **moto_container.get_aws_client_config()) as c:
        yield c


@pytest_asyncio.fixture()
async def moto_lambda_client(moto_container: MotoContainer) -> AsyncGenerator[LambdaClient, None]:
    async with get_session().create_client("lambda", **moto_container.get_aws_client_config()) as c:
        yield c
