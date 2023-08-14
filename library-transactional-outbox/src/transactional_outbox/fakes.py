import copy
import uuid

from transactional_outbox.outbox import Message, MessageAlreadyPublishedError, OutboxRepository, PublishedMessage


class FakeOutboxRepository(OutboxRepository):
    """Fake implementation of OutboxRepository for unit testing purposes.

    Stores original message objects instead of converting them to PublishedMessage
    for easier assertions in unit tests.
    """

    def __init__(self, messages: list[Message]) -> None:
        self.messages = messages

    async def publish(self, messages: list[Message]) -> None:
        for message in messages:
            if await self.get(message_id=message.message_id):
                raise MessageAlreadyPublishedError(message.message_id)
        self.messages.extend(copy.deepcopy(messages))

    async def get(self, message_id: uuid.UUID) -> PublishedMessage | None:
        message = next((copy.deepcopy(v) for v in self.messages if v.message_id == message_id), None)
        if not message:
            return None
        return PublishedMessage(
            message_id=message.message_id,
            correlation_id=message.correlation_id,
            aggregate_id=message.aggregate_id,
            topic=message.__class__.__name__,
            message=message.serialize(),
            created_at=message.created_at,
            is_dispatched=False,
            dispatched_at=None,
        )

    def clear(self) -> None:
        self.messages.clear()

    async def mark_dispatched(self, message_id: uuid.UUID) -> None:
        raise NotImplementedError

    async def get_not_dispatched_messages(self) -> list[PublishedMessage]:
        raise NotImplementedError
