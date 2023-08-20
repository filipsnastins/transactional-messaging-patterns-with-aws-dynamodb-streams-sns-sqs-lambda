import uuid

import pytest

from tests.middleware.proto_build.message_pb2 import MessageWithCorrelationId, MessageWithoutCorrelationId
from tomodachi_bootstrap.middleware import message_correlation_id_middleware


@pytest.mark.asyncio()
async def test_correlation_id_fetched_from_json_message() -> None:
    message = {"data": {"correlation_id": "430d1506-5e9c-467d-a303-751d2ddee79d"}}

    async def _message_handler(message: dict, correlation_id: uuid.UUID) -> None:
        assert message == {"data": {"correlation_id": "430d1506-5e9c-467d-a303-751d2ddee79d"}}
        assert isinstance(correlation_id, uuid.UUID)
        assert correlation_id == uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")

    await message_correlation_id_middleware(_message_handler, message=message)


@pytest.mark.asyncio()
async def test_correlation_id_fetched_from_protobuf_message() -> None:
    event_id = str(uuid.uuid4())
    message = MessageWithCorrelationId(event_id=event_id, correlation_id="430d1506-5e9c-467d-a303-751d2ddee79d")

    async def _message_handler(message: MessageWithCorrelationId, correlation_id: uuid.UUID) -> None:
        assert message == MessageWithCorrelationId(
            event_id=event_id, correlation_id="430d1506-5e9c-467d-a303-751d2ddee79d"
        )
        assert isinstance(correlation_id, uuid.UUID)
        assert correlation_id == uuid.UUID("430d1506-5e9c-467d-a303-751d2ddee79d")

    await message_correlation_id_middleware(_message_handler, message=message)


@pytest.mark.asyncio()
async def test_new_correlation_id_generated__json_message() -> None:
    message = {"data": {"foo": "bar"}}

    async def _message_handler(message: dict, correlation_id: uuid.UUID) -> None:
        assert message == {"data": {"foo": "bar"}}
        assert isinstance(correlation_id, uuid.UUID)

    await message_correlation_id_middleware(_message_handler, message=message)


@pytest.mark.asyncio()
async def test_new_correlation_id_generated__protobuf_message() -> None:
    event_id = str(uuid.uuid4())
    message = MessageWithoutCorrelationId(event_id=event_id)

    async def _message_handler(message: MessageWithoutCorrelationId, correlation_id: uuid.UUID) -> None:
        assert message == MessageWithoutCorrelationId(event_id=event_id)
        assert isinstance(correlation_id, uuid.UUID)

    await message_correlation_id_middleware(_message_handler, message=message)


@pytest.mark.asyncio()
async def test_new_correlation_id_generated__other_message_type() -> None:
    message = ["foo", "bar"]

    async def _message_handler(message: tuple, correlation_id: uuid.UUID) -> None:
        assert message == ["foo", "bar"]
        assert isinstance(correlation_id, uuid.UUID)

    await message_correlation_id_middleware(_message_handler, message=message)
