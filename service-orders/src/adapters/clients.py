from aiobotocore.session import AioSession, get_session
from pydantic import BaseModel
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_iam import IAMClient
from types_aiobotocore_lambda import LambdaClient
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_sns import SNSClient

from adapters.settings import get_settings

session: AioSession = get_session()


class AWSClientConfig(BaseModel):
    region_name: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    endpoint_url: str | None = None

    @staticmethod
    def from_settings() -> "AWSClientConfig":
        settings = get_settings()
        return AWSClientConfig(
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            endpoint_url=settings.aws_endpoint_url,
        )


def get_dynamodb_client() -> DynamoDBClient:
    return session.create_client("dynamodb", **AWSClientConfig.from_settings().model_dump())


def get_iam_client() -> IAMClient:
    return session.create_client("iam", **AWSClientConfig.from_settings().model_dump())


def get_lambda_client() -> LambdaClient:
    return session.create_client("lambda", **AWSClientConfig.from_settings().model_dump())


def get_s3_client() -> S3Client:
    return session.create_client("s3", **AWSClientConfig.from_settings().model_dump())


def get_sns_client() -> SNSClient:
    return session.create_client("sns", **AWSClientConfig.from_settings().model_dump())
