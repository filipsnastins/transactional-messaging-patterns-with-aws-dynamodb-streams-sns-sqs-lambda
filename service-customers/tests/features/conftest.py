import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
from pytest_bdd import given, parsers, then, when
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

from utils.time import datetime_to_str, utcnow

# Shared steps


@given(parsers.parse('customer exists with credit limit of "{credit_limit}"'), target_fixture="create_customer")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, credit_limit: str) -> httpx.Response:
    async def _async() -> httpx.Response:
        data = {
            "name": "John Doe",
            "credit_limit": int(Money(credit_limit).to_sub_units()),
        }

        response = await http_client.post("/customers", json=data)

        assert response.status_code == 200
        return response

    return event_loop.run_until_complete(_async())


@given(parsers.parse('order created with total amount of "{order_total}"'), target_fixture="order_id")
@when(parsers.parse('order created with total amount of "{order_total}"'), target_fixture="order_id")
def _(
    event_loop: AbstractEventLoop, moto_sns_client: SNSClient, create_customer: httpx.Response, order_total: str
) -> uuid.UUID:
    async def _async() -> uuid.UUID:
        order_id = uuid.uuid4()
        customer_id = create_customer.json()["id"]
        data = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": str(uuid.uuid4()),
            "order_id": str(order_id),
            "customer_id": customer_id,
            "order_total": int(Money(order_total).to_sub_units()),
            "created_at": datetime_to_str(utcnow()),
        }

        await snssqs_client.publish(moto_sns_client, "order--created", data, JsonBase)

        return order_id

    return event_loop.run_until_complete(_async())


@given("CustomerCreditReserved event is published")
@then("CustomerCreditReserved event is published")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, create_customer: httpx.Response, order_id: uuid.UUID
) -> None:
    async def _assert_customer_credit_reserved() -> None:
        customer_id = create_customer.json()["id"]
        [message] = await snssqs_client.receive(moto_sqs_client, "customer--credit-reserved", JsonBase, dict[str, Any])

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


@given(parsers.parse('the customer available credit is "{available_credit}"'))
@then(parsers.parse('the customer available credit is "{available_credit}"'))
def _(
    event_loop: AbstractEventLoop,
    http_client: httpx.AsyncClient,
    create_customer: httpx.Response,
    available_credit: str,
) -> None:
    async def _validate_customer_available_credit() -> None:
        get_customer_link = create_customer.json()["_links"]["self"]["href"]

        response = await http_client.get(get_customer_link)
        body = response.json()

        assert response.status_code == 200
        assert body["available_credit"] == int(Money(available_credit).to_sub_units())

    async def _async() -> None:
        await probe_until(_validate_customer_available_credit, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@then(parsers.parse('the CustomerValidationFailed event is published - "{error}"'))
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, not_existing_customer_id: uuid.UUID, error: str
) -> None:
    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(
            moto_sqs_client, "customer--validation-failed", JsonBase, dict[str, Any]
        )

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "order_id": message["order_id"],
            "customer_id": str(not_existing_customer_id),
            "error": error,
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_credit_reserved, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())
