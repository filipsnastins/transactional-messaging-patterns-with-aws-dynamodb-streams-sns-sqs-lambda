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

scenarios("../create_customer.feature")


@given(parsers.parse('a customer data with credit limit of "{credit_limit}"'), target_fixture="customer_data")
def _(credit_limit: str) -> dict:
    return {
        "name": "John Doe",
        "credit_limit": int(Money(credit_limit).to_sub_units()),
    }


@when("customer creation is requested", target_fixture="create_customer")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer_data: dict) -> httpx.Response:
    async def _async() -> httpx.Response:
        data = {
            "name": customer_data["name"],
            "credit_limit": customer_data["credit_limit"],
        }

        return await http_client.post("/customers", json=data)

    return event_loop.run_until_complete(_async())


@then("the customer creation request succeeded")
def _(create_customer: httpx.Response) -> None:
    assert create_customer.status_code == 200
    body = create_customer.json()
    assert body == {
        "id": body["id"],
        "_links": {
            "self": {"href": f"/customer/{body['id']}"},
        },
    }


@then("the customer is created")
def _(
    event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer_data: dict, create_customer: httpx.Response
) -> None:
    body = create_customer.json()
    customer_id = body["id"]
    get_customer_link = body["_links"]["self"]["href"]

    async def _async() -> None:
        response = await http_client.get(get_customer_link)

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "id": customer_id,
            "name": customer_data["name"],
            "credit_limit": customer_data["credit_limit"],
            "available_credit": body["available_credit"],
            "version": 0,
            "created_at": body["created_at"],
            "updated_at": None,
            "_links": {
                "self": {"href": get_customer_link},
            },
        }

    return event_loop.run_until_complete(_async())


@then("the CustomerCreated event is published")
def _(event_loop: AbstractEventLoop, moto_sqs_client: SQSClient, create_customer: httpx.Response) -> None:
    body = create_customer.json()
    customer_id = body["id"]

    async def _assert_customer_created_event_published() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "customer--created", JsonBase, dict[str, Any])

        assert message == {
            "event_id": message["event_id"],
            "correlation_id": message["correlation_id"],
            "customer_id": customer_id,
            "name": "John Doe",
            "credit_limit": 24999,
            "created_at": message["created_at"],
        }

    async def _async() -> None:
        await probe_until(_assert_customer_created_event_published, probe_interval=0.3, stop_after=8)

    return event_loop.run_until_complete(_async())


@when("not existing customer is queried", target_fixture="get_not_existing_customer")
def _(event_loop: AbstractEventLoop, http_client: httpx.AsyncClient) -> httpx.Response:
    async def _async() -> httpx.Response:
        customer_id = uuid.uuid4()
        return await http_client.get(f"/customer/{customer_id}")

    return event_loop.run_until_complete(_async())


@then("the customer is not found")
def _(get_not_existing_customer: httpx.Response) -> None:
    customer_id = get_not_existing_customer.url.path.split("/")[-1]

    assert get_not_existing_customer.status_code == 404
    assert get_not_existing_customer.json() == {
        "error": "CUSTOMER_NOT_FOUND",
        "_links": {
            "self": {"href": f"/customer/{customer_id}"},
        },
    }
