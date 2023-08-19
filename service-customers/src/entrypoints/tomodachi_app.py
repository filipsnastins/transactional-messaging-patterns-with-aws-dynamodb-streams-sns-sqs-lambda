import uuid

import tomodachi
from aiohttp import web
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase

from adapters import dynamodb, inbox, outbox, sns
from adapters.settings import get_settings
from customers.commands import CreateCustomerCommand, ReleaseCreditCommand, ReserveCreditCommand
from entrypoints.middleware import (
    http_correlation_id_middleware,
    message_correlation_id_middleware,
    message_retry_middleware,
    structlog_logger_middleware,
)
from service_layer import use_cases, views
from service_layer.logger import configure_structlog
from service_layer.response import ResponseTypes
from service_layer.unit_of_work import DynamoDBUnitOfWork

STATUS_CODES: dict[ResponseTypes, int] = {
    ResponseTypes.SUCCESS: 200,
    ResponseTypes.CUSTOMER_NOT_FOUND_ERROR: 404,
    ResponseTypes.SYSTEM_ERROR: 500,
}


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    http_middleware: list = [
        http_correlation_id_middleware,
        structlog_logger_middleware,
    ]
    message_middleware: list = [
        message_retry_middleware,
        message_correlation_id_middleware,
        structlog_logger_middleware,
    ]

    def __init__(self) -> None:
        configure_structlog()
        self.settings = get_settings()
        self.options = tomodachi.Options(
            aws_endpoint_urls=tomodachi.Options.AWSEndpointURLs(
                sns=self.settings.aws_endpoint_url,
                sqs=self.settings.aws_endpoint_url,
            ),
            aws_sns_sqs=tomodachi.Options.AWSSNSSQS(
                region_name=self.settings.aws_region,
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                topic_prefix=self.settings.aws_sns_topic_prefix,
                queue_name_prefix=self.settings.aws_sqs_queue_name_prefix,
            ),
        )

    async def _start_service(self) -> None:
        if self.settings.environment in ["development", "autotest"]:
            await sns.create_topics()
            await dynamodb.create_customers_table()
            await inbox.create_inbox_table()
            await outbox.create_outbox_table()
            await outbox.create_dynamodb_streams_outbox()

    @tomodachi.http("GET", r"/customers/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        return web.json_response(
            {"status": "ok"},
            status=200,
            headers={"X-Correlation-Id": str(correlation_id)},
        )

    @tomodachi.http_error(status_code=500)
    async def error_500(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        return web.json_response(
            {"error": ResponseTypes.SYSTEM_ERROR.value},
            status=500,
            headers={"X-Correlation-Id": str(correlation_id)},
        )

    @tomodachi.http("POST", r"/customers")
    async def create_customer_handler(self, request: web.Request, correlation_id: uuid.UUID) -> web.Response:
        async with DynamoDBUnitOfWork() as uow:
            data = await request.json()
            cmd = CreateCustomerCommand(
                correlation_id=correlation_id,
                name=str(data["name"]),
                credit_limit=Money.from_sub_units(int(data["credit_limit"])).as_decimal(),
            )
            response = await use_cases.create_customer(uow, cmd)
            return web.json_response(
                response.to_dict(),
                status=STATUS_CODES[response.type],
                headers={"X-Correlation-Id": str(correlation_id)},
            )

    @tomodachi.http("GET", r"/customer/(?P<customer_id>[^/]+?)/?")
    async def get_customer_handler(
        self, request: web.Request, customer_id: str, correlation_id: uuid.UUID
    ) -> web.Response:
        async with DynamoDBUnitOfWork() as uow:
            response = await views.get_customer(uow, customer_id=uuid.UUID(customer_id))
            return web.json_response(
                response.to_dict(),
                status=STATUS_CODES[response.type],
                headers={"X-Correlation-Id": str(correlation_id)},
            )

    @tomodachi.aws_sns_sqs(
        "order--created",
        queue_name="customer--order-created",
        dead_letter_queue_name="customer--order-created--dlq",
        max_receive_count=3,
        message_envelope=JsonBase,
    )
    async def order_created_handler(self, data: dict, correlation_id: uuid.UUID) -> None:
        async with DynamoDBUnitOfWork(message_id=uuid.UUID(data["event_id"])) as uow:
            event = ReserveCreditCommand(
                correlation_id=correlation_id,
                order_id=uuid.UUID(data["order_id"]),
                customer_id=uuid.UUID(data["customer_id"]),
                order_total=Money.from_sub_units(int(data["order_total"])).as_decimal(),
            )
            await use_cases.reserve_credit(uow, event)

    @tomodachi.aws_sns_sqs(
        "order--cancelled",
        queue_name="customer--order-cancelled",
        dead_letter_queue_name="customer--order-cancelled--dlq",
        max_receive_count=3,
        message_envelope=JsonBase,
    )
    async def order_cancelled_handler(self, data: dict, correlation_id: uuid.UUID) -> None:
        async with DynamoDBUnitOfWork(message_id=uuid.UUID(data["event_id"])) as uow:
            event = ReleaseCreditCommand(
                correlation_id=correlation_id,
                order_id=uuid.UUID(data["order_id"]),
                customer_id=uuid.UUID(data["customer_id"]),
            )
            await use_cases.release_credit(uow, event)
