import datetime
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
    created_at: datetime.datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "order_id": str(self.order_id),
            "customer_id": str(self.customer_id),
            "correlation_id": str(self.correlation_id),
            "created_at": datetime_to_str(self.created_at),
        }


@dataclass(kw_only=True)
class OrderCreatedEvent(Event):
    state: OrderState = OrderState.PENDING
    total_amount: Decimal

    def to_dict(self) -> dict:
        return super().to_dict() | {"total_amount": int(Money(self.total_amount).to_sub_units())}
