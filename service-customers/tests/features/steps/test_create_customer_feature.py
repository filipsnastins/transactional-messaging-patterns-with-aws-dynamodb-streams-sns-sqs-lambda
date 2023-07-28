from asyncio import AbstractEventLoop

import httpx
from pytest_bdd import given, parsers, scenarios, then, when
from stockholm import Money

scenarios("../create_customer.feature")


@given(parsers.parse('customer with name "{name}" and credit limit "{credit_limit}"'), target_fixture="customer")
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
    async def _async() -> None:
        body = create_customer.json()
        customer_id = body["id"]
        get_customer_link = body["_links"]["self"]["href"]

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


@when(parsers.parse('customer with ID "{customer_id}" is queried'), target_fixture="get_customer")
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
