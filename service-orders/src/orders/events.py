import datetime
import json
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from stockholm import Money

from orders.order import OrderState
from utils.time import datetime_to_str, utcnow


@dataclass(kw_only=True)
class Event:
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    order_id: uuid.UUID
    customer_id: uuid.UUID
    state: OrderState
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
            "customer_id": str(self.customer_id),
            "state": self.state.value,
            "created_at": datetime_to_str(self.created_at),
        }

    def serialize(self) -> str:
        return json.dumps(self.to_dict())


@dataclass(kw_only=True)
class OrderCreatedEvent(Event):
    order_total: Decimal

    def to_dict(self) -> dict:
        return super().to_dict() | {"order_total": int(Money(self.order_total).to_sub_units())}


@dataclass(kw_only=True)
class OrderApprovedEvent(Event):
    pass


@dataclass(kw_only=True)
class OrderRejectedEvent(Event):
    pass


@dataclass(kw_only=True)
class OrderCancelledEvent(Event):
    pass
