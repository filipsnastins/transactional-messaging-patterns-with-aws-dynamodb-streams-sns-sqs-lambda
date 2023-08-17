import os
from functools import lru_cache
from typing import Protocol


class SettingsType(Protocol):
    dynamodb_outbox_table_name: str
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None


class Settings(SettingsType):
    dynamodb_outbox_table_name: str
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None

    def __init__(self) -> None:
        self.dynamodb_outbox_table_name = os.environ["DYNAMODB_OUTBOX_TABLE_NAME"]
        self.aws_region = os.environ["AWS_REGION"]
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
