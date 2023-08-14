import datetime
import uuid
from dataclasses import dataclass
from typing import Protocol


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
