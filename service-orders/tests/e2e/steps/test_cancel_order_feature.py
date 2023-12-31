import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
from pytest_bdd import given, scenarios, then, when
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_during_interval, probe_until
from types_aiobotocore_sqs import SQSClient

scenarios("../../features/cancel_order.feature")


@given("order cancellation is requested", target_fixture="cancel_order")
@when("order cancellation is requested", target_fixture="cancel_order")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, create_order: httpx.Response) -> httpx.Response:
    cancel_order_link = create_order.json()["_links"]["cancel"]["href"]

    async def _async() -> httpx.Response:
        return await http_client.post(cancel_order_link)

    return event_loop.run_until_complete(_async())


@given("the order cancellation request succeeded")
@then("the order cancellation request succeeded")
def _(create_order: httpx.Response, cancel_order: httpx.Response) -> None:
    order_id = create_order.json()["id"]

    assert cancel_order.status_code == 200
    assert cancel_order.json() == {
        "id": order_id,
        "_links": {
            "self": {"href": f"/order/{order_id}"},
            "cancel": {"href": f"/order/{order_id}/cancel"},
        },
    }


@given("the OrderCancelled event is published")
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


@then("the OrderCancelled event is not published")
def _(event_loop: AbstractEventLoop, moto_sqs_client: SQSClient) -> None:
    async def _assert_customer_credit_reserved() -> None:
        messages = await snssqs_client.receive(moto_sqs_client, "order--cancelled", JsonBase, dict[str, Any])

        assert len(messages) == 0

    async def _async() -> None:
        await probe_during_interval(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@then("the order cancellation request succeeded")
def _(create_order: httpx.Response, cancel_order: httpx.Response) -> None:
    order_id = create_order.json()["id"]

    assert cancel_order.status_code == 200
    assert cancel_order.json() == {
        "id": order_id,
        "_links": {
            "self": {"href": f"/order/{order_id}"},
            "cancel": {"href": f"/order/{order_id}/cancel"},
        },
    }


@then("pending order cannot be cancelled error is returned")
def _(create_order: httpx.Response, cancel_order: httpx.Response) -> None:
    order_id = create_order.json()["id"]

    assert cancel_order.status_code == 400
    assert cancel_order.json() == {
        "error": "PENDING_ORDER_CANNOT_BE_CANCELLED_ERROR",
        "_links": {
            "self": {"href": f"/order/{order_id}"},
            "cancel": {"href": f"/order/{order_id}/cancel"},
        },
    }
