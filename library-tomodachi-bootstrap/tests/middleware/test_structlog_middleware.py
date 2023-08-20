import uuid

import pytest
import structlog

from tomodachi_bootstrap import structlog_middleware


@pytest.mark.asyncio()
async def test_bind_passed_correlation_id_kwarg_to_structlog() -> None:
    correlation_id = uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")

    async def _handler(correlation_id: uuid.UUID) -> None:
        assert isinstance(correlation_id, uuid.UUID)
        assert correlation_id == uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")

    await structlog_middleware(_handler, correlation_id=correlation_id)

    context = structlog.contextvars.get_contextvars()
    assert context == {"correlation_id": correlation_id}


@pytest.mark.asyncio()
async def test_generate_new_correlation_id_if_kwarg_not_set() -> None:
    async def _handler() -> None:
        return None

    await structlog_middleware(_handler)

    context = structlog.contextvars.get_contextvars()
    assert isinstance(context["correlation_id"], uuid.UUID)


@pytest.mark.asyncio()
async def test_old_structlog_contextvars_cleared() -> None:
    structlog.contextvars.bind_contextvars(foo="bar")

    async def _handler() -> None:
        return None

    await structlog_middleware(_handler)

    context = structlog.contextvars.get_contextvars()
    assert context.keys() == {"correlation_id"}


@pytest.mark.asyncio()
async def test_function_arguments_forwarded() -> None:
    async def _handler(arg_1: str, kwarg_2: str = "") -> None:
        assert arg_1 == "arg_1"
        assert kwarg_2 == "kwarg_2"

    await structlog_middleware(_handler, "arg_1", kwarg_2="kwarg_2")


@pytest.mark.asyncio()
async def test_function_return_value_forwarded() -> None:
    async def _handler() -> str:
        return "return_value"

    response = await structlog_middleware(_handler)

    assert response == "return_value"
