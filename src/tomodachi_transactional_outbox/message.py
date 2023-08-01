import datetime
import uuid
from dataclasses import dataclass


@dataclass
class Message:
    event_id: uuid.UUID
    aggregate_id: uuid.UUID
    correlation_id: uuid.UUID
    topic: str
    message: str
    created_at: datetime.datetime
    dispatched: bool = False
    dispatched_at: datetime.datetime | None = None
