import uuid

import pytest
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.containers import TomodachiContainer
from tomodachi_testcontainers.pytest.async_probes import probe_until
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient


@pytest.mark.asyncio()
async def test_correlation_id_forwarded_from_message_data(
    tomodachi_container: TomodachiContainer, moto_sns_client: SNSClient, moto_sqs_client: SQSClient
) -> None:
    correlation_id = "4695079f-e5a5-4688-86ad-0ebbb4225d47"

    await snssqs_client.publish(moto_sns_client, "incoming-topic", {"correlation_id": correlation_id}, JsonBase)

    async def _assert_correlation_forwarded() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "outgoing-queue", JsonBase, dict[str, str])

        assert message["correlation_id"] == correlation_id

    await probe_until(_assert_correlation_forwarded)


@pytest.mark.asyncio()
async def test_new_correlation_id_generated_if_correlation_id_not_passed_in_message_data(
    tomodachi_container: TomodachiContainer, moto_sns_client: SNSClient, moto_sqs_client: SQSClient
) -> None:
    await snssqs_client.publish(moto_sns_client, "incoming-topic", {}, JsonBase)

    async def _assert_new_correlation_is_generated() -> None:
        [message] = await snssqs_client.receive(moto_sqs_client, "outgoing-queue", JsonBase, dict[str, str])

        assert uuid.UUID(message["correlation_id"])

    await probe_until(_assert_new_correlation_is_generated)


@pytest.mark.asyncio()
async def test_correlation_id_bound_to_logs(
    tomodachi_container: TomodachiContainer, moto_sns_client: SNSClient
) -> None:
    correlation_id = "4695079f-e5a5-4688-86ad-0ebbb4225d47"

    await snssqs_client.publish(moto_sns_client, "incoming-topic", {"correlation_id": correlation_id}, JsonBase)

    async def _assert_correlation_id_bound_to_logs() -> None:
        _, logs = tomodachi_container.get_logs()

        assert '"correlation_id": "4695079f-e5a5-4688-86ad-0ebbb4225d47"' in logs.decode()

    await probe_until(_assert_correlation_id_bound_to_logs)
