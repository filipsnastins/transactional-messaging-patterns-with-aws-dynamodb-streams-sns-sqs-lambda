import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderState(Enum):
    PENDING = "PENDING"


@dataclass
class Order:
    id: uuid.UUID
    customer_id: uuid.UUID
    total_amount: Decimal
    state: OrderState
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    def __init__(
        self,
        id: uuid.UUID,
        customer_id: uuid.UUID,
        total_amount: Decimal,
        state: OrderState,
        created_at: datetime.datetime,
        updated_at: datetime.datetime | None,
    ) -> None:
        self.id = id
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.state = state
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, customer_id: uuid.UUID, total_amount: Decimal) -> "Order":
        return cls(
            id=uuid.uuid4(),
            customer_id=customer_id,
            total_amount=total_amount,
            state=OrderState.PENDING,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
            updated_at=None,
        )
