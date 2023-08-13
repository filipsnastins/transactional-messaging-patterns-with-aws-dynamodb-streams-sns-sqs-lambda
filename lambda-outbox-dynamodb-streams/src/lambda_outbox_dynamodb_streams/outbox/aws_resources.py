import json
from pathlib import Path

from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_iam.type_defs import CreateRoleResponseTypeDef
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_lambda.type_defs import FunctionConfigurationResponseTypeDef
from types_aiobotocore_s3 import S3Client


async def upload_lambda_to_s3(s3_client: S3Client, s3_bucket_name: str, lambda_zip_path: Path) -> str:
    try:
        await s3_client.head_bucket(Bucket=s3_bucket_name)
    except s3_client.exceptions.ClientError:
        await s3_client.create_bucket(Bucket=s3_bucket_name)

    s3_object_key = lambda_zip_path.name
    with open(lambda_zip_path, "rb") as f:
        await s3_client.put_object(Bucket=s3_bucket_name, Key=s3_object_key, Body=f)
    return s3_object_key


async def create_lambda_function(
    lambda_client: LambdaClient,
    function_name: str,
    environment_variables: dict[str, str],
    lambda_role_arn: str,
    s3_bucket_name: str,
    s3_lambda_key: str,
) -> FunctionConfigurationResponseTypeDef:
    return await lambda_client.create_function(
        FunctionName=f"lambda-{function_name}",
        Runtime="python3.10",
        Role=lambda_role_arn,
        Handler="app.lambda_function.lambda_handler",
        Code={"S3Bucket": s3_bucket_name, "S3Key": s3_lambda_key},
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
