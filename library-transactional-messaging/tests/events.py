import datetime
import json
import uuid
from dataclasses import dataclass, field

from transactional_messaging.utils.time import datetime_to_str, utcnow


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    order_id: uuid.UUID
    created_at: datetime.datetime = field(default_factory=utcnow)

    @property
    def message_id(self) -> uuid.UUID:
        return self.event_id

    @property
    def aggregate_id(self) -> uuid.UUID:
        return self.order_id

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "correlation_id": str(self.correlation_id),
            "order_id": str(self.order_id),
            "created_at": datetime_to_str(self.created_at),
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())


@dataclass(kw_only=True)
class OrderCreatedEvent(Event):
    pass


@dataclass(kw_only=True)
class UnknownOrderEvent(Event):
    pass
