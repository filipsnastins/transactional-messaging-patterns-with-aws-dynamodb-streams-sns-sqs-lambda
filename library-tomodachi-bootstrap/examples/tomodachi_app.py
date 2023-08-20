import uuid

import structlog
import tomodachi
from aiohttp import web
from tomodachi.envelope.json_base import JsonBase

from tomodachi_bootstrap import TomodachiServiceBase

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class TomodachiService(TomodachiServiceBase):
    name = "example"

    @tomodachi.http("GET", r"/corelation-id?", ignore_logging=[200])
    async def http_forward_correlation_id(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        logger.info("http_forward_correlation_id")
        return web.json_response({"correlation_id": str(correlation_id)}, status=200)

    @tomodachi.aws_sns_sqs("incoming-topic", queue_name="incoming-queue", message_envelope=JsonBase)
    async def sns_sqs_forward_correlation_id(self, data: dict, correlation_id: uuid.UUID) -> None:
        message = {"correlation_id": str(correlation_id)}
        logger.info("sns_sqs_forward_correlation_id")
        await tomodachi.aws_sns_sqs_publish(self, message, topic="outgoing-topic", message_envelope=JsonBase)
