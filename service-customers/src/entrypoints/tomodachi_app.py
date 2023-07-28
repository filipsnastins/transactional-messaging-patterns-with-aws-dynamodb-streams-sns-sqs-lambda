import uuid

import tomodachi
from adapters import dynamodb
from aiohttp import web
from customers.commands import CreateCustomerCommand
from service_layer import use_cases, views
from service_layer.response import CreateCustomerResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    async def _start_service(self) -> None:
        await dynamodb.create_dynamodb_table()

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
