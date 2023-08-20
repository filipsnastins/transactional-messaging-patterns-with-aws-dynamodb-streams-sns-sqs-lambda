import pytest
from pydantic import ValidationError

from tomodachi_bootstrap import TomodachiServiceBase


def test_mandatory_envvars_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)

    with pytest.raises(ValidationError):
        TomodachiServiceBase()


def test_tomodachi_options_set_from_envvars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "aws_access_key_id")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secrete_access_key")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setenv("AWS_SNS_TOPIC_PREFIX", "sns-prefix-")
    monkeypatch.setenv("AWS_SQS_QUEUE_NAME_PREFIX", "sqs-prefix-")

    service = TomodachiServiceBase()

    assert service.options.aws_sns_sqs.region_name == "us-east-1"
    assert service.options.aws_sns_sqs.aws_access_key_id == "aws_access_key_id"
    assert service.options.aws_sns_sqs.aws_secret_access_key == "aws_secrete_access_key"
    assert service.options.aws_endpoint_urls.sns == "http://localhost:4566"
    assert service.options.aws_endpoint_urls.sqs == "http://localhost:4566"
    assert service.options.aws_sns_sqs.topic_prefix == "sns-prefix-"
    assert service.options.aws_sns_sqs.queue_name_prefix == "sqs-prefix-"


def test_tomodachi_option_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    service = TomodachiServiceBase()

    assert service.options.aws_sns_sqs.region_name == "us-east-1"
    assert service.options.aws_sns_sqs.aws_access_key_id is None
    assert service.options.aws_sns_sqs.aws_secret_access_key is None
    assert service.options.aws_endpoint_urls.sns is None
    assert service.options.aws_endpoint_urls.sqs is None
    assert service.options.aws_sns_sqs.topic_prefix == ""
    assert service.options.aws_sns_sqs.queue_name_prefix == ""


@pytest.mark.parametrize("environment", ["development", "autotest"])
def test_is_dev_env(monkeypatch: pytest.MonkeyPatch, environment: str) -> None:
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    service = TomodachiServiceBase()

    assert service.is_dev_env is True


def test_is_not_dev_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "any other env name")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    service = TomodachiServiceBase()

    assert service.is_dev_env is False
