from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None
    dynamodb_outbox_table_name: str


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
