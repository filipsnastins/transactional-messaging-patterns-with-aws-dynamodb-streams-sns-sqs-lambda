from functools import lru_cache

from pydantic_settings import BaseSettings

DEV_ENVIRONMENTS = ["development", "autotest"]


class TomodachiBaseSettings(BaseSettings):
    environment: str
    aws_region: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None
    aws_sns_topic_prefix: str = ""
    aws_sqs_queue_name_prefix: str = ""

    @property
    def is_dev_env(self) -> bool:
        return self.environment in DEV_ENVIRONMENTS


@lru_cache
def get_settings() -> TomodachiBaseSettings:
    return TomodachiBaseSettings()  # type: ignore
