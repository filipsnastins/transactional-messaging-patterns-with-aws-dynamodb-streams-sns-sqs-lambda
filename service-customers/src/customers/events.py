import datetime
import json
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from stockholm import Money

from utils.time import datetime_to_str, utcnow


class CustomerValidationErrors(Enum):
    CUSTOMER_NOT_FOUND_ERROR = "CUSTOMER_NOT_FOUND_ERROR"


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID
    created_at: datetime.datetime = field(default_factory=utcnow)

    @property
    def message_id(self) -> uuid.UUID:
        return self.event_id

    @property
    def aggregate_id(self) -> uuid.UUID:
        return self.customer_id

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "customer_id": str(self.customer_id),
            "correlation_id": str(self.correlation_id),
            "created_at": datetime_to_str(self.created_at),
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())


@dataclass(kw_only=True)
class CustomerCreatedEvent(Event):
    name: str
    credit_limit: Decimal

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "name": self.name,
            "credit_limit": int(Money(self.credit_limit).to_sub_units()),
        }


@dataclass(kw_only=True)
class CustomerCreditReservedEvent(Event):
    order_id: uuid.UUID

    def to_dict(self) -> dict:
        return super().to_dict() | {"order_id": str(self.order_id)}


@dataclass(kw_only=True)
class CustomerCreditReservationFailedEvent(Event):
    order_id: uuid.UUID

    def to_dict(self) -> dict:
        return super().to_dict() | {"order_id": str(self.order_id)}


@dataclass(kw_only=True)
class CustomerValidationFailedEvent(Event):
    order_id: uuid.UUID
    error: CustomerValidationErrors

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "order_id": str(self.order_id),
            "error": self.error.value,
        }
