import tomodachi
from aiohttp import web


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    @tomodachi.http("GET", r"/health")
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response(data={"status": "ok"})

    @tomodachi.http("POST", r"/customers")
    async def create_customer(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "id": "0c0ca9df-71e7-4762-a105-4babfd4a8da5",
                "_links": {
                    "self": {"href": "/customer/0c0ca9df-71e7-4762-a105-4babfd4a8da5"},
                },
            }
        )

    @tomodachi.http("GET", r"/customer/(?P<customer_id>[^/]+?)/?")
    async def get_customer(self, request: web.Request, customer_id: str) -> web.Response:
        return web.json_response(
            {
                "id": customer_id,
                "name": "John Doe",
                "credit_limit": 20000,
                "available_credit": 20000,
                "created_at": "2021-01-01T00:00:00+00:00",
                "version": 0,
                "_links": {
                    "self": {"href": f"/customer/{customer_id}"},
                },
            }
        )
