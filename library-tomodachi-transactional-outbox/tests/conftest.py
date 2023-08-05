from typing import AsyncGenerator

import pytest_asyncio
from aiobotocore.session import get_session
from tomodachi_testcontainers.containers import LocalStackContainer
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient


@pytest_asyncio.fixture()
async def localstack_iam_client(localstack_container: LocalStackContainer) -> AsyncGenerator[IAMClient, None]:
    async with get_session().create_client("iam", **localstack_container.get_aws_client_config()) as c:
        yield c


@pytest_asyncio.fixture()
async def localstack_lambda_client(localstack_container: LocalStackContainer) -> AsyncGenerator[LambdaClient, None]:
    async with get_session().create_client("lambda", **localstack_container.get_aws_client_config()) as c:
        yield c
