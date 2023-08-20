import pytest
from tomodachi.transport.aws_sns_sqs import AWSSNSSQSInternalServiceError

from tomodachi_bootstrap.middleware import sns_sqs_message_retry_middleware


@pytest.mark.asyncio()
async def test_unhandled_exception_converted_to_AWSSNSSQSInternalServiceError() -> None:
    async def _raising_handler() -> None:
        raise RuntimeError("Something went wrong")

    with pytest.raises(AWSSNSSQSInternalServiceError):
        await sns_sqs_message_retry_middleware(_raising_handler)


@pytest.mark.asyncio()
async def test_do_nothing_if_no_exception() -> None:
    async def _passing_handler() -> None:
        return None

    await sns_sqs_message_retry_middleware(_passing_handler)


@pytest.mark.asyncio()
async def test_function_arguments_forwarded() -> None:
    async def _passing_handler(arg_1: str, kwarg_2: str = "") -> None:
        assert arg_1 == "arg_1"
        assert kwarg_2 == "kwarg_2"

    await sns_sqs_message_retry_middleware(_passing_handler, "arg_1", kwarg_2="kwarg_2")


@pytest.mark.asyncio()
async def test_function_return_value_forwarded() -> None:
    async def _passing_handler() -> str:
        return "return_value"

    response = await sns_sqs_message_retry_middleware(_passing_handler)

    assert response == "return_value"
