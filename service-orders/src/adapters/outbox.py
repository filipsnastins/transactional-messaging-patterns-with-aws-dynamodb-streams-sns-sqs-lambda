from lambda_outbox_dynamodb_streams import outbox
from transactional_outbox.dynamodb import create_outbox_table as transactional_outbox_create_outbox_table

from adapters import clients
from adapters.settings import get_settings


def get_outbox_table_name() -> str:
    return get_settings().dynamodb_outbox_table_name


async def create_outbox_table() -> None:
    async with clients.get_dynamodb_client() as client:
        await transactional_outbox_create_outbox_table(table_name=get_outbox_table_name(), client=client)


async def create_dynamodb_streams_outbox() -> None:
    settings = get_settings()
    async with (
        clients.get_lambda_client() as lambda_client,
        clients.get_iam_client() as iam_client,
        clients.get_dynamodb_client() as dynamodb_client,
        clients.get_s3_client() as s3_client,
    ):
        dynamodb_table_name = get_outbox_table_name()
        await outbox.create_dynamodb_streams_outbox(
            lambda_client,
            iam_client,
            dynamodb_client,
            s3_client,
            settings=outbox.Settings(
                dynamodb_outbox_table_name=dynamodb_table_name,
                aws_endpoint_url=settings.aws_endpoint_url,
                aws_sns_topic_prefix=settings.aws_sns_topic_prefix,
            ),
        )
