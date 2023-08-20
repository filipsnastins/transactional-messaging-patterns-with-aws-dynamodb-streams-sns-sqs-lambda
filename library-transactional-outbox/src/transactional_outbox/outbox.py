import datetime
import uuid
from dataclasses import dataclass
from typing import Protocol


class MessageAlreadyPublishedError(Exception):
    pass


class UnknownTopicError(Exception):
    pass


class MessageNotFoundError(Exception):
    pass


class Message(Protocol):
    @property
    def message_id(self) -> uuid.UUID:
        ...

    @property
    def aggregate_id(self) -> uuid.UUID:
        ...

    @property
    def correlation_id(self) -> uuid.UUID:
        ...

    @property
    def created_at(self) -> datetime.datetime:
        ...

    def serialize(self) -> str:
        ...


@dataclass
class PublishedMessage:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime
    approximate_dispatch_count: int
    is_dispatched: bool
    dispatched_at: datetime.datetime | None


class OutboxRepository(Protocol):
    async def publish(self, messages: list[Message]) -> None:
        ...

    async def get(self, message_id: uuid.UUID) -> PublishedMessage | None:
        ...

    async def mark_as_dispatched(self, message_id: uuid.UUID) -> None:
        ...

    async def get_not_dispatched_messages(self) -> list[PublishedMessage]:
        ...
