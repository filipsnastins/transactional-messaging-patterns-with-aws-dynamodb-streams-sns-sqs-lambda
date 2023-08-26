import uuid

import pytest

from transactional_messaging.fakes import FakeInboxRepository
from transactional_messaging.idempotent_consumer import MessageAlreadyProcessedError, ensure_idempotence


@pytest.fixture()
def repo() -> FakeInboxRepository:
    return FakeInboxRepository([])


@pytest.mark.asyncio()
async def test_new_message_processed(repo: FakeInboxRepository) -> None:
    message_id_1 = uuid.uuid4()
    message_id_2 = uuid.uuid4()

    await ensure_idempotence(message_id_1, repo)
    await ensure_idempotence(message_id_2, repo)

    assert await repo.get(message_id_1)
    assert await repo.get(message_id_2)


@pytest.mark.asyncio()
async def test_already_processed_message(repo: FakeInboxRepository) -> None:
    message_id = uuid.uuid4()
    await ensure_idempotence(message_id, repo)

    with pytest.raises(MessageAlreadyProcessedError, match=str(message_id)):
        await ensure_idempotence(message_id, repo)
