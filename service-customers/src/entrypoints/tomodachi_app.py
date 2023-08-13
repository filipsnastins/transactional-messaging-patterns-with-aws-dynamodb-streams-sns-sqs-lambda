import uuid

import tomodachi
from aiohttp import web
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase

from adapters import dynamodb, outbox, sns
from adapters.settings import get_settings
from customers.commands import CreateCustomerCommand, ReleaseCreditCommand, ReserveCreditCommand
from service_layer import use_cases, views
from service_layer.response import ResponseTypes
from service_layer.unit_of_work import DynamoDBUnitOfWork

STATUS_CODES: dict[ResponseTypes, int] = {
    ResponseTypes.SUCCESS: 200,
    ResponseTypes.CUSTOMER_NOT_FOUND_ERROR: 404,
    ResponseTypes.SYSTEM_ERROR: 500,
}


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    def __init__(self) -> None:
        settings = get_settings()
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

    async def _start_service(self) -> None:
        await sns.create_topics()
        await dynamodb.create_customers_table()
        await outbox.create_outbox_table()
        await outbox.create_dynamodb_streams_outbox()

    @tomodachi.http("GET", r"/customers/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)

    @tomodachi.http_error(status_code=500)
    async def error_500(self, request: web.Request) -> web.Response:
        return web.json_response({"error": ResponseTypes.SYSTEM_ERROR.value}, status=500)

    @tomodachi.http("POST", r"/customers")
    async def create_customer_handler(self, request: web.Request) -> web.Response:
        uow = DynamoDBUnitOfWork()
        data = await request.json()
        cmd = CreateCustomerCommand(
            name=str(data["name"]),
            credit_limit=Money.from_sub_units(int(data["credit_limit"])).as_decimal(),
        )
        response = await use_cases.create_customer(uow, cmd)
        return web.json_response(response.to_dict(), status=STATUS_CODES[response.type])

    @tomodachi.http("GET", r"/customer/(?P<customer_id>[^/]+?)/?")
    async def get_customer_handler(self, request: web.Request, customer_id: str) -> web.Response:
        uow = DynamoDBUnitOfWork()
        response = await views.get_customer(uow, customer_id=uuid.UUID(customer_id))
        return web.json_response(response.to_dict(), status=STATUS_CODES[response.type])

    @tomodachi.aws_sns_sqs("order--created", queue="customer--order-created", message_envelope=JsonBase)
    async def order_created_handler(self, data: dict) -> None:
        uow = DynamoDBUnitOfWork()
        event = ReserveCreditCommand(
            correlation_id=uuid.UUID(data["correlation_id"]),
            order_id=uuid.UUID(data["order_id"]),
            customer_id=uuid.UUID(data["customer_id"]),
            order_total=Money.from_sub_units(int(data["order_total"])).as_decimal(),
        )
        await use_cases.reserve_credit(uow, event)

    @tomodachi.aws_sns_sqs("order--cancelled", queue="customer--order-cancelled", message_envelope=JsonBase)
    async def order_cancelled_handler(self, data: dict) -> None:
        uow = DynamoDBUnitOfWork()
        event = ReleaseCreditCommand(
            correlation_id=uuid.UUID(data["correlation_id"]),
            order_id=uuid.UUID(data["order_id"]),
            customer_id=uuid.UUID(data["customer_id"]),
        )
        await use_cases.release_credit(uow, event)
