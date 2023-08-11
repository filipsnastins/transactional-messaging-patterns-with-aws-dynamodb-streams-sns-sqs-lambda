import uuid
from asyncio import AbstractEventLoop

import httpx
from pytest_bdd import scenarios, when
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from types_aiobotocore_sns import SNSClient

from utils.time import datetime_to_str, utcnow

scenarios("../release_credit.feature")


@when("OrderCancelled event is received")
def _(
    event_loop: AbstractEventLoop, moto_sns_client: SNSClient, create_customer: httpx.Response, order_id: uuid.UUID
) -> None:
    async def _async() -> None:
        customer_id = create_customer.json()["id"]
        data = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": str(uuid.uuid4()),
            "order_id": str(order_id),
            "customer_id": customer_id,
            "created_at": datetime_to_str(utcnow()),
        }

        await snssqs_client.publish(moto_sns_client, "order--cancelled", data, JsonBase)

    event_loop.run_until_complete(_async())
