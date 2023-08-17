from dataclasses import dataclass

import structlog
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_s3 import S3Client

from lambda_outbox_dynamodb_streams import LAMBDA_OUTBOX_DYNAMODB_STREAMS_ZIP_PATH
from lambda_outbox_dynamodb_streams.app.settings import SettingsType
from lambda_outbox_dynamodb_streams.outbox.aws_resources import (
    add_dynamodb_stream_on_lambda,
    create_lambda_dynamodb_streams_role,
    create_lambda_function,
    upload_lambda_to_s3,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


@dataclass
class Settings(SettingsType):
    dynamodb_outbox_table_name: str
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None


async def create_dynamodb_streams_outbox(
    lambda_client: LambdaClient,
    iam_client: IAMClient,
    dynamodb_client: DynamoDBClient,
    s3_client: S3Client,
    settings: Settings,
    skip_mark_messages_as_dispatched: bool = True,
) -> None:
    dynamodb_table_name = settings.dynamodb_outbox_table_name

    create_role_response = await create_lambda_dynamodb_streams_role(
        iam_client, dynamodb_client, dynamodb_table_name=dynamodb_table_name
    )
    lambda_role_arn = create_role_response["Role"]["Arn"]

    s3_bucket_name = f"dynamodb-streams--{dynamodb_table_name}"
    s3_lambda_key = await upload_lambda_to_s3(
        s3_client, s3_bucket_name=s3_bucket_name, lambda_zip_path=LAMBDA_OUTBOX_DYNAMODB_STREAMS_ZIP_PATH
    )

    environment_variables = {
        "AWS_REGION": settings.aws_region,
        "DYNAMODB_OUTBOX_TABLE_NAME": dynamodb_table_name,
    }
    if skip_mark_messages_as_dispatched:
        environment_variables["OUTBOX_SKIP_MARK_MESSAGES_AS_DISPATCHED"] = "1"
    if settings.aws_access_key_id:
        environment_variables["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        environment_variables["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
    if settings.aws_endpoint_url:
        environment_variables["AWS_ENDPOINT_URL"] = settings.aws_endpoint_url

    create_lambda_function_response = await create_lambda_function(
        lambda_client,
        function_name=f"dynamodb-streams--{dynamodb_table_name}",
        environment_variables=environment_variables,
        lambda_role_arn=lambda_role_arn,
        handler="app.lambda_function.lambda_handler",
        s3_bucket_name=s3_bucket_name,
        s3_lambda_key=s3_lambda_key,
    )
    function_name = create_lambda_function_response["FunctionName"]

    await add_dynamodb_stream_on_lambda(
        lambda_client,
        dynamodb_client,
        dynamodb_table_name=dynamodb_table_name,
        function_name=function_name,
    )

    waiter = lambda_client.get_waiter("function_active_v2")
    await waiter.wait(FunctionName=function_name)

    logger.info(
        "dynamodb_streams_outbox_created",
        function_name=function_name,
        dynamodb_table_name=dynamodb_table_name,
    )
