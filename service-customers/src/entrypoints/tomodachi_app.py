import os
import uuid

import tomodachi
from aiohttp import web

from adapters import dynamodb, outbox
from customers.commands import CreateCustomerCommand
from service_layer import use_cases, views
from service_layer.response import CreateCustomerResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    options = tomodachi.Options(
        aws_endpoint_urls=tomodachi.Options.AWSEndpointURLs(
            sns=os.environ.get("AWS_SNS_ENDPOINT_URL"),
            sqs=os.environ.get("AWS_SQS_ENDPOINT_URL"),
        ),
        aws_sns_sqs=tomodachi.Options.AWSSNSSQS(
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            topic_prefix=os.environ.get("AWS_SNS_TOPIC_PREFIX", ""),
            queue_name_prefix=os.environ.get("AWS_SQS_QUEUE_NAME_PREFIX", ""),
        ),
    )

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
