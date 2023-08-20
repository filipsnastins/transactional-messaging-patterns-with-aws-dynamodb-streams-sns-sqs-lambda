import uuid
from unittest.mock import Mock

import pytest
from aiohttp import web
from structlog.testing import capture_logs

from tomodachi_bootstrap.middleware import http_correlation_id_middleware


@pytest.mark.asyncio()
async def test_correlation_id_fetched_from_request_header() -> None:
    service = Mock()
    request = Mock(headers={"X-Correlation-Id": "430d1506-5e9c-467d-a303-751d2ddee79d"})

    async def _request_handler(correlation_id: uuid.UUID) -> web.Response:
        assert isinstance(correlation_id, uuid.UUID)
        assert correlation_id == uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")
        return web.Response()

    await http_correlation_id_middleware(_request_handler, service, request)


@pytest.mark.asyncio()
async def test_correlation_id_set_to_web_response_object() -> None:
    service = Mock()
    request = Mock(headers={"X-Correlation-Id": "430d1506-5e9c-467d-a303-751d2ddee79d"})

    async def _request_handler(correlation_id: uuid.UUID) -> web.Response:
        return web.Response()

    response = await http_correlation_id_middleware(_request_handler, service, request)

    assert response.headers["X-Correlation-Id"] == "430d1506-5e9c-467d-a303-751d2ddee79d"


@pytest.mark.asyncio()
async def test_new_correlation_id_generated_if_X_Correlation_Id_header_not_set_in_request() -> None:
    service = Mock()
    request = Mock(headers={})

    async def _request_handler(correlation_id: uuid.UUID) -> web.Response:
        return web.Response()

    response = await http_correlation_id_middleware(_request_handler, service, request)

    assert uuid.UUID(response.headers["X-Correlation-Id"])


@pytest.mark.asyncio()
async def test_correlation_id_not_set_if_request_handler_return_type_is_not_web_response_object() -> None:
    service = Mock()
    request = Mock(headers={"X-Correlation-Id": "430d1506-5e9c-467d-a303-751d2ddee79d"})

    async def _request_handler(correlation_id: uuid.UUID) -> dict:
        return {"foo": "bar"}

    with capture_logs() as cap_logs:
        response = await http_correlation_id_middleware(_request_handler, service, request)

    assert response == {"foo": "bar"}
    assert cap_logs == [
        {
            "correlation_id": uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d"),
            "event": (
                "HTTP correlation ID middleware did not receive a Response object;"
                " 'X-Correlation-Id' header will not be set"
            ),
            "log_level": "warning",
        }
    ]


@pytest.mark.asyncio()
async def test_function_arguments_forwarded() -> None:
    service = Mock()
    request = Mock(headers={})

    async def _request_handler(arg_1: str, correlation_id: uuid.UUID, kwarg_2: str = "") -> None:
        assert arg_1 == "arg_1"
        assert isinstance(correlation_id, uuid.UUID)
        assert kwarg_2 == "kwarg_2"

    await http_correlation_id_middleware(_request_handler, service, request, "arg_1", kwarg_2="kwarg_2")


@pytest.mark.asyncio()
async def test_function_return_value_forwarded() -> None:
    service = Mock()
    request = Mock(headers={})

    async def _request_handler(correlation_id: uuid.UUID) -> str:
        return "return_value"

    response = await http_correlation_id_middleware(_request_handler, service, request)

    assert response == "return_value"
