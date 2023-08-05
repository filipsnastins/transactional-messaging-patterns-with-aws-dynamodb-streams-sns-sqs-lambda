import datetime
import uuid
from dataclasses import dataclass, field


@dataclass
class Message:
    message_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.utcnow().replace(tzinfo=datetime.UTC)
    )
    dispatched: bool = False
    dispatched_at: datetime.datetime | None = None
