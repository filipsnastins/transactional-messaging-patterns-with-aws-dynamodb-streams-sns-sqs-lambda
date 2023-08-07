import datetime
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from stockholm import Money


class CustomerValidationErrors(Enum):
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    customer_id: uuid.UUID
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.utcnow().replace(tzinfo=datetime.UTC)
    )

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


@dataclass(kw_only=True)
class OrderCreatedExternalEvent(Event):
    order_id: uuid.UUID
    order_total: Decimal

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "order_id": str(self.order_id),
            "order_total": int(Money(self.order_total).to_sub_units()),
        }
