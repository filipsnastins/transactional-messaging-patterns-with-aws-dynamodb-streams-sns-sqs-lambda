from dataclasses import dataclass

from aiobotocore.session import AioSession, get_session
from types_aiobotocore_dynamodb import DynamoDBClient
from types_aiobotocore_sns import SNSClient

from .settings import get_settings

session: AioSession = get_session()


@dataclass
class AWSClientConfig:
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

    def to_dict(self) -> dict:
        return {
            "region_name": self.region_name,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "endpoint_url": self.endpoint_url,
        }


def get_dynamodb_client() -> DynamoDBClient:
    return session.create_client("dynamodb", **AWSClientConfig.from_settings().to_dict())


def get_sns_client() -> SNSClient:
    return session.create_client("sns", **AWSClientConfig.from_settings().to_dict())
