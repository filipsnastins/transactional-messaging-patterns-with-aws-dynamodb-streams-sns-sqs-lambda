import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderState(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    id: uuid.UUID
    customer_id: uuid.UUID
    state: OrderState
    total_amount: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    def __init__(
        self,
        id: uuid.UUID,
        customer_id: uuid.UUID,
        state: OrderState,
        total_amount: Decimal,
        version: int,
        created_at: datetime.datetime,
        updated_at: datetime.datetime | None,
    ) -> None:
        self.id = id
        self.customer_id = customer_id
        self.state = state
        self.total_amount = total_amount
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(customer_id: uuid.UUID, total_amount: Decimal) -> "Order":
        return Order(
            id=uuid.uuid4(),
            customer_id=customer_id,
            state=OrderState.PENDING,
            total_amount=total_amount,
            version=0,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
            updated_at=None,
        )
