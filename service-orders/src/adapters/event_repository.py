import uuid
from typing import Protocol

from tomodachi_outbox.message import Message

from orders.events import Event


class AbstractEventRepository(Protocol):
    async def publish(self, events: list[Event]) -> None:
        ...

    async def get(self, event_id: uuid.UUID) -> Message | None:
        ...
