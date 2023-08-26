import datetime
import uuid

import pytest
from unit_of_work.dynamodb import DynamoDBClientFactory, DynamoDBSession

from transactional_messaging.dynamodb import DynamoDBInboxRepository
from transactional_messaging.idempotent_consumer import MessageAlreadyProcessedError
from transactional_messaging.utils.time import utcnow

pytestmark = pytest.mark.usefixtures("_create_inbox_table", "_reset_moto_container_on_teardown")


@pytest.fixture()
def session(client_factory: DynamoDBClientFactory) -> DynamoDBSession:
    return DynamoDBSession(client_factory)


@pytest.fixture()
def repo(session: DynamoDBSession) -> DynamoDBInboxRepository:
    return DynamoDBInboxRepository(table_name="orders-inbox", session=session)


@pytest.mark.asyncio()
async def test_processed_message_not_found(repo: DynamoDBInboxRepository) -> None:
    assert await repo.get(message_id=uuid.uuid4()) is None


@pytest.mark.asyncio()
async def test_save_processed_message(repo: DynamoDBInboxRepository, session: DynamoDBSession) -> None:
    message_id = uuid.uuid4()

    await repo.save(message_id=message_id)
    await session.commit()

    message = await repo.get(message_id=message_id)
    assert message
    assert message.message_id == message_id
    assert datetime.timedelta(seconds=1) > utcnow() - message.created_at


@pytest.mark.asyncio()
async def test_message_already_processed(repo: DynamoDBInboxRepository, session: DynamoDBSession) -> None:
    message_id = uuid.uuid4()
    await repo.save(message_id=message_id)
    await session.commit()

    await repo.save(message_id=message_id)
    with pytest.raises(MessageAlreadyProcessedError, match=str(message_id)):
        await session.commit()
