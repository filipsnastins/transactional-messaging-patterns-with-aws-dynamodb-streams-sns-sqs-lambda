import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
from pytest_bdd import given, parsers, scenarios, then, when
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sqs import SQSClient

scenarios("../create_order.feature")


@given(parsers.parse('an order data with total amount of "{order_total}"'), target_fixture="order_data")
def _(order_total: str) -> dict:
    return {
        "customer_id": str(uuid.uuid4()),
        "order_total": int(Money(order_total).to_sub_units()),
    }


@when("order creation is requested", target_fixture="create_order")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, order_data: dict) -> httpx.Response:
    async def _async() -> httpx.Response:
        data = {
            "customer_id": order_data["customer_id"],
            "order_total": order_data["order_total"],
        }

        response = await http_client.post("/orders", json=data)

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "id": body["id"],
            "_links": {
                "self": {"href": f"/order/{body['id']}"},
            },
        }

        return response

    return event_loop.run_until_complete(_async())


@then(parsers.parse('the order is created with state "{state}"'))
def _(
    event_loop: AbstractEventLoop,
    http_client: httpx.AsyncClient,
    order_data: dict,
    create_order: httpx.Response,
    state: str,
) -> None:
    body = create_order.json()
    order_id = body["id"]
    get_order_link = body["_links"]["self"]["href"]

    async def _async() -> None:
        response = await http_client.get(get_order_link)

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "id": order_id,
            "customer_id": order_data["customer_id"],
            "state": state,
            "order_total": order_data["order_total"],
            "version": 0,
            "created_at": body["created_at"],
            "updated_at": None,
            "_links": {
                "self": {"href": f"/order/{order_id}"},
            },
        }

    return event_loop.run_until_complete(_async())


@then("the OrderCreated event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, order_data: dict, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]
    customer_id = order_data["customer_id"]
    order_total = order_data["order_total"]

    async def _assert_customer_created() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "order--created", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": order_id,
            "customer_id": customer_id,
            "state": "PENDING",
            "order_total": order_total,
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_created, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@when("not existing order is queried", target_fixture="get_not_existing_order")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient) -> httpx.Response:
    async def _async() -> httpx.Response:
        order_id = uuid.uuid4()
        return await http_client.get(f"/order/{order_id}")

    return event_loop.run_until_complete(_async())


@then("the order is not found")
def _(get_not_existing_order: httpx.Response) -> None:
    order_id = get_not_existing_order.url.path.split("/")[-1]

    assert get_not_existing_order.status_code == 404
    assert get_not_existing_order.json() == {
        "error": "ORDER_NOT_FOUND",
        "_links": {
            "self": {"href": f"/order/{order_id}"},
        },
    }
