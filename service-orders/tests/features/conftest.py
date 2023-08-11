from asyncio import AbstractEventLoop

import httpx
from pytest_bdd import parsers, then
from tomodachi_testcontainers.pytest.async_probes import probe_until


@then(parsers.parse('the order state is "{state}"'))
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, create_order: httpx.Response, state: str) -> None:
    body = create_order.json()
    get_order_link = body["_links"]["self"]["href"]

    async def _assert_order_state() -> None:
        response = await http_client.get(get_order_link)

        assert response.status_code == 200
        body = response.json()
        assert body["state"] == state

    async def _async() -> None:
        await probe_until(_assert_order_state, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())
