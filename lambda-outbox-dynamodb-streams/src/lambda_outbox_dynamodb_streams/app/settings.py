from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dynamodb_outbox_table_name: str
    aws_endpoint_url: str | None = None
    aws_sns_topic_prefix: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
