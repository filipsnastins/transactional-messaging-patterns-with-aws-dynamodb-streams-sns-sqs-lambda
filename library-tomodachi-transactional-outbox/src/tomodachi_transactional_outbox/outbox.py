from pathlib import Path

from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient

from tomodachi_transactional_outbox.aws.resources import (
    add_dynamodb_stream_on_lambda,
    create_lambda_dynamodb_streams_role,
    create_lambda_function,
)

__all__ = [
    "create_dynamodb_streams_outbox",
]


async def create_dynamodb_streams_outbox(
    lambda_client: LambdaClient,
    iam_client: IAMClient,
    dynamodb_client: DynamoDBClient,
    environment_variables: dict[str, str],
    dynamodb_table_name: str,
    lambda_path: Path,
) -> None:
    create_role_response = await create_lambda_dynamodb_streams_role(
        iam_client, dynamodb_client, dynamodb_table_name=dynamodb_table_name
    )
    lambda_role_arn = create_role_response["Role"]["Arn"]

    create_lambda_function_response = await create_lambda_function(
        lambda_client,
        function_name=f"dynamodb-streams--{dynamodb_table_name}",
        environment_variables=environment_variables,
        lambda_role_arn=lambda_role_arn,
        lambda_path=lambda_path,
    )
    function_name = create_lambda_function_response["FunctionName"]

    await add_dynamodb_stream_on_lambda(
        lambda_client, dynamodb_client, dynamodb_table_name=dynamodb_table_name, function_name=function_name
    )
