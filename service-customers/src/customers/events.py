import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID
    created_at: datetime


@dataclass(kw_only=True)
class CustomerCreatedEvent(Event):
    id: uuid.UUID
    name: str
    credit_limit: Decimal
