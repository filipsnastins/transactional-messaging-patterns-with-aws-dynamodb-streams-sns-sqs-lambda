from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None
    aws_sns_topic_prefix: str = ""
    aws_sqs_queue_name_prefix: str = ""
    dynamodb_aggregate_table_name: str
    dynamodb_outbox_table_name: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
