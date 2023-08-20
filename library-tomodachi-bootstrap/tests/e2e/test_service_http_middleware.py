import uuid

import httpx
import pytest
from tomodachi_testcontainers.containers import TomodachiContainer


@pytest.mark.asyncio()
async def test_correlation_id_forwarded_from_http_header(http_client: httpx.AsyncClient) -> None:
    correlation_id = "4695079f-e5a5-4688-86ad-0ebbb4225d47"

    response = await http_client.get("/corelation-id", headers={"X-Correlation-Id": correlation_id})

    assert response.status_code == 200
    assert response.json() == {"correlation_id": correlation_id}
    assert response.headers["X-Correlation-Id"] == correlation_id


@pytest.mark.asyncio()
async def test_new_correlation_id_generated_if_http_header_is_not_set(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/corelation-id")

    assert response.status_code == 200
    body = response.json()
    correlation_id = uuid.UUID(body["correlation_id"])
    assert response.json() == {"correlation_id": str(correlation_id)}
    assert response.headers["X-Correlation-Id"] == str(correlation_id)


@pytest.mark.asyncio()
async def test_correlation_id_bound_to_logs(
    tomodachi_container: TomodachiContainer, http_client: httpx.AsyncClient
) -> None:
    correlation_id = "4695079f-e5a5-4688-86ad-0ebbb4225d47"

    await http_client.get("/corelation-id", headers={"X-Correlation-Id": correlation_id})

    _, logs = tomodachi_container.get_logs()
    assert '"correlation_id": "4695079f-e5a5-4688-86ad-0ebbb4225d47"' in logs.decode()
