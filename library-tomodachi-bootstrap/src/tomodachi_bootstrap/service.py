import tomodachi
from pydantic_settings import BaseSettings


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
        return self.environment in ["development", "autotest"]


class TomodachiServiceBase(tomodachi.Service):
    def __init__(self) -> None:
        settings = TomodachiBaseSettings()  # type: ignore
        self.is_dev_env = settings.is_dev_env
        self.options = tomodachi.Options(
            aws_endpoint_urls=tomodachi.Options.AWSEndpointURLs(
                sns=settings.aws_endpoint_url,
                sqs=settings.aws_endpoint_url,
            ),
            aws_sns_sqs=tomodachi.Options.AWSSNSSQS(
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                topic_prefix=settings.aws_sns_topic_prefix,
                queue_name_prefix=settings.aws_sqs_queue_name_prefix,
            ),
        )
