import uuid
from asyncio import AbstractEventLoop

import httpx
import pytest
from pytest_bdd import given, parsers, then, when
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sns import SNSClient

from utils.time import datetime_to_str, utcnow


@pytest.fixture()
def customer_id() -> uuid.UUID:
    return uuid.uuid4()


@given(parsers.parse('an order is created with total amount of "{order_total}"'), target_fixture="create_order")
def _(
    event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer_id: uuid.UUID, order_total: str
) -> httpx.Response:
    async def _async() -> httpx.Response:
        data = {
            "customer_id": str(customer_id),
            "order_total": int(Money(order_total).to_sub_units()),
        }

        return await http_client.post("/orders", json=data)

    return event_loop.run_until_complete(_async())


@given(parsers.parse('the order state is "{state}"'))
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


@given("CustomerCreditReserved event is received")
@when("CustomerCreditReserved event is received")
def _(
    event_loop: AbstractEventLoop, moto_sns_client: SNSClient, customer_id: uuid.UUID, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]

    async def _async() -> None:
        data = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": str(uuid.uuid4()),
            "customer_id": str(customer_id),
            "order_id": order_id,
            "created_at": datetime_to_str(utcnow()),
        }

        await snssqs_client.publish(moto_sns_client, "customer--credit-reserved", data, JsonBase)

    event_loop.run_until_complete(_async())
