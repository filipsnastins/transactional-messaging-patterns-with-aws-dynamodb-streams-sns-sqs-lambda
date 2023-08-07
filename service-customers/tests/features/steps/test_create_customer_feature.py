from asyncio import AbstractEventLoop
from typing import Any

import httpx
import pytest
from busypie import wait_at_most
from pytest_bdd import given, parsers, scenarios, then, when
from stockholm import Money
from tomodachi.envelope.json_base import JsonBase
from types_aiobotocore_sqs import SQSClient

from tomodachi_testcontainers.clients import snssqs_client

pytestmark = pytest.mark.xfail(strict=False)


scenarios("../create_customer.feature")


@given(
    parsers.parse('customer with name "{name}" and credit limit "{credit_limit}"'),
    target_fixture="customer",
)
def _(name: str, credit_limit: str) -> dict:
    return {
        "name": name,
        "credit_limit": int(Money(credit_limit).to_sub_units()),
    }


@when("customer creation is requested", target_fixture="create_customer")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer: dict) -> httpx.Response:
    async def _async() -> httpx.Response:
        data = {
            "name": customer["name"],
            "credit_limit": customer["credit_limit"],
        }

        return await http_client.post("/customers", json=data)

    return event_loop.run_until_complete(_async())


@then("the customer creation request is successful")
def _(create_customer: httpx.Response) -> None:
    assert create_customer.status_code == 200
    body = create_customer.json()
    assert body == {
        "id": body["id"],
        "_links": {
            "self": {"href": f"/customer/{body['id']}"},
        },
    }


@then("the customer is created with correct data and full available credit")
def _(
    event_loop: AbstractEventLoop,
    http_client: httpx.AsyncClient,
    moto_sqs_client: SQSClient,
    customer: dict,
    create_customer: httpx.Response,
) -> None:
    body = create_customer.json()
    customer_id = body["id"]
    get_customer_link = body["_links"]["self"]["href"]

    async def _assert_get_customer() -> None:
        response = await http_client.get(get_customer_link)

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "id": customer_id,
            "name": customer["name"],
            "credit_limit": customer["credit_limit"],
            "available_credit": customer["credit_limit"],
            "created_at": body["created_at"],
            "version": 0,
            "_links": {
                "self": {"href": get_customer_link},
            },
        }

    async def _assert_customer_created() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "customer--created", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "customer_id": customer_id,
            "name": "John Doe",
            "credit_limit": 24999,
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await wait_at_most(3).until_asserted_async(_assert_get_customer)
        await wait_at_most(3).until_asserted_async(_assert_customer_created)

    return event_loop.run_until_complete(_async())


@when(
    parsers.parse('customer with ID "{customer_id}" is queried'),
    target_fixture="get_customer",
)
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer_id: str) -> httpx.Response:
    async def _async() -> httpx.Response:
        return await http_client.get(f"/customer/{customer_id}")

    return event_loop.run_until_complete(_async())


@then("the customer is not found")
def _(get_customer: httpx.Response) -> None:
    customer_id = get_customer.url.path.split("/")[-1]

    assert get_customer.status_code == 404
    assert get_customer.json() == {
        "error": "CUSTOMER_NOT_FOUND",
        "_links": {
            "self": {"href": f"/customer/{customer_id}"},
        },
    }
