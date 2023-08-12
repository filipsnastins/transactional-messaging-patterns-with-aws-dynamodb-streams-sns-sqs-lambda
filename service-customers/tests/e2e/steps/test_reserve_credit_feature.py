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

scenarios("../../features/reserve_credit.feature")


@then("the CustomerCreditReservationFailed event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, create_customer: httpx.Response, order_id: uuid.UUID
) -> None:
    async def _assert_customer_credit_reserved() -> None:
        customer_id = create_customer.json()["id"]
        [message] = await snssqs_client.receive(
            moto_sqs_client, "customer--credit-reservation-failed", JsonBase, dict[str, Any]
        )

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": str(order_id),
            "customer_id": customer_id,
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@when("order is created for not existing customer", target_fixture="not_existing_customer_id")
def _(event_loop: AbstractEventLoop, moto_sns_client: SNSClient) -> uuid.UUID:
    async def _async() -> uuid.UUID:
        customer_id = uuid.uuid4()
        data = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": str(uuid.uuid4()),
            "order_id": str(uuid.uuid4()),
            "customer_id": str(customer_id),
            "order_total": 10000,
            "created_at": datetime_to_str(utcnow()),
        }

        await snssqs_client.publish(moto_sns_client, "order--created", data, JsonBase)

        return customer_id

    return event_loop.run_until_complete(_async())
