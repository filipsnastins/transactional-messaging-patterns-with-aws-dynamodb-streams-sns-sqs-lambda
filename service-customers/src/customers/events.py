import datetime
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from stockholm import Money


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID
    correlation_id: uuid.UUID
    created_at: datetime.datetime

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "customer_id": str(self.customer_id),
            "correlation_id": str(self.correlation_id),
            "created_at": self.created_at.isoformat(),
        }


@dataclass(kw_only=True)
class CustomerCreatedEvent(Event):
    name: str
    credit_limit: Decimal

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
        }
