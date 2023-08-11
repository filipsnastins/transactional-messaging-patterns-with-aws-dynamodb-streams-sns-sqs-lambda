import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
from pytest_bdd import parsers, scenarios, then, when
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sqs import SQSClient

scenarios("../cancel_order.feature")


@when("order cancellation is requested", target_fixture="cancel_order")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, create_order: httpx.Response) -> httpx.Response:
    cancel_order_link = create_order.json()["_links"]["cancel"]["href"]

    async def _async() -> httpx.Response:
        return await http_client.post(cancel_order_link)

    return event_loop.run_until_complete(_async())


@then("the order cancellation request succeeded")
def _(cancel_order: httpx.Response) -> None:
    assert cancel_order.status_code == 200
    body = cancel_order.json()
    assert body == {
        "id": body["id"],
        "_links": {
            "self": {"href": f"/order/{body['id']}"},
            "cancel": {"href": f"/order/{body['id']}/cancel"},
        },
    }


@then("the OrderCancelled event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, customer_id: uuid.UUID, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]

    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "order--cancelled", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": order_id,
            "customer_id": str(customer_id),
            "state": "CANCELLED",
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@then("the order cancellation request succeeded")
def _(cancel_order: httpx.Response) -> None:
    assert cancel_order.status_code == 200
    body = cancel_order.json()
    assert body == {
        "id": body["id"],
        "_links": {
            "self": {"href": f"/order/{body['id']}"},
            "cancel": {"href": f"/order/{body['id']}/cancel"},
        },
    }


@then(parsers.parse("the order cancellation request failed {error}"))
def _(cancel_order: httpx.Response, error: str) -> None:
    assert cancel_order.status_code == 400
    body = cancel_order.json()
    assert body == {
        "error": error,
        "_links": {
            "self": {"href": f"/order/{body['id']}"},
            "cancel": {"href": f"/order/{body['id']}/cancel"},
        },
    }
