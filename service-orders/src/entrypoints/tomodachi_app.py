import uuid

import tomodachi
from aiohttp import web
from stockholm import Money

from adapters import dynamodb, outbox, sns
from orders.commands import CreateOrderCommand
from service_layer import use_cases, views
from service_layer.response import CreateOrderResponse
from service_layer.unit_of_work import DynamoDBUnitOfWork


class TomodachiService(tomodachi.Service):
    name = "service-orders"

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
    async def get_customer_handler(self, request: web.Request, order_id: str) -> web.Response:
        uow = DynamoDBUnitOfWork.create()
        response = await views.get_order(uow, order_id=uuid.UUID(order_id))
        return web.json_response(response.to_dict(), status=response.status_code)
