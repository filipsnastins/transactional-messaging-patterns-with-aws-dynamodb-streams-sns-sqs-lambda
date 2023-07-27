import tomodachi
from adapters import dynamodb
from aiohttp import web
from customers.commands import CreateCustomerCommand
from service_layer.unit_of_work import DynamoDBUnitOfWork
from service_layer.use_cases import create_customer
from stockholm import Money


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    async def _start_service(self) -> None:
        await dynamodb.create_dynamodb_table()

    @tomodachi.http("GET", r"/health")
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response(data={"status": "ok"})

    @tomodachi.http("POST", r"/customers")
    async def create_customer(self, request: web.Request) -> web.Response:
        data = await request.json()
        cmd = CreateCustomerCommand(
            name=data["name"],
            credit_limit=Money.from_sub_units(data["credit_limit"]).as_decimal(),
        )

        uow = DynamoDBUnitOfWork.create()
        customer = await create_customer(uow, cmd)

        return web.json_response(
            {
                "id": str(customer.id),
                "_links": {
                    "self": {"href": f"/customer/{customer.id}"},
                },
            }
        )

    @tomodachi.http("GET", r"/customer/(?P<customer_id>[^/]+?)/?")
    async def get_customer(self, request: web.Request, customer_id: str) -> web.Response:
        return web.json_response(
            {
                "id": customer_id,
                "name": "John Doe",
                "credit_limit": 24999,
                "available_credit": 24999,
                "created_at": "2021-01-01T00:00:00+00:00",
                "version": 0,
                "_links": {
                    "self": {"href": f"/customer/{customer_id}"},
                },
            }
        )
