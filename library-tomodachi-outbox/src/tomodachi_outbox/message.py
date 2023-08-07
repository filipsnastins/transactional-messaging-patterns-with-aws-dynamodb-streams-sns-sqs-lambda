import datetime
import uuid
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Message:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    )


@dataclass(kw_only=True)
class DispatchedMessage(Message):
    dispatched_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    )
