import httpx
import pytest


@pytest.mark.asyncio()
async def test_healthcheck(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/orders/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
