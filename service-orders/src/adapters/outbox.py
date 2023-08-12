import structlog
from tomodachi_outbox import outbox
from tomodachi_outbox.dynamodb import create_outbox_table as tomodachi_outbox_create_outbox_table

from adapters import clients
from adapters.settings import get_settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def get_outbox_table_name() -> str:
    return get_settings().dynamodb_outbox_table_name


async def create_outbox_table() -> None:
    async with clients.get_dynamodb_client() as client:
        await tomodachi_outbox_create_outbox_table(table_name=get_outbox_table_name(), client=client)


async def create_dynamodb_streams_outbox() -> None:
    settings = get_settings()
    async with (
        clients.get_lambda_client() as lambda_client,
        clients.get_iam_client() as iam_client,
        clients.get_dynamodb_client() as dynamodb_client,
    ):
        dynamodb_table_name = get_outbox_table_name()
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
