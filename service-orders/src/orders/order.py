import datetime
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class NotPendingOrderCannotBeApprovedError(Exception):
    pass


class PendingOrderCannotBeCancelledError(Exception):
    pass


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
    order_total: Decimal
    version: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    def __init__(
        self,
        id: uuid.UUID,
        customer_id: uuid.UUID,
        state: OrderState,
        order_total: Decimal,
        version: int,
        created_at: datetime.datetime,
        updated_at: datetime.datetime | None,
    ) -> None:
        self.id = id
        self.customer_id = customer_id
        self.state = state
        self.order_total = order_total
        self.version = version
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(customer_id: uuid.UUID, order_total: Decimal) -> "Order":
        return Order(
            id=uuid.uuid4(),
            customer_id=customer_id,
            state=OrderState.PENDING,
            order_total=order_total,
            version=0,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
            updated_at=None,
        )

    def note_credit_reserved(self) -> None:
        if self.state == OrderState.PENDING:
            self.state = OrderState.APPROVED
        else:
            raise NotPendingOrderCannotBeApprovedError(self.id)

    def note_credit_rejected(self) -> None:
        self.state = OrderState.REJECTED

    def cancel(self) -> None:
        if self.state == OrderState.APPROVED:
            self.state = OrderState.CANCELLED
        elif self.state == OrderState.PENDING:
            raise PendingOrderCannotBeCancelledError(self.id)
        else:
            raise RuntimeError(f"Can't cancel order in state: {self.state}")
