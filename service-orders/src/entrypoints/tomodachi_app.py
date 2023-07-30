import tomodachi
from aiohttp import web


class TomodachiService(tomodachi.Service):
    name = "service-orders"

    @tomodachi.http("GET", r"/orders/health/?", ignore_logging=[200])
    async def healthcheck(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)
