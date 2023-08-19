from aiobotocore.session import AioSession, get_session
from pydantic import BaseModel
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_sns import SNSClient

from .settings import get_settings

session: AioSession = get_session()


class AWSClientConfig(BaseModel):
    endpoint_url: str | None = None

    @staticmethod
    def create() -> "AWSClientConfig":
        settings = get_settings()
        return AWSClientConfig(endpoint_url=settings.aws_endpoint_url)


def get_dynamodb_client() -> DynamoDBClient:
    return session.create_client("dynamodb", **AWSClientConfig.create().model_dump())


def get_sns_client() -> SNSClient:
    return session.create_client("sns", **AWSClientConfig.create().model_dump())
