import tomodachi
from aiohttp import web


class TomodachiService(tomodachi.Service):
    name = "service-customers"

    @tomodachi.http("GET", r"/health")
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response(data={"status": "ok"})
