import os

from aiobotocore.session import get_session
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient


def get_dynamodb_client() -> DynamoDBClient:
    return get_session().create_client(
        "dynamodb",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"),
    )


def get_lambda_client() -> LambdaClient:
    return get_session().create_client(
        "lambda",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"),
    )


def get_iam_client() -> IAMClient:
    return get_session().create_client(
        "iam",
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"),
    )
