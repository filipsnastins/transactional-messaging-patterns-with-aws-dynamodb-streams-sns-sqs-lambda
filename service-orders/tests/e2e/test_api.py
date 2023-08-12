import httpx
import pytest


@pytest.mark.asyncio()
async def test_healthcheck(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/orders/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio()
async def test_error_500(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/order/invalid-uuid-format")

    assert response.status_code == 500
    assert response.json() == {"error": "SYSTEM_ERROR"}
