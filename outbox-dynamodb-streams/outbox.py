import json
from pathlib import Path

from outbox.utils import create_in_memory_zip
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_iam.type_defs import CreateRoleResponseTypeDef
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_lambda.type_defs import FunctionConfigurationResponseMetadataTypeDef

__all__ = [
    "create_ddb_streams_outbox_lambda",
]

DEFAULT_LAMBDA_PATH = Path(__file__).parent / "lambda"


async def create_ddb_streams_outbox_lambda(
    lambda_client: LambdaClient,
    iam_client: IAMClient,
    dynamodb_client: DynamoDBClient,
    environment: str,
    dynamodb_table_name: str,
    lambda_path: Path = DEFAULT_LAMBDA_PATH,
) -> None:
    create_role_response = await create_lambda_dynamodb_streams_outbox_role(
        iam_client, dynamodb_client, environment=environment, dynamodb_table_name=dynamodb_table_name
    )
    lambda_role_arn = create_role_response["Role"]["Arn"]

    create_lambda_function_response = await create_lambda_function(
        lambda_client,
        environment=environment,
        lambda_role_arn=lambda_role_arn,
        dynamodb_table_name=dynamodb_table_name,
        lambda_path=lambda_path,
    )
    function_name = create_lambda_function_response["FunctionName"]

    await add_dynamodb_stream_on_lambda(
        lambda_client, dynamodb_client, dynamodb_table_name=dynamodb_table_name, function_name=function_name
    )


async def create_lambda_function(
    lambda_client: LambdaClient, environment: str, lambda_role_arn: str, dynamodb_table_name: str, lambda_path: Path
) -> FunctionConfigurationResponseMetadataTypeDef:
    code = create_in_memory_zip(lambda_path)
    return await lambda_client.create_function(
        FunctionName=f"{environment}-lambda-dynamodb-streams-outbox-{dynamodb_table_name}",
        Runtime="python3.10",
        Role=lambda_role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": code.read()},
        Publish=True,
        Timeout=30,
        MemorySize=256,
        Environment={},
    )


async def create_lambda_dynamodb_streams_outbox_role(
    iam_client: IAMClient, dynamodb_client: DynamoDBClient, environment: str, dynamodb_table_name: str
) -> CreateRoleResponseTypeDef:
    describe_table_response = await dynamodb_client.describe_table(TableName=dynamodb_table_name)
    table_arn = describe_table_response["Table"]["TableArn"]
    return await iam_client.create_role(
        RoleName=f"{environment}-role-lambda-dynamodb-streams-outbox-{dynamodb_table_name}",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                        "Resource": "*",
                        "Effect": "Allow",
                    },
                    {
                        "Action": "dynamodb:ListStreams",
                        "Resource": "*",
                        "Effect": "Allow",
                    },
                    {
                        "Action": ["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"],
                        "Resource": table_arn,
                        "Effect": "Allow",
                    },
                ],
            }
        ),
    )


async def add_dynamodb_stream_on_lambda(
    lambda_client: LambdaClient, dynamodb_client: DynamoDBClient, dynamodb_table_name: str, function_name: str
) -> None:
    describe_table_response = await dynamodb_client.describe_table(TableName=dynamodb_table_name)
    event_source_arn = describe_table_response["Table"]["LatestStreamArn"]
    get_function_response = await lambda_client.get_function(FunctionName=function_name)
    function_arn = get_function_response["Configuration"]["FunctionArn"]
    await lambda_client.create_event_source_mapping(
        EventSourceArn=event_source_arn,
        FunctionName=function_arn,
        Enabled=True,
    )
