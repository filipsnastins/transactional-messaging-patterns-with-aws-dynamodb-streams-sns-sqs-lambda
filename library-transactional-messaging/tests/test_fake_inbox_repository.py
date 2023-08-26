import datetime
import uuid

import pytest

from transactional_messaging.fakes import FakeInboxRepository
from transactional_messaging.idempotent_consumer import MessageAlreadyProcessedError
from transactional_messaging.utils.time import utcnow


@pytest.fixture()
def repo() -> FakeInboxRepository:
    return FakeInboxRepository([])


@pytest.mark.asyncio()
async def test_processed_message_not_found(repo: FakeInboxRepository) -> None:
    assert await repo.get(message_id=uuid.uuid4()) is None


@pytest.mark.asyncio()
async def test_save_processed_message(repo: FakeInboxRepository) -> None:
    message_id = uuid.uuid4()

    await repo.save(message_id=message_id)

    message = await repo.get(message_id=message_id)
    assert message
    assert message.message_id == message_id
    assert datetime.timedelta(seconds=1) > utcnow() - message.created_at


@pytest.mark.asyncio()
async def test_message_already_processed(repo: FakeInboxRepository) -> None:
    message_id = uuid.uuid4()
    await repo.save(message_id=message_id)

    with pytest.raises(MessageAlreadyProcessedError, match=str(message_id)):
        await repo.save(message_id=message_id)
