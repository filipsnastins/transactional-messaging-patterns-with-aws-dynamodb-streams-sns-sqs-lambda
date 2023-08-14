import datetime
import uuid
from dataclasses import dataclass
from typing import Protocol

import structlog

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class MessageAlreadyProcessedError(Exception):
    pass


@dataclass
class ProcessedMessage:
    message_id: uuid.UUID
    created_at: datetime.datetime


class InboxRepository(Protocol):
    async def save(self, message_id: uuid.UUID) -> None:
        ...

    async def get(self, message_id: uuid.UUID) -> ProcessedMessage | None:
        ...


async def ensure_idempotence(message_id: uuid.UUID, repository: InboxRepository) -> None:
    processed_message = await repository.get(message_id=message_id)
    if processed_message is not None:
        logger.info("idempotent_consumer__message_already_processed", message_id=message_id)
        raise MessageAlreadyProcessedError(message_id)
    await repository.save(message_id=message_id)
