import uuid

import tomodachi
from aiohttp import web
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase

from adapters import dynamodb, outbox, sns
from adapters.settings import get_settings
from orders.commands import ApproveOrderCommand, CancelOrderCommand, CreateOrderCommand, RejectOrderCommand
from service_layer import use_cases, views
from service_layer.response import CreateOrderResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork


class TomodachiService(tomodachi.Service):
    name = "service-orders"

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
        await dynamodb.create_aggregate_table()
        await dynamodb.create_outbox_table()
        await outbox.create_dynamodb_streams_outbox()

    @tomodachi.http("GET", r"/orders/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)

    @tomodachi.http("POST", r"/orders")
    async def create_order_handler(self, request: web.Request) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        data = await request.json()
        cmd = CreateOrderCommand(
            customer_id=uuid.UUID(data["customer_id"]),
            order_total=Money.from_sub_units(int(data["order_total"])).as_decimal(),
        )
        customer = await use_cases.create_order(uow, cmd)
        response = CreateOrderResponse.create(customer)
        return web.json_response(response.to_dict(), status=response.status_code)

    @tomodachi.http("GET", r"/order/(?P<order_id>[^/]+?)/?")
    async def get_order_handler(self, request: web.Request, order_id: str) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        response = await views.get_order(uow, order_id=uuid.UUID(order_id))
        return web.json_response(response.to_dict(), status=response.status_code)

    @tomodachi.http("POST", r"/order/(?P<order_id>[^/]+?)/cancel?")
    async def cancel_order_handler(self, request: web.Request, order_id: str) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        cmd = CancelOrderCommand(order_id=uuid.UUID(order_id))
        response = await use_cases.cancel_order(uow, cmd)
        return web.json_response(response.to_dict(), status=response.status_code)

    @tomodachi.aws_sns_sqs(
        "customer--credit-reserved",
        queue="order--customer-credit-reserved",
        message_envelope=JsonBase,
    )
    async def customer_credit_reserved_handler(self, data: dict) -> None:
        uow = DynamoDBUnitOfWork.create()
        cmd = ApproveOrderCommand(
            correlation_id=uuid.UUID(data["correlation_id"]), order_id=uuid.UUID(data["order_id"])
        )
        await use_cases.approve_order(uow, cmd)

    @tomodachi.aws_sns_sqs(
        "customer--credit-reservation-failed",
        queue="order--customer-credit-reservation-failed",
        message_envelope=JsonBase,
    )
    async def customer_credit_reservation_failed_handler(self, data: dict) -> None:
        uow = DynamoDBUnitOfWork.create()
        cmd = RejectOrderCommand(correlation_id=uuid.UUID(data["correlation_id"]), order_id=uuid.UUID(data["order_id"]))
        await use_cases.reject_order(uow, cmd)
