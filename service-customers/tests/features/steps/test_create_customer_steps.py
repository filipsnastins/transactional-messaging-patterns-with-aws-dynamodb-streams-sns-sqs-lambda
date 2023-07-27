from asyncio import AbstractEventLoop
from decimal import Decimal

import httpx
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../create_customer.feature")


@given(parsers.parse('customer with name "{name}" and credit limit "{credit_limit}"'), target_fixture="customer")
def _(name: str, credit_limit: str) -> dict:
    return {
        "name": name,
        "credit_limit": int(Decimal(credit_limit) * 100),
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


@then("the customer is created successfully")
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
    event_loop: AbstractEventLoop, http_client: httpx.AsyncClient, customer: dict, create_customer: httpx.Response
) -> None:
    body = create_customer.json()
    customer_id = body["id"]
    get_customer_link = body["_links"]["self"]["href"]

    async def _async() -> None:
        response = await http_client.get(get_customer_link)

        assert response.status_code == 200
        assert response.json() == {
            "id": customer_id,
            "name": customer["name"],
            "credit_limit": customer["credit_limit"],
            "available_credit": customer["credit_limit"],
            "created_at": response.json()["created_at"],
            "version": 0,
            "_links": {
                "self": {"href": get_customer_link},
            },
        }

    return event_loop.run_until_complete(_async())
