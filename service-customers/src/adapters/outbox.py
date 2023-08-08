import os

import structlog
from tomodachi_outbox import outbox

from adapters import clients, dynamodb
from adapters.settings import get_settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def create_dynamodb_streams_outbox() -> None:
    settings = get_settings()
    async with (
        clients.get_lambda_client() as lambda_client,
        clients.get_iam_client() as iam_client,
        clients.get_dynamodb_client() as dynamodb_client,
    ):
        dynamodb_table_name = dynamodb.get_outbox_table_name()
        await outbox.create_dynamodb_streams_outbox(
            lambda_client,
            iam_client,
            dynamodb_client,
            environment_variables={
                "AWS_REGION": settings.aws_region,
                "AWS_ENDPOINT_URL": settings.aws_endpoint_url or "",
                "DYNAMODB_OUTBOX_TABLE_NAME": dynamodb_table_name,
            },
            dynamodb_table_name=dynamodb_table_name,
        )

        logger.info("dynamodb_streams_outbox_created", dynamodb_table_name=dynamodb_table_name)
