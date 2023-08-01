import os

import structlog
from adapters import clients, dynamodb

from tomodachi_transactional_outbox import dynamodb_streams

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_dynamodb_streams_outbox_lambda() -> None:
    environment = os.environ["ENVIRONMENT"]
    dynamodb_table_name = dynamodb.get_outbox_table_name()
    async with (
        clients.get_lambda_client() as lambda_client,
        clients.get_iam_client() as iam_client,
        clients.get_dynamodb_client() as dynamodb_client,
    ):
        await dynamodb_streams.create_outbox_lambda(
            lambda_client,
            iam_client,
            dynamodb_client,
            environment=environment,
            dynamodb_table_name=dynamodb_table_name,
        )
    logger.info(
        "dynamodb_streams_outbox_lambda_created",
        environment=environment,
        dynamodb_table_name=dynamodb_table_name,
    )
