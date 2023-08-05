import json
from pathlib import Path

from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_iam.type_defs import CreateRoleResponseTypeDef
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_lambda.type_defs import FunctionConfigurationResponseTypeDef

from tomodachi_transactional_outbox.aws.utils import package_lambda_as_zip


async def create_lambda_function(
    lambda_client: LambdaClient,
    function_name: str,
    environment_variables: dict[str, str],
    lambda_role_arn: str,
    lambda_path: Path,
) -> FunctionConfigurationResponseTypeDef:
    code = package_lambda_as_zip(lambda_path)
    return await lambda_client.create_function(
        FunctionName=f"lambda-{function_name}",
        Runtime="python3.10",
        Role=lambda_role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": code.read()},
        Publish=True,
        Timeout=30,
        MemorySize=256,
        Environment={"Variables": environment_variables},
    )


async def create_lambda_dynamodb_streams_role(
    iam_client: IAMClient, dynamodb_client: DynamoDBClient, dynamodb_table_name: str
) -> CreateRoleResponseTypeDef:
    describe_table_response = await dynamodb_client.describe_table(TableName=dynamodb_table_name)
    table_arn = describe_table_response["Table"]["TableArn"]
    return await iam_client.create_role(
        RoleName=f"role-lambda-dynamodb-streams--{dynamodb_table_name}",
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
    get_function_response = await lambda_client.get_function(FunctionName=function_name)
    function_arn = get_function_response["Configuration"]["FunctionArn"]

    describe_table_response = await dynamodb_client.describe_table(TableName=dynamodb_table_name)
    event_source_arn = describe_table_response["Table"]["LatestStreamArn"]

    await lambda_client.create_event_source_mapping(
        FunctionName=function_arn,
        EventSourceArn=event_source_arn,
        Enabled=True,
        StartingPosition="LATEST",
    )
