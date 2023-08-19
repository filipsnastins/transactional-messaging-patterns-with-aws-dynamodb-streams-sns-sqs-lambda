import uuid
from typing import Any, Callable

import structlog
from aiohttp import web
from tomodachi.transport.aws_sns_sqs import AWSSNSSQSInternalServiceError


async def message_retry_middleware(func: Callable, *args: Any, **kwargs: Any) -> Any:
    try:
        return await func(*args, **kwargs)
    except Exception as exc:
        raise AWSSNSSQSInternalServiceError from exc


async def http_correlation_id_middleware(
    func: Callable, service: Any, request: web.Request, *args: Any, **kwargs: Any
) -> Any:
    correlation_id = request.headers.get("X-Correlation-Id", uuid.uuid4())
    if not isinstance(correlation_id, uuid.UUID):
        correlation_id = uuid.UUID(correlation_id)

    return await func(*args, **kwargs, correlation_id=correlation_id)


async def message_correlation_id_middleware(func: Callable, *args: Any, **kwargs: Any) -> Any:
    correlation_id = kwargs.get("message", {}).get("data", {}).get("correlation_id", uuid.uuid4())
    if not isinstance(correlation_id, uuid.UUID):
        correlation_id = uuid.UUID(correlation_id)

    return await func(*args, **kwargs, correlation_id=correlation_id)


async def structlog_logger_middleware(func: Callable, *args: Any, **kwargs: Any) -> Any:
    correlation_id = kwargs.get("correlation_id", uuid.uuid4())
    if not isinstance(correlation_id, uuid.UUID):
        correlation_id = uuid.UUID(correlation_id)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=str(correlation_id))

    return await func(*args, **kwargs)
