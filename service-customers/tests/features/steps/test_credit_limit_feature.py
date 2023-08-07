import datetime
import uuid
from asyncio import AbstractEventLoop
from typing import Any

import httpx
import pytest
from busypie import wait_at_most
from pytest_bdd import given, parsers, scenarios, then, when
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient

pytestmark = pytest.mark.xfail(strict=True)

scenarios("../credit_limit.feature")


@given(parsers.parse('customer exists with credit limit "{credit_limit}"'), target_fixture="create_customer")
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


@when(parsers.parse('order created with total "{order_total}"'), target_fixture="order_id")
def _(
    event_loop: AbstractEventLoop, moto_sns_client: SNSClient, create_customer: httpx.Response, order_total: uuid.UUID
) -> uuid.UUID:
    async def _async() -> uuid.UUID:
        order_id = uuid.uuid4()
        data = {
            "order_id": str(order_id),
            "customer_id": create_customer.json()["id"],
            "order_total": int(Money(order_total).to_sub_units()),
            "created_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
        }

        await snssqs_client.publish(moto_sns_client, "order--created", data, JsonBase)

        return order_id

    return event_loop.run_until_complete(_async())


@then("the customer credit is reserved")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, create_customer: httpx.Response, order_id: uuid.UUID
) -> None:
    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "customer--credit-reserved", JsonBase, dict[str, Any])

        assert message == {
            "order_id": order_id,
            "customer_id": create_customer.json()["id"],
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await wait_at_most(3).until_asserted_async(_assert_customer_credit_reserved)

    return event_loop.run_until_complete(_async())


@then(parsers.parse('the customer available credit is "{available_credit}"'))
def _(
    event_loop: AbstractEventLoop,
    http_client: httpx.AsyncClient,
    create_customer: httpx.Response,
    available_credit: str,
) -> None:
    async def _async() -> None:
        get_customer_link = create_customer.json()["_links"]["self"]["href"]

        response = await http_client.get(get_customer_link)
        body = response.json()

        assert response.status_code == 200
        assert body["available_credit"] == int(Money(available_credit).to_sub_units())

    return event_loop.run_until_complete(_async())


@then("the customer credit reservation fails")
def _(
    event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, create_customer: httpx.Response, order_id: uuid.UUID
) -> None:
    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(
            moto_sqs_client, "customer--credit-reservation-failed", JsonBase, dict[str, Any]
        )

        assert message == {
            "order_id": order_id,
            "customer_id": create_customer.json()["id"],
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await wait_at_most(3).until_asserted_async(_assert_customer_credit_reserved)

    return event_loop.run_until_complete(_async())


@when("order is created for non-existing customer", target_fixture="non_existing_customer_id")
def _(event_loop: AbstractEventLoop, moto_sns_client: SNSClient) -> uuid.UUID:
    async def _async() -> uuid.UUID:
        customer_id = uuid.uuid4()
        data = {
            "order_id": str(uuid.uuid4()),
            "customer_id": str(customer_id),
            "order_total": 10000,
            "created_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
        }

        await snssqs_client.publish(moto_sns_client, "order--created", data, JsonBase)

        return customer_id

    return event_loop.run_until_complete(_async())


@then("the customer validation fails - customer is not found")
def _(event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, non_existing_customer_id: uuid.UUID) -> None:
    async def _assert_customer_credit_reserved() -> None:
        [message] = await snssqs_client.receive(
            moto_sqs_client, "customer--validation-failed", JsonBase, dict[str, Any]
        )

        assert message == {
            "customer_id": str(non_existing_customer_id),
            "error": "CUSTOMER_NOT_FOUND",
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await wait_at_most(3).until_asserted_async(_assert_customer_credit_reserved)

    return event_loop.run_until_complete(_async())
