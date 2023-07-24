import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


class CustomerCreditLimitExceededError(Exception):
    pass


@dataclass
class Customer:
    customer_id: uuid.UUID
    name: str
    _credit_limit: Decimal
    _credit_reservations: dict[uuid.UUID, Decimal]
    created_at: datetime
    version: int

    def __init__(
        self,
        name: str,
        credit_limit: Decimal,
        customer_id: uuid.UUID | None = None,
        credit_reservations: dict[uuid.UUID, Decimal] | None = None,
        created_at: datetime | None = None,
        version: int | None = None,
    ) -> None:
        self.customer_id = customer_id or uuid.uuid4()
        self.name = name
        self._credit_limit = credit_limit
        self._credit_reservations = credit_reservations or {}
        self.created_at = created_at or datetime.utcnow().replace(tzinfo=timezone.utc)
        self.version = version or 0

    @staticmethod
    def from_dict(data: dict) -> "Customer":
        return Customer(**data)

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "credit_limit": self._credit_limit,
            "credit_reservations": self._credit_reservations,
            "created_at": self.created_at,
            "version": self.version,
        }

    def available_credit(self) -> Decimal:
        return self._credit_limit - sum(self._credit_reservations.values())

    def reserve_credit(self, order_id: uuid.UUID, order_total: Decimal) -> None:
        if self.available_credit() >= order_total:
            self._credit_reservations[order_id] = order_total
        else:
            raise CustomerCreditLimitExceededError

    def unreserve_credit(self, order_id: uuid.UUID) -> None:
        self._credit_reservations.pop(order_id)
