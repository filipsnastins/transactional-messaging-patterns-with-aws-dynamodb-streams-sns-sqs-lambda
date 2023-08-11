import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
from pytest_bdd import scenarios, then, when
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

from utils.time import datetime_to_str, utcnow

scenarios("../order_credit_check.feature")


@when("CustomerCreditReservationFailed event is received")
def _(
    event_loop: AbstractEventLoop, moto_sns_client: SNSClient, customer_id: uuid.UUID, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]

    async def _async() -> None:
        data = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": str(uuid.uuid4()),
            "order_id": order_id,
            "customer_id": str(customer_id),
            "created_at": datetime_to_str(utcnow()),
        }

        await snssqs_client.publish(moto_sns_client, "customer--credit-reservation-failed", data, JsonBase)

    event_loop.run_until_complete(_async())


@then("the OrderApproved event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, customer_id: uuid.UUID, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]

    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "order--approved", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": order_id,
            "customer_id": str(customer_id),
            "state": "APPROVED",
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@then("the OrderRejected event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, customer_id: uuid.UUID, create_order: httpx.Response
) -> None:
    order_id = create_order.json()["id"]

    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "order--rejected", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": order_id,
            "customer_id": str(customer_id),
            "state": "REJECTED",
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())
