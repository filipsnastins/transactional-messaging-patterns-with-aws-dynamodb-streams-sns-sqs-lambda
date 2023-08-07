import datetime
import os
import uuid

import tomodachi
from aiohttp import web
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase

from adapters import dynamodb, outbox, sns
from customers.commands import CreateCustomerCommand
from customers.events import OrderCreatedExternalEvent
from service_layer import use_cases, views
from service_layer.response import CreateCustomerResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork
from utils.time import str_to_datetime


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    options = tomodachi.Options(
        aws_endpoint_urls=tomodachi.Options.AWSEndpointURLs(
            sns=os.environ.get("AWS_ENDPOINT_URL"),
            sqs=os.environ.get("AWS_ENDPOINT_URL"),
        ),
        aws_sns_sqs=tomodachi.Options.AWSSNSSQS(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            topic_prefix=os.environ.get("AWS_SNS_TOPIC_PREFIX", ""),
            queue_name_prefix=os.environ.get("AWS_SQS_QUEUE_NAME_PREFIX", ""),
        ),
    )

    async def _start_service(self) -> None:
        await sns.create_topics()
        await dynamodb.create_aggregate_table()
        await dynamodb.create_outbox_table()
        await outbox.create_dynamodb_streams_outbox()

    @tomodachi.http("GET", r"/customers/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)

    @tomodachi.http("POST", r"/customers")
    async def create_customer_handler(self, request: web.Request) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        data = await request.json()
        cmd = CreateCustomerCommand.from_dict(data)
        customer = await use_cases.create_customer(uow, cmd)
        response = CreateCustomerResponse.create(customer)
        return web.json_response(response.to_dict(), status=response.status_code)

    @tomodachi.http("GET", r"/customer/(?P<customer_id>[^/]+?)/?")
    async def get_customer_handler(self, request: web.Request, customer_id: str) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        response = await views.get_customer(uow, customer_id=uuid.UUID(customer_id))
        return web.json_response(response.to_dict(), status=response.status_code)

    @tomodachi.aws_sns_sqs(
        "order--created",
        queue="customer--order-created",
        message_envelope=JsonBase,
    )
    async def order_created_handler(self, data: dict) -> None:
        uow = DynamoDBUnitOfWork.create()
        event = OrderCreatedExternalEvent(
            event_id=uuid.UUID(data["event_id"]),
            order_id=uuid.UUID(data["order_id"]),
            customer_id=uuid.UUID(data["customer_id"]),
            order_total=Money.from_sub_units(int(data["order_total"])).as_decimal(),
            created_at=str_to_datetime(data["created_at"]),
        )
        await use_cases.reserve_credit(uow, event)
