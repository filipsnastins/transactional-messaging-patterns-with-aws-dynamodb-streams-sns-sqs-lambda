import datetime
import uuid
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime


@dataclass(kw_only=True)
class CustomerCreatedEvent(Event):
    customer_id: uuid.UUID
    name: str
    credit_limit: Decimal
    created_at: datetime.datetime
